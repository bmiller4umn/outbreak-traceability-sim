"""
Investigation engine for outbreak traceback simulation.

Implements FDA-style convergence analysis to trace back through supply
chain records and identify potential contamination sources. Compares
effectiveness under deterministic vs. probabilistic lot code scenarios.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from collections import defaultdict
import math

from ..models.base import ProductCategory
from ..models.lots import LotGraph, TracebackPath
from .network import SupplyChainNetwork
from .exposure import IllnessCase

if TYPE_CHECKING:
    from .flow import Shipment


# Minimum confidence score gap required for a conclusive identification
IDENTIFICATION_CONFIDENCE_THRESHOLD = 0.05


@dataclass
class InvestigationTimingConfig:
    """
    Configuration for estimating investigation time.

    Based on realistic FDA outbreak investigation timeframes.
    Times are in hours unless otherwise specified.

    Typical outbreak investigation takes 1-3 weeks with a team of investigators:
    - Days 1-3: Case interviews, identifying exposure locations
    - Days 3-5: Record requests sent, waiting for responses (main bottleneck)
    - Days 5-10: Analyzing records, tracebacks, convergence analysis
    - Days 10-14: Farm verification, confirmation
    """
    # Investigation team
    num_investigators: int = 5  # Number of investigators assigned to traceback
    direct_work_hours_per_day: float = 6.0  # Direct work hours per investigator per day (excludes meetings, travel, etc.)

    # Record request phase - this is the main bottleneck (calendar time, not parallelizable by adding investigators)
    record_request_turnaround_hours: float = 48.0  # Time for entity to respond (24-72 hrs typical)
    parallel_request_capacity: int = 10  # How many locations can be contacted simultaneously

    # Analysis phase - these are quick once you have records
    # TLC review is mostly automated database lookups
    analysis_hours_per_tlc: float = 0.01  # ~36 seconds per TLC (reviewing record)
    analysis_hours_per_traceback_path: float = 0.005  # ~18 seconds per path (following link)

    # Convergence analysis - more substantial analytical work
    convergence_analysis_base_hours: float = 16.0  # Base time for convergence analysis
    convergence_hours_per_farm: float = 4.0  # Additional time per farm to evaluate

    # Verification phase (contacting farms, verifying records)
    farm_verification_hours: float = 16.0  # Time to verify each candidate farm
    max_farms_to_verify: int = 3  # Only verify top N farms

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "num_investigators": self.num_investigators,
            "direct_work_hours_per_day": self.direct_work_hours_per_day,
            "record_request_turnaround_hours": self.record_request_turnaround_hours,
            "parallel_request_capacity": self.parallel_request_capacity,
            "analysis_hours_per_tlc": self.analysis_hours_per_tlc,
            "analysis_hours_per_traceback_path": self.analysis_hours_per_traceback_path,
            "convergence_analysis_base_hours": self.convergence_analysis_base_hours,
            "convergence_hours_per_farm": self.convergence_hours_per_farm,
            "farm_verification_hours": self.farm_verification_hours,
            "max_farms_to_verify": self.max_farms_to_verify,
        }


@dataclass
class InvestigationTimingEstimate:
    """
    Estimated time for each phase of the investigation.

    All times are in hours unless otherwise noted.
    - "hours" fields represent total person-hours of work
    - "calendar_days" represents actual elapsed time accounting for team size
    """
    # Phase breakdowns (person-hours of work)
    record_request_hours: float = 0.0  # Calendar time waiting for records (not parallelizable)
    tlc_analysis_hours: float = 0.0  # Person-hours analyzing TLC records
    traceback_hours: float = 0.0  # Person-hours following traceback paths
    convergence_analysis_hours: float = 0.0  # Person-hours analyzing convergence patterns
    farm_verification_hours: float = 0.0  # Person-hours verifying candidate farms

    # Totals
    total_work_hours: float = 0.0  # Total person-hours of investigative work
    total_calendar_days: float = 0.0  # Actual elapsed days (accounting for team size)

    # Team configuration used
    num_investigators: int = 5
    direct_work_hours_per_day: float = 6.0

    # Breakdown factors (for explanation)
    locations_contacted: int = 0
    tlcs_analyzed: int = 0
    paths_traced: int = 0
    farms_evaluated: int = 0
    farms_verified: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "record_request_hours": round(self.record_request_hours, 1),
            "tlc_analysis_hours": round(self.tlc_analysis_hours, 1),
            "traceback_hours": round(self.traceback_hours, 1),
            "convergence_analysis_hours": round(self.convergence_analysis_hours, 1),
            "farm_verification_hours": round(self.farm_verification_hours, 1),
            "total_work_hours": round(self.total_work_hours, 1),
            "total_calendar_days": round(self.total_calendar_days, 1),
            "num_investigators": self.num_investigators,
            "direct_work_hours_per_day": self.direct_work_hours_per_day,
            "locations_contacted": self.locations_contacted,
            "tlcs_analyzed": self.tlcs_analyzed,
            "paths_traced": self.paths_traced,
            "farms_evaluated": self.farms_evaluated,
            "farms_verified": self.farms_verified,
        }


class IdentificationOutcome(str, Enum):
    """Outcome of source identification in an investigation."""
    YES = "yes"  # Correct source identified with clear margin
    NO = "no"  # Wrong source identified with clear margin
    INCONCLUSIVE = "inconclusive"  # Top farms too close to determine


@dataclass
class TracebackNode:
    """Node in a traceback investigation."""
    node_id: UUID
    node_name: str
    node_type: str
    tlcs: list[str] = field(default_factory=list)
    probability: float = 1.0  # Probability this node is on the contamination path


@dataclass
class TracebackPath:
    """A path through the supply chain from retail to farm."""
    id: UUID = field(default_factory=uuid4)
    starting_location_id: UUID = field(default_factory=uuid4)
    starting_tlc: str = ""

    nodes: list[TracebackNode] = field(default_factory=list)
    path_probability: float = 1.0

    # Terminal farm info
    terminal_farm_id: Optional[UUID] = None
    terminal_farm_name: str = ""


@dataclass
class ConvergenceResult:
    """
    Result of convergence analysis across multiple tracebacks.

    Convergence occurs when multiple illness cases trace back to
    the same source (farm/lot), providing evidence of the outbreak source.
    """
    farm_id: UUID = field(default_factory=uuid4)
    farm_name: str = ""

    # Evidence - case convergence
    cases_converging: int = 0  # Total cases that trace to this farm
    exclusive_cases: int = 0  # Cases that ONLY trace to this farm (not to any other)
    total_cases_analyzed: int = 0  # Total cases in investigation (for percentage calc)

    # Evidence - TLC and location convergence
    tlcs_converging: list[str] = field(default_factory=list)
    retail_locations_converging: list[UUID] = field(default_factory=list)

    # Probability (for probabilistic scenarios)
    convergence_probability: float = 1.0  # Probability this is the source
    confidence_score: float = 0.0  # 0-1 confidence in this being the source

    # Computed metrics
    @property
    def case_coverage_pct(self) -> float:
        """Percentage of cases that converge to this farm."""
        if self.total_cases_analyzed == 0:
            return 0.0
        return (self.cases_converging / self.total_cases_analyzed) * 100

    @property
    def exclusive_case_pct(self) -> float:
        """Percentage of cases that ONLY converge to this farm."""
        if self.total_cases_analyzed == 0:
            return 0.0
        return (self.exclusive_cases / self.total_cases_analyzed) * 100


@dataclass
class InvestigationResult:
    """
    Complete result of an outbreak investigation.

    Contains all identified potential sources with their probabilities
    and the trace width metrics for comparison.
    """
    id: UUID = field(default_factory=uuid4)
    investigation_date: date = field(default_factory=date.today)

    # Input
    total_cases_investigated: int = 0
    cases_interviewed: int = 0  # Cases successfully interviewed with location info

    # Convergence results
    convergence_results: list[ConvergenceResult] = field(default_factory=list)

    # Primary suspect (highest convergence)
    primary_suspect_farm_id: Optional[UUID] = None
    primary_suspect_farm_name: str = ""
    primary_suspect_probability: float = 0.0

    # Trace metrics
    farms_in_scope: int = 0
    tlcs_in_scope: int = 0
    tlcs_in_scope_locations: int = 0  # TLCS - unique locations where TLCs were created
    total_traceback_paths: int = 0

    # Mode-specific metrics
    is_probabilistic_mode: bool = False
    average_path_probability: float = 1.0
    min_path_probability: float = 1.0

    # Ground truth comparison (for simulation)
    actual_source_farm_id: Optional[UUID] = None
    identification_outcome: IdentificationOutcome = IdentificationOutcome.INCONCLUSIVE
    source_rank: int = 0  # Rank of actual source in results (1 = top)
    top_two_margin: float = 0.0  # Confidence score gap between #1 and #2

    # Investigation timing estimate
    timing_estimate: Optional[InvestigationTimingEstimate] = None


class InvestigationEngine:
    """
    Performs outbreak investigation using supply chain traceback.

    Implements FDA-style convergence analysis where multiple case
    tracebacks are analyzed to find common upstream sources.

    Two modes:
    - Deterministic: Each traceback follows exact TLC linkage
    - Probabilistic: Tracebacks include probability-weighted paths

    Investigation Model (realistic for bulk produce):
    - Consumers do NOT have TLC info for bulk products like cucumbers
    - Epidemiologists interview patients to get exposure location and estimated date
    - FDA requests records from retail locations for a time window
    - Investigation traces back from ALL TLCs at the location during that window
    """

    def __init__(
        self,
        network: SupplyChainNetwork,
        lot_graph: LotGraph,
        is_probabilistic: bool = False,
        record_collection_window_days: int = 14,
        node_inventory: Optional[dict[UUID, list]] = None,
        tlc_shipment_map: Optional[dict[tuple[UUID, str], "Shipment"]] = None,
        timing_config: Optional[InvestigationTimingConfig] = None
    ):
        """
        Initialize the investigation engine.

        Args:
            network: Supply chain network
            lot_graph: Lot tracking graph
            is_probabilistic: Whether to use probabilistic traceback
            record_collection_window_days: Days of records FDA requests from retailers
            node_inventory: Inventory records by node ID (from flow simulator)
            tlc_shipment_map: Map of (location_id, tlc) -> Shipment for DC probabilistic tracking
            timing_config: Configuration for investigation timing estimates
        """
        self.network = network
        self.lot_graph = lot_graph
        self.is_probabilistic = is_probabilistic
        self.record_collection_window_days = record_collection_window_days
        self.node_inventory = node_inventory or {}
        self.tlc_shipment_map = tlc_shipment_map or {}
        self.timing_config = timing_config or InvestigationTimingConfig()

        # Investigation state
        self.case_tracebacks: dict[UUID, list[TracebackPath]] = {}
        self.farm_convergence: dict[UUID, list[UUID]] = {}  # farm_id -> case_ids
        self.locations_contacted: set[UUID] = set()  # Track unique locations contacted

    def get_tlcs_at_location_in_window(
        self,
        location_id: UUID,
        center_date: date,
        window_days: Optional[int] = None
    ) -> list[str]:
        """
        Get all TLCs that were at a location during a date window.

        This simulates FDA requesting records from a retail location
        for a time window around the estimated purchase date.

        Args:
            location_id: Retail or deli location ID
            center_date: Center of the date window (estimated purchase date)
            window_days: Days before/after center (uses default if None)

        Returns:
            List of TLCs present at the location during the window
        """
        if window_days is None:
            window_days = self.record_collection_window_days

        # Calculate window bounds
        half_window = window_days // 2
        window_start = center_date - timedelta(days=half_window)
        window_end = center_date + timedelta(days=half_window)

        tlcs_in_window = []

        # Look up TLCs from inventory records at this location
        inventory_records = self.node_inventory.get(location_id, [])
        for record in inventory_records:
            record_date = record.received_date.date()
            if window_start <= record_date <= window_end:
                tlcs_in_window.append(record.tlc)

        return tlcs_in_window

    def traceback_from_tlc(
        self,
        starting_tlc: str,
        starting_location_id: UUID,
        min_probability: float = 0.01
    ) -> list[TracebackPath]:
        """
        Perform traceback from a single TLC.

        In probabilistic mode, this expands the scope to include ALL TLCs that
        the supplying DC said might have been shipped (based on shipment.tlc_probabilities).
        This reflects the uncertainty in DC records when they can't prove exactly
        which TLCs were in each shipment.

        Args:
            starting_tlc: TLC to trace back from
            starting_location_id: Location where TLC was found
            min_probability: Minimum probability to include in path

        Returns:
            List of traceback paths to source farms
        """
        paths = []

        # Determine which TLCs to trace back
        # In probabilistic mode, expand to all TLCs the DC said might have been shipped
        tlcs_to_trace: dict[str, float] = {starting_tlc: 1.0}

        if self.is_probabilistic:
            # Check if this TLC was delivered by a shipment with probabilistic tracking
            shipment_key = (starting_location_id, starting_tlc)
            if shipment_key in self.tlc_shipment_map:
                shipment = self.tlc_shipment_map[shipment_key]
                if shipment.tlc_probabilities:
                    # Expand to all TLCs the DC said might have been shipped
                    for tlc, prob in shipment.tlc_probabilities.items():
                        if prob >= min_probability:
                            # Use the DC's probability estimate
                            tlcs_to_trace[tlc] = prob

        # Trace back from each TLC (expanded set in probabilistic mode)
        for trace_tlc, tlc_probability in tlcs_to_trace.items():
            # Use lot graph traceback
            if self.is_probabilistic:
                graph_result = self.lot_graph.traceback(trace_tlc, min_probability=min_probability)
            else:
                graph_result = self.lot_graph.traceback(trace_tlc, min_probability=1.0)

            # Convert to traceback paths
            for tlc, graph_probability in graph_result.tlc_probabilities.items():
                if tlc not in self.lot_graph.lots:
                    continue

                lot = self.lot_graph.lots[tlc]

                # Check if this is a farm lot (source)
                farm_id = lot.created_by_node_id
                farm = self.network.farms.get(farm_id)

                if farm is not None:
                    # Combined probability: DC's shipment probability * lot graph probability
                    combined_probability = tlc_probability * graph_probability

                    path = TracebackPath(
                        starting_location_id=starting_location_id,
                        starting_tlc=starting_tlc,
                        path_probability=combined_probability,
                        terminal_farm_id=farm_id,
                        terminal_farm_name=farm.farm_name,
                    )

                    # Build path nodes from graph path
                    if tlc in graph_result.paths:
                        path_tlcs = graph_result.paths[tlc]
                        for path_tlc in path_tlcs:
                            if path_tlc in self.lot_graph.lots:
                                path_lot = self.lot_graph.lots[path_tlc]
                                node_id = path_lot.created_by_node_id
                                node = self.network.get_node(node_id)
                                if node:
                                    path.nodes.append(TracebackNode(
                                        node_id=node_id,
                                        node_name=self.network.get_node_name(node_id),
                                        node_type=node.node_type.value,
                                        tlcs=[path_tlc],
                                        probability=combined_probability,
                                    ))

                    paths.append(path)

        return paths

    def traceback_case(
        self,
        case: IllnessCase,
        min_probability: float = 0.01
    ) -> list[TracebackPath]:
        """
        Perform traceback for a single illness case using realistic investigation model.

        For bulk produce (like cucumbers), consumers don't have TLC info.
        Investigation requires:
        1. Case to have been successfully interviewed
        2. Patient reported exposure location
        3. Patient estimated purchase date
        4. FDA requests records from location for a time window
        5. Traceback from ALL TLCs at location during that window

        Args:
            case: Illness case to trace back
            min_probability: Minimum probability threshold

        Returns:
            List of traceback paths for this case
        """
        paths = []

        # Case must have been successfully interviewed with location info
        if not case.was_interviewed:
            self.case_tracebacks[case.id] = paths
            return paths

        if not case.reported_exposure_location_id or not case.estimated_purchase_date:
            self.case_tracebacks[case.id] = paths
            return paths

        # Track this location as contacted for timing estimation
        self.locations_contacted.add(case.reported_exposure_location_id)

        # Get all TLCs at the reported location during the FDA record window
        # Window accounts for patient uncertainty in purchase date recall
        window_days = self.record_collection_window_days + case.purchase_date_uncertainty_days
        tlcs_at_location = self.get_tlcs_at_location_in_window(
            case.reported_exposure_location_id,
            case.estimated_purchase_date,
            window_days
        )

        # Trace back from each TLC found in records
        for tlc in tlcs_at_location:
            paths.extend(self.traceback_from_tlc(
                tlc,
                case.reported_exposure_location_id,
                min_probability
            ))

        self.case_tracebacks[case.id] = paths
        return paths

    def analyze_convergence(
        self,
        cases: list[IllnessCase],
        min_probability: float = 0.01
    ) -> list[ConvergenceResult]:
        """
        Analyze convergence across multiple cases.

        Performs traceback for all cases and identifies common
        upstream sources (farms) where multiple cases converge.
        Uses FDA-style convergence analysis where farms that explain
        more cases (especially exclusive cases) are ranked higher.

        Args:
            cases: List of illness cases to analyze
            min_probability: Minimum probability threshold

        Returns:
            List of convergence results, sorted by evidence strength
        """
        # Reset state
        self.case_tracebacks = {}
        self.farm_convergence = defaultdict(list)

        # Track which farms each case traces to (for exclusive case calculation)
        case_to_farms: dict[UUID, set[UUID]] = defaultdict(set)

        # Traceback each case
        for case in cases:
            paths = self.traceback_case(case, min_probability)

            # Record farm convergence
            for path in paths:
                if path.terminal_farm_id:
                    self.farm_convergence[path.terminal_farm_id].append(case.id)
                    case_to_farms[case.id].add(path.terminal_farm_id)

        # Count cases that traced to any farm (usable cases)
        cases_with_traces = len([c for c in cases if case_to_farms.get(c.id)])

        # Build convergence results
        results = []
        for farm_id, case_ids in self.farm_convergence.items():
            farm = self.network.farms.get(farm_id)
            if not farm:
                continue

            unique_case_ids = set(case_ids)

            # Calculate exclusive cases - cases that ONLY trace to this farm
            exclusive_cases = sum(
                1 for case_id in unique_case_ids
                if len(case_to_farms.get(case_id, set())) == 1
            )

            # Calculate convergence probability
            path_probs = []
            tlcs = set()
            locations = set()

            for case_id in unique_case_ids:
                for path in self.case_tracebacks.get(case_id, []):
                    if path.terminal_farm_id == farm_id:
                        path_probs.append(path.path_probability)
                        tlcs.add(path.starting_tlc)
                        locations.add(path.starting_location_id)

            # Calculate aggregate probability
            if self.is_probabilistic and path_probs:
                # Use geometric mean for combined probability
                convergence_prob = math.exp(
                    sum(math.log(max(p, 1e-10)) for p in path_probs) / len(path_probs)
                )
            else:
                convergence_prob = 1.0

            # FDA-style confidence scoring - heavily weight exclusive cases
            # Exclusive cases are the strongest evidence since they can ONLY come from this farm
            total_usable = max(1, cases_with_traces)
            case_coverage = len(unique_case_ids) / total_usable
            exclusive_coverage = exclusive_cases / total_usable
            location_diversity = len(locations) / max(1, len(set(
                c.reported_exposure_location_id for c in cases
                if case_to_farms.get(c.id) and c.reported_exposure_location_id
            )))

            # Weighted confidence score:
            # - 50% exclusive cases (cases that ONLY trace to this farm - strongest evidence)
            # - 30% case coverage (what % of cases trace to this farm)
            # - 15% location diversity (cases from different retail locations)
            # - 5% path probability (for probabilistic mode)
            confidence = min(1.0, (
                0.50 * exclusive_coverage +
                0.30 * case_coverage +
                0.15 * location_diversity +
                0.05 * convergence_prob
            ))

            result = ConvergenceResult(
                farm_id=farm_id,
                farm_name=farm.farm_name,
                cases_converging=len(unique_case_ids),
                exclusive_cases=exclusive_cases,
                total_cases_analyzed=cases_with_traces,
                tlcs_converging=list(tlcs),
                retail_locations_converging=list(locations),
                convergence_probability=convergence_prob,
                confidence_score=confidence,
            )
            results.append(result)

        # Sort by confidence score (highest first), then by cases converging
        results.sort(key=lambda r: (-r.confidence_score, -r.cases_converging, -r.exclusive_cases))
        return results

    def estimate_investigation_time(
        self,
        tlcs_in_scope: int,
        total_paths: int,
        farms_in_scope: int,
        identification_outcome: IdentificationOutcome
    ) -> InvestigationTimingEstimate:
        """
        Estimate the time required for this investigation.

        Models realistic FDA investigation timing based on:
        - Number of locations to contact (record requests)
        - Number of TLCs to analyze
        - Number of traceback paths to follow
        - Number of farms to evaluate and verify

        The calculation distinguishes between:
        - Calendar time (record requests - waiting, not parallelizable)
        - Person-hours (analysis work - can be divided among team)

        Args:
            tlcs_in_scope: Number of TLCs being traced
            total_paths: Number of traceback paths
            farms_in_scope: Number of farms in investigation scope
            identification_outcome: Whether source was identified

        Returns:
            Timing estimate with phase breakdowns
        """
        config = self.timing_config
        estimate = InvestigationTimingEstimate()

        # Store team configuration
        estimate.num_investigators = config.num_investigators
        estimate.direct_work_hours_per_day = config.direct_work_hours_per_day

        # Phase 1: Record Request
        # Time to get records from retail/deli locations
        # This is CALENDAR time (waiting for responses), not parallelizable by adding investigators
        num_locations = len(self.locations_contacted)
        estimate.locations_contacted = num_locations
        request_batches = math.ceil(num_locations / config.parallel_request_capacity)
        estimate.record_request_hours = request_batches * config.record_request_turnaround_hours

        # Phase 2: TLC Analysis (person-hours)
        # Time to analyze each TLC's records - can be divided among team
        estimate.tlcs_analyzed = tlcs_in_scope
        estimate.tlc_analysis_hours = tlcs_in_scope * config.analysis_hours_per_tlc

        # Phase 3: Traceback (person-hours)
        # Time to follow each traceback path through supply chain
        estimate.paths_traced = total_paths
        estimate.traceback_hours = total_paths * config.analysis_hours_per_traceback_path

        # Phase 4: Convergence Analysis (person-hours)
        # Base time plus time per farm to evaluate
        estimate.farms_evaluated = farms_in_scope
        estimate.convergence_analysis_hours = (
            config.convergence_analysis_base_hours +
            farms_in_scope * config.convergence_hours_per_farm
        )

        # Phase 5: Farm Verification (person-hours)
        # Investigators verify top candidate farms
        if identification_outcome in (IdentificationOutcome.YES, IdentificationOutcome.INCONCLUSIVE):
            farms_to_verify = min(farms_in_scope, config.max_farms_to_verify)
            estimate.farms_verified = farms_to_verify
            estimate.farm_verification_hours = farms_to_verify * config.farm_verification_hours
        else:
            # If wrong farm identified, may need extended investigation
            # Model this as verifying more farms
            farms_to_verify = min(farms_in_scope, config.max_farms_to_verify + 2)
            estimate.farms_verified = farms_to_verify
            estimate.farm_verification_hours = farms_to_verify * config.farm_verification_hours

        # Calculate total person-hours of work (parallelizable phases only)
        parallelizable_hours = (
            estimate.tlc_analysis_hours +
            estimate.traceback_hours +
            estimate.convergence_analysis_hours +
            estimate.farm_verification_hours
        )
        estimate.total_work_hours = parallelizable_hours

        # Calculate calendar days
        # Team capacity per day
        team_hours_per_day = config.num_investigators * config.direct_work_hours_per_day

        # Record requests are calendar time (convert hours to days)
        record_request_days = estimate.record_request_hours / 24.0

        # Parallelizable work is divided among team
        work_days = parallelizable_hours / team_hours_per_day if team_hours_per_day > 0 else 0

        # Total calendar days = waiting time + working time
        estimate.total_calendar_days = record_request_days + work_days

        return estimate

    def investigate(
        self,
        cases: list[IllnessCase],
        actual_source_farm_id: Optional[UUID] = None,
        min_probability: float = 0.01
    ) -> InvestigationResult:
        """
        Perform complete outbreak investigation.

        Args:
            cases: List of illness cases to investigate
            actual_source_farm_id: Ground truth farm ID (for simulation comparison)
            min_probability: Minimum probability threshold

        Returns:
            Complete investigation result with metrics
        """
        # Run convergence analysis
        convergence_results = self.analyze_convergence(cases, min_probability)

        # Calculate trace metrics
        all_tlcs_in_scope = set()
        unique_tlcs_sources = set()  # TLCS - unique GLNs where TLCs were assigned
        farms_in_scope = set()
        all_path_probs = []

        for case_id, paths in self.case_tracebacks.items():
            for path in paths:
                all_path_probs.append(path.path_probability)
                if path.terminal_farm_id:
                    farms_in_scope.add(path.terminal_farm_id)
                for node in path.nodes:
                    all_tlcs_in_scope.update(node.tlcs)
                    # Track the actual TLCS (GLN) for each TLC from the lot record
                    for tlc in node.tlcs:
                        if tlc in self.lot_graph.lots:
                            lot_record = self.lot_graph.lots[tlc]
                            if lot_record.tlcs:
                                unique_tlcs_sources.add(lot_record.tlcs)

        # Build result
        # Count interviewed cases (those that could contribute to investigation)
        interviewed_cases = [
            c for c in cases
            if c.was_interviewed and c.reported_exposure_location_id and c.estimated_purchase_date
        ]

        result = InvestigationResult(
            investigation_date=date.today(),
            total_cases_investigated=len(cases),
            cases_interviewed=len(interviewed_cases),
            convergence_results=convergence_results,
            farms_in_scope=len(farms_in_scope),
            tlcs_in_scope=len(all_tlcs_in_scope),
            tlcs_in_scope_locations=len(unique_tlcs_sources),  # TLCS count - unique GLNs where TLCs were assigned
            total_traceback_paths=sum(len(paths) for paths in self.case_tracebacks.values()),
            is_probabilistic_mode=self.is_probabilistic,
            average_path_probability=sum(all_path_probs) / max(1, len(all_path_probs)),
            min_path_probability=min(all_path_probs) if all_path_probs else 1.0,
            actual_source_farm_id=actual_source_farm_id,
        )

        # Set primary suspect
        if convergence_results:
            result.primary_suspect_farm_id = convergence_results[0].farm_id
            result.primary_suspect_farm_name = convergence_results[0].farm_name
            result.primary_suspect_probability = convergence_results[0].convergence_probability

        # Check ground truth and determine identification outcome
        if actual_source_farm_id and convergence_results:
            # Find rank of actual source
            for i, cr in enumerate(convergence_results):
                if cr.farm_id == actual_source_farm_id:
                    result.source_rank = i + 1
                    break

            # Calculate margin between top two farms
            top_score = convergence_results[0].confidence_score
            second_score = convergence_results[1].confidence_score if len(convergence_results) > 1 else 0.0
            margin = top_score - second_score
            result.top_two_margin = margin

            # Determine identification outcome based on margin and correctness
            if margin < IDENTIFICATION_CONFIDENCE_THRESHOLD:
                # Top farms too close - inconclusive regardless of which is correct
                result.identification_outcome = IdentificationOutcome.INCONCLUSIVE
            elif result.primary_suspect_farm_id == actual_source_farm_id:
                # Correct source identified with clear margin
                result.identification_outcome = IdentificationOutcome.YES
            else:
                # Wrong source identified with clear margin
                result.identification_outcome = IdentificationOutcome.NO

        # Calculate investigation timing estimate
        result.timing_estimate = self.estimate_investigation_time(
            tlcs_in_scope=result.tlcs_in_scope,
            total_paths=result.total_traceback_paths,
            farms_in_scope=result.farms_in_scope,
            identification_outcome=result.identification_outcome
        )

        return result

    def get_farm_probability_distribution(
        self,
        cases: list[IllnessCase],
        min_probability: float = 0.01
    ) -> dict[str, float]:
        """
        Get probability distribution over farms as potential sources.

        Args:
            cases: Cases to analyze
            min_probability: Minimum probability threshold

        Returns:
            Dictionary mapping farm name to probability
        """
        convergence = self.analyze_convergence(cases, min_probability)

        # Normalize probabilities
        total = sum(cr.confidence_score for cr in convergence)
        if total == 0:
            return {}

        return {
            cr.farm_name: cr.confidence_score / total
            for cr in convergence
        }


def compare_investigation_modes(
    network: SupplyChainNetwork,
    lot_graph: LotGraph,
    cases: list[IllnessCase],
    actual_source_farm_id: Optional[UUID] = None,
    record_collection_window_days: int = 14,
    node_inventory: Optional[dict[UUID, list]] = None,
    tlc_shipment_map: Optional[dict[tuple[UUID, str], "Shipment"]] = None,
    timing_config: Optional[InvestigationTimingConfig] = None
) -> dict:
    """
    Compare investigation results between deterministic and probabilistic modes.

    This is the key comparison for demonstrating the impact of
    calculated lot codes on outbreak investigation effectiveness.

    Args:
        network: Supply chain network
        lot_graph: Lot tracking graph
        cases: Cases to investigate
        actual_source_farm_id: Ground truth farm ID
        record_collection_window_days: Days of records FDA requests from retailers
        node_inventory: Inventory records by node ID (from flow simulator)
        tlc_shipment_map: Map of (location_id, tlc) -> Shipment for DC probabilistic tracking
        timing_config: Configuration for investigation timing estimates

    Returns:
        Comparison metrics between modes
    """
    # Deterministic investigation
    det_engine = InvestigationEngine(
        network, lot_graph,
        is_probabilistic=False,
        record_collection_window_days=record_collection_window_days,
        node_inventory=node_inventory,
        tlc_shipment_map=tlc_shipment_map,
        timing_config=timing_config
    )
    det_result = det_engine.investigate(cases, actual_source_farm_id, min_probability=1.0)

    # Probabilistic investigation
    prob_engine = InvestigationEngine(
        network, lot_graph,
        is_probabilistic=True,
        record_collection_window_days=record_collection_window_days,
        node_inventory=node_inventory,
        tlc_shipment_map=tlc_shipment_map,
        timing_config=timing_config
    )
    prob_result = prob_engine.investigate(cases, actual_source_farm_id, min_probability=0.01)

    # Get primary suspect confidence scores from convergence results
    det_primary_confidence = (
        det_result.convergence_results[0].confidence_score
        if det_result.convergence_results else 0.0
    )
    prob_primary_confidence = (
        prob_result.convergence_results[0].confidence_score
        if prob_result.convergence_results else 0.0
    )

    # Extract timing estimates
    det_timing = det_result.timing_estimate.to_dict() if det_result.timing_estimate else {}
    prob_timing = prob_result.timing_estimate.to_dict() if prob_result.timing_estimate else {}

    # Calculate timing expansion based on calendar days
    det_days = det_result.timing_estimate.total_calendar_days if det_result.timing_estimate else 1
    prob_days = prob_result.timing_estimate.total_calendar_days if prob_result.timing_estimate else 1
    timing_expansion = prob_days / max(0.1, det_days)

    # Calculate comparison metrics
    return {
        "deterministic": {
            "farms_in_scope": det_result.farms_in_scope,
            "tlcs_in_scope": det_result.tlcs_in_scope,
            "tlcs_locations": det_result.tlcs_in_scope_locations,  # TLCS
            "traceback_paths": det_result.total_traceback_paths,
            "primary_suspect": det_result.primary_suspect_farm_name,
            "primary_suspect_probability": det_result.primary_suspect_probability,
            "primary_suspect_confidence": det_primary_confidence,
            "identification_outcome": det_result.identification_outcome.value,
            "source_rank": det_result.source_rank,
            "top_two_margin": det_result.top_two_margin,
            "convergence_results": len(det_result.convergence_results),
            "investigation_timing": det_timing,
        },
        "probabilistic": {
            "farms_in_scope": prob_result.farms_in_scope,
            "tlcs_in_scope": prob_result.tlcs_in_scope,
            "tlcs_locations": prob_result.tlcs_in_scope_locations,  # TLCS
            "traceback_paths": prob_result.total_traceback_paths,
            "primary_suspect": prob_result.primary_suspect_farm_name,
            "primary_suspect_probability": prob_result.primary_suspect_probability,
            "primary_suspect_confidence": prob_primary_confidence,
            "identification_outcome": prob_result.identification_outcome.value,
            "source_rank": prob_result.source_rank,
            "top_two_margin": prob_result.top_two_margin,
            "average_path_probability": prob_result.average_path_probability,
            "convergence_results": len(prob_result.convergence_results),
            "investigation_timing": prob_timing,
        },
        "comparison": {
            "farm_scope_expansion": (
                prob_result.farms_in_scope / max(1, det_result.farms_in_scope)
            ),
            "tlc_scope_expansion": (
                prob_result.tlcs_in_scope / max(1, det_result.tlcs_in_scope)
            ),
            "tlcs_location_expansion": (
                prob_result.tlcs_in_scope_locations / max(1, det_result.tlcs_in_scope_locations)
            ),
            "path_expansion": (
                prob_result.total_traceback_paths / max(1, det_result.total_traceback_paths)
            ),
            "timing_expansion": timing_expansion,
            "deterministic_outcome": det_result.identification_outcome.value,
            "probabilistic_outcome": prob_result.identification_outcome.value,
            "confidence_difference": det_primary_confidence - prob_primary_confidence,
        },
    }
