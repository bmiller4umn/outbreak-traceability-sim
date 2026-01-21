"""
Lot tracking system for FSMA 204 traceability simulation.

This module provides the core lot tracking functionality that supports
both deterministic (full compliance) and probabilistic (calculated)
lot code assignment scenarios.

The key difference between scenarios:
- DETERMINISTIC: Exact 1:1 mapping of input TLCs to output TLCs
- PROBABILISTIC: Multiple possible input TLCs with probability weights

This difference dramatically affects traceback scope during outbreak
investigations, which is the primary focus of this simulation.
"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


class TrackingMode(str, Enum):
    """Lot code tracking modes for supply chain simulation."""
    DETERMINISTIC = "deterministic"
    PROBABILISTIC = "probabilistic"


class LotCodeRecord(BaseModel):
    """
    Record of a lot code (TLC) in the system.

    Tracks the lot from creation through the supply chain,
    maintaining linkage to source lots and destination lots.

    The Traceability Lot Code Source (TLCS) is the GLN of the physical
    location where the TLC was assigned. Per FSMA 204, this is recorded
    at Initial Packing or Transformation CTEs.
    """
    tlc: str = Field(..., description="Traceability Lot Code")
    tlcs: Optional[str] = Field(
        None,
        description="Traceability Lot Code Source - GLN of location where TLC was assigned"
    )
    created_at: datetime
    created_by_node_id: UUID
    created_at_location_id: UUID

    # Product information
    product_category: str
    product_description: str
    initial_quantity_value: float
    initial_quantity_unit: str

    # Source linkage - deterministic
    source_tlcs: list[str] = Field(
        default_factory=list,
        description="Definite source TLCs (for deterministic tracking)"
    )

    # Source linkage - probabilistic
    source_tlc_probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Source TLC to probability mapping (for calculated scenarios)"
    )

    # Destination tracking
    destination_tlcs: list[str] = Field(
        default_factory=list,
        description="TLCs derived from this lot"
    )

    # Contamination tracking for simulation
    is_contaminated: bool = False
    contamination_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )
    contamination_source: Optional[str] = None

    @computed_field
    @property
    def has_probabilistic_sources(self) -> bool:
        """Check if this lot has probabilistic source linkage."""
        return len(self.source_tlc_probabilities) > 0

    @computed_field
    @property
    def tracking_mode(self) -> TrackingMode:
        """Determine the tracking mode for this lot."""
        if self.has_probabilistic_sources:
            return TrackingMode.PROBABILISTIC
        return TrackingMode.DETERMINISTIC


class LotAssignment(BaseModel):
    """
    Assignment of lots to a shipment or transformation.

    Used when determining which TLCs to associate with an outbound
    event, supporting both deterministic and calculated scenarios.
    """
    tlc: str
    quantity_value: float
    quantity_unit: str

    # For deterministic: this is 1.0, for calculated: this is probability
    assignment_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Weight/probability of this assignment"
    )

    # Flag for tracking mode
    is_calculated: bool = Field(
        default=False,
        description="True if this assignment is calculated/probabilistic"
    )


class LotGraph(BaseModel):
    """
    Graph structure tracking lot code relationships.

    This graph enables both traceforward (farm to retail) and
    traceback (retail to farm) analysis with support for
    probabilistic edges in calculated scenarios.
    """
    id: UUID = Field(default_factory=uuid4)
    lots: dict[str, LotCodeRecord] = Field(default_factory=dict)

    # Edge tracking: source_tlc -> list of (dest_tlc, weight)
    forward_edges: dict[str, list[tuple[str, float]]] = Field(default_factory=dict)
    backward_edges: dict[str, list[tuple[str, float]]] = Field(default_factory=dict)

    def add_lot(self, lot: LotCodeRecord) -> None:
        """Add a lot to the graph."""
        self.lots[lot.tlc] = lot

        # Initialize edge lists
        if lot.tlc not in self.forward_edges:
            self.forward_edges[lot.tlc] = []
        if lot.tlc not in self.backward_edges:
            self.backward_edges[lot.tlc] = []

        # Add backward edges from sources
        for source_tlc in lot.source_tlcs:
            self._add_edge(source_tlc, lot.tlc, 1.0)

        for source_tlc, prob in lot.source_tlc_probabilities.items():
            self._add_edge(source_tlc, lot.tlc, prob)

    def _add_edge(self, source_tlc: str, dest_tlc: str, weight: float) -> None:
        """Add a directed edge from source to destination."""
        if source_tlc not in self.forward_edges:
            self.forward_edges[source_tlc] = []
        if dest_tlc not in self.backward_edges:
            self.backward_edges[dest_tlc] = []

        self.forward_edges[source_tlc].append((dest_tlc, weight))
        self.backward_edges[dest_tlc].append((source_tlc, weight))

    def link_lots(
        self,
        source_tlc: str,
        dest_tlc: str,
        weight: float = 1.0
    ) -> None:
        """Create a link between two lots."""
        self._add_edge(source_tlc, dest_tlc, weight)

        # Update lot records
        if source_tlc in self.lots:
            self.lots[source_tlc].destination_tlcs.append(dest_tlc)

        if dest_tlc in self.lots:
            if weight == 1.0:
                self.lots[dest_tlc].source_tlcs.append(source_tlc)
            else:
                self.lots[dest_tlc].source_tlc_probabilities[source_tlc] = weight

    def add_probabilistic_alias(
        self,
        actual_tlc: str,
        possible_tlc: str,
        probability: float
    ) -> None:
        """
        Add a probabilistic alias relationship between TLCs.

        This is used when a DC ships TLCs with probabilistic tracking.
        The actual_tlc is what was really shipped, but the traceability
        system thinks possible_tlc could also have been shipped.

        When investigating actual_tlc, the traceback should also consider
        possible_tlc's sources with the given probability.

        This adds a backward edge from actual_tlc to possible_tlc, so that
        traceback from actual_tlc will also explore possible_tlc's ancestry.
        """
        if actual_tlc not in self.backward_edges:
            self.backward_edges[actual_tlc] = []

        # Check if this edge already exists
        existing = [t for t, _ in self.backward_edges[actual_tlc] if t == possible_tlc]
        if not existing:
            self.backward_edges[actual_tlc].append((possible_tlc, probability))

    def traceback(
        self,
        starting_tlc: str,
        min_probability: float = 0.0,
        max_depth: Optional[int] = None
    ) -> "TracebackPath":
        """
        Perform traceback from a TLC to find all possible sources.

        Args:
            starting_tlc: TLC to trace back from
            min_probability: Minimum cumulative probability to include a path
            max_depth: Maximum depth to trace (None for unlimited)

        Returns:
            TracebackPath with all identified source TLCs and probabilities
        """
        result = TracebackPath(starting_tlc=starting_tlc)
        visited = set()

        def _traceback_recursive(
            tlc: str,
            cumulative_prob: float,
            depth: int,
            path: list[str]
        ):
            if tlc in visited:
                return
            if max_depth is not None and depth > max_depth:
                return
            if cumulative_prob < min_probability:
                return

            visited.add(tlc)
            current_path = path + [tlc]

            # Add to result
            result.add_tlc(tlc, cumulative_prob, current_path)

            # Recurse to sources
            for source_tlc, weight in self.backward_edges.get(tlc, []):
                new_prob = cumulative_prob * weight
                _traceback_recursive(source_tlc, new_prob, depth + 1, current_path)

        _traceback_recursive(starting_tlc, 1.0, 0, [])
        return result

    def traceforward(
        self,
        starting_tlc: str,
        min_probability: float = 0.0,
        max_depth: Optional[int] = None
    ) -> "TraceforwardPath":
        """
        Perform traceforward from a TLC to find all possible destinations.

        Args:
            starting_tlc: TLC to trace forward from
            min_probability: Minimum cumulative probability to include a path
            max_depth: Maximum depth to trace (None for unlimited)

        Returns:
            TraceforwardPath with all identified destination TLCs and probabilities
        """
        result = TraceforwardPath(starting_tlc=starting_tlc)
        visited = set()

        def _traceforward_recursive(
            tlc: str,
            cumulative_prob: float,
            depth: int,
            path: list[str]
        ):
            if tlc in visited:
                return
            if max_depth is not None and depth > max_depth:
                return
            if cumulative_prob < min_probability:
                return

            visited.add(tlc)
            current_path = path + [tlc]

            # Add to result
            result.add_tlc(tlc, cumulative_prob, current_path)

            # Recurse to destinations
            for dest_tlc, weight in self.forward_edges.get(tlc, []):
                new_prob = cumulative_prob * weight
                _traceforward_recursive(dest_tlc, new_prob, depth + 1, current_path)

        _traceforward_recursive(starting_tlc, 1.0, 0, [])
        return result

    def get_contaminated_lots(self) -> list[LotCodeRecord]:
        """Get all lots marked as contaminated."""
        return [lot for lot in self.lots.values() if lot.is_contaminated]

    def propagate_contamination(
        self,
        source_tlc: str,
        probability: float = 1.0
    ) -> dict[str, float]:
        """
        Propagate contamination probability forward through the graph.

        Returns dict of TLC -> contamination probability.
        """
        if source_tlc in self.lots:
            self.lots[source_tlc].is_contaminated = True
            self.lots[source_tlc].contamination_probability = probability

        result = {source_tlc: probability}
        traceforward = self.traceforward(source_tlc)

        for tlc, prob in traceforward.tlc_probabilities.items():
            contamination_prob = probability * prob
            result[tlc] = contamination_prob

            if tlc in self.lots:
                # Probabilistic union for contamination from multiple sources
                # P(A OR B) = P(A) + P(B) - P(A)*P(B)
                existing = self.lots[tlc].contamination_probability
                new_prob = existing + contamination_prob - (existing * contamination_prob)
                self.lots[tlc].contamination_probability = new_prob
                # Also set is_contaminated flag for downstream lots
                if new_prob > 0:
                    self.lots[tlc].is_contaminated = True

        return result


class TracebackPath(BaseModel):
    """Result of a traceback operation."""
    starting_tlc: str
    tlc_probabilities: dict[str, float] = Field(default_factory=dict)
    paths: dict[str, list[str]] = Field(default_factory=dict)

    def add_tlc(self, tlc: str, probability: float, path: list[str]) -> None:
        """Add a TLC to the traceback result."""
        # Keep highest probability if TLC seen multiple times
        if tlc not in self.tlc_probabilities or probability > self.tlc_probabilities[tlc]:
            self.tlc_probabilities[tlc] = probability
            self.paths[tlc] = path

    @computed_field
    @property
    def deterministic_tlcs(self) -> list[str]:
        """TLCs with probability 1.0 (deterministic linkage)."""
        return [tlc for tlc, prob in self.tlc_probabilities.items() if prob == 1.0]

    @computed_field
    @property
    def probabilistic_tlcs(self) -> list[str]:
        """TLCs with probability < 1.0 (calculated/probabilistic linkage)."""
        return [tlc for tlc, prob in self.tlc_probabilities.items() if prob < 1.0]

    @computed_field
    @property
    def total_scope(self) -> int:
        """Total number of TLCs in traceback scope."""
        return len(self.tlc_probabilities)


class TraceforwardPath(BaseModel):
    """Result of a traceforward operation."""
    starting_tlc: str
    tlc_probabilities: dict[str, float] = Field(default_factory=dict)
    paths: dict[str, list[str]] = Field(default_factory=dict)

    def add_tlc(self, tlc: str, probability: float, path: list[str]) -> None:
        """Add a TLC to the traceforward result."""
        if tlc not in self.tlc_probabilities or probability > self.tlc_probabilities[tlc]:
            self.tlc_probabilities[tlc] = probability
            self.paths[tlc] = path

    @computed_field
    @property
    def total_scope(self) -> int:
        """Total number of TLCs in traceforward scope."""
        return len(self.tlc_probabilities)


class LotTracker(BaseModel):
    """
    Main lot tracking system for the simulation.

    Manages lot code creation, assignment, and tracking across the
    supply chain, supporting both deterministic and calculated modes.
    """
    id: UUID = Field(default_factory=uuid4)
    graph: LotGraph = Field(default_factory=LotGraph)

    # Tracking mode configuration
    default_mode: TrackingMode = Field(default=TrackingMode.DETERMINISTIC)

    # Node-specific mode overrides (node_id -> mode)
    node_mode_overrides: dict[str, TrackingMode] = Field(default_factory=dict)

    # Statistics
    total_lots_created: int = 0
    deterministic_assignments: int = 0
    probabilistic_assignments: int = 0

    def get_mode_for_node(self, node_id: UUID) -> TrackingMode:
        """Get the tracking mode for a specific node."""
        return self.node_mode_overrides.get(str(node_id), self.default_mode)

    def set_node_mode(self, node_id: UUID, mode: TrackingMode) -> None:
        """Set the tracking mode for a specific node."""
        self.node_mode_overrides[str(node_id)] = mode

    def create_lot(
        self,
        tlc: str,
        node_id: UUID,
        location_id: UUID,
        product_category: str,
        product_description: str,
        quantity_value: float,
        quantity_unit: str,
        source_tlcs: Optional[list[str]] = None,
        source_probabilities: Optional[dict[str, float]] = None,
        is_contaminated: bool = False,
        contamination_source: Optional[str] = None
    ) -> LotCodeRecord:
        """
        Create a new lot in the tracking system.

        Args:
            tlc: Traceability Lot Code
            node_id: ID of node creating the lot
            location_id: ID of location where lot was created
            product_category: Category of product
            product_description: Description of product
            quantity_value: Initial quantity value
            quantity_unit: Unit of measure for quantity
            source_tlcs: Deterministic source TLCs
            source_probabilities: Probabilistic source TLC mapping
            is_contaminated: Whether lot is contaminated (for simulation)
            contamination_source: Description of contamination source

        Returns:
            Created LotCodeRecord
        """
        lot = LotCodeRecord(
            tlc=tlc,
            created_at=datetime.now(),
            created_by_node_id=node_id,
            created_at_location_id=location_id,
            product_category=product_category,
            product_description=product_description,
            initial_quantity_value=quantity_value,
            initial_quantity_unit=quantity_unit,
            source_tlcs=source_tlcs or [],
            source_tlc_probabilities=source_probabilities or {},
            is_contaminated=is_contaminated,
            contamination_source=contamination_source
        )

        self.graph.add_lot(lot)
        self.total_lots_created += 1

        if source_probabilities:
            self.probabilistic_assignments += 1
        elif source_tlcs:
            self.deterministic_assignments += 1

        return lot

    def assign_lots_deterministic(
        self,
        available_lots: list[tuple[str, float]],  # (tlc, quantity_available)
        quantity_needed: float,
        quantity_unit: str
    ) -> list[LotAssignment]:
        """
        Assign lots deterministically (FIFO) to fulfill a quantity need.

        Returns list of LotAssignments with exact quantities.
        """
        assignments = []
        remaining = quantity_needed

        for tlc, available in available_lots:
            if remaining <= 0:
                break

            take = min(remaining, available)
            assignments.append(LotAssignment(
                tlc=tlc,
                quantity_value=take,
                quantity_unit=quantity_unit,
                assignment_weight=1.0,
                is_calculated=False
            ))
            remaining -= take
            self.deterministic_assignments += 1

        return assignments

    def assign_lots_probabilistic(
        self,
        candidate_lots: list[tuple[str, float]],  # (tlc, probability)
        quantity_needed: float,
        quantity_unit: str
    ) -> list[LotAssignment]:
        """
        Assign lots probabilistically for calculated lot code scenarios.

        Returns list of LotAssignments with probability weights.
        All candidates are included with their respective probabilities.
        """
        assignments = []

        for tlc, probability in candidate_lots:
            assignments.append(LotAssignment(
                tlc=tlc,
                quantity_value=quantity_needed,  # Full quantity, weighted by probability
                quantity_unit=quantity_unit,
                assignment_weight=probability,
                is_calculated=True
            ))
            self.probabilistic_assignments += 1

        return assignments

    def traceback_from_retail(
        self,
        retail_tlc: str,
        mode: Optional[TrackingMode] = None
    ) -> TracebackPath:
        """
        Perform traceback from a retail TLC.

        This is the primary traceback entry point for outbreak investigations.
        """
        # Use default mode if not specified
        if mode is None:
            mode = self.default_mode

        # Minimum probability threshold based on mode
        min_prob = 0.0 if mode == TrackingMode.PROBABILISTIC else 1.0

        return self.graph.traceback(retail_tlc, min_probability=min_prob)

    def compare_traceback_scope(
        self,
        retail_tlc: str
    ) -> dict:
        """
        Compare traceback scope between deterministic and probabilistic modes.

        Returns metrics showing scope expansion in calculated scenarios.
        """
        deterministic_result = self.graph.traceback(retail_tlc, min_probability=1.0)
        probabilistic_result = self.graph.traceback(retail_tlc, min_probability=0.0)

        deterministic_scope = deterministic_result.total_scope
        probabilistic_scope = probabilistic_result.total_scope

        expansion_factor = (
            probabilistic_scope / deterministic_scope
            if deterministic_scope > 0 else float('inf')
        )

        return {
            "retail_tlc": retail_tlc,
            "deterministic_scope": deterministic_scope,
            "probabilistic_scope": probabilistic_scope,
            "scope_expansion_factor": expansion_factor,
            "additional_tlcs_in_scope": probabilistic_scope - deterministic_scope,
            "deterministic_tlcs": deterministic_result.deterministic_tlcs,
            "probabilistic_only_tlcs": [
                tlc for tlc in probabilistic_result.probabilistic_tlcs
                if tlc not in deterministic_result.tlc_probabilities
            ]
        }


class OutbreakScenario(BaseModel):
    """
    Configuration for an outbreak simulation scenario.

    Defines the contamination event and parameters for comparing
    traceback effectiveness under different lot code tracking modes.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str

    # Contamination source
    contaminated_farm_id: UUID
    contaminated_tlc: str
    contamination_date: date
    contamination_source_description: str

    # Outbreak detection
    first_illness_date: date
    illness_report_locations: list[UUID] = Field(default_factory=list)
    days_to_detection: int = Field(
        default=7,
        description="Days between contamination and first illness report"
    )

    # Comparison metrics (populated after simulation)
    deterministic_farms_in_scope: int = 0
    deterministic_tlcs_in_scope: int = 0
    calculated_farms_in_scope: int = 0
    calculated_tlcs_in_scope: int = 0

    @computed_field
    @property
    def farm_scope_expansion(self) -> float:
        """Factor by which farm scope expands in calculated scenario."""
        if self.deterministic_farms_in_scope == 0:
            return float('inf')
        return self.calculated_farms_in_scope / self.deterministic_farms_in_scope

    @computed_field
    @property
    def tlc_scope_expansion(self) -> float:
        """Factor by which TLC scope expands in calculated scenario."""
        if self.deterministic_tlcs_in_scope == 0:
            return float('inf')
        return self.calculated_tlcs_in_scope / self.deterministic_tlcs_in_scope
