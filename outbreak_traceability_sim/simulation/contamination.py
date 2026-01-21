"""
Contamination seeder for outbreak simulation.

This module provides functionality to mark farm lots as contaminated
during a specified date range, simulating the introduction of a
pathogen into the food supply chain.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from ..models.base import ContaminationStatus
from ..models.lots import LotGraph, LotCodeRecord


@dataclass
class ContaminationEvent:
    """
    Represents a contamination event at a farm.

    This is the root cause of the outbreak - contamination introduced
    at a specific farm during a specific time period.
    """
    id: UUID = field(default_factory=uuid4)
    farm_id: UUID = field(default_factory=uuid4)
    farm_name: str = ""

    # Contamination period
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)

    # Contamination details
    pathogen: str = "Salmonella"
    contamination_source: str = "Unknown"

    # Affected growing areas (None = all areas)
    affected_growing_areas: Optional[list[str]] = None

    # Contamination probability (1.0 = all product contaminated)
    contamination_rate: float = 1.0

    # Tracking
    contaminated_tlcs: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate contamination event parameters."""
        if not (0.0 <= self.contamination_rate <= 1.0):
            raise ValueError(
                f"contamination_rate must be between 0.0 and 1.0, got {self.contamination_rate}"
            )
        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must be >= start_date ({self.start_date})"
            )

    def is_date_in_range(self, check_date: date) -> bool:
        """Check if a date falls within the contamination period."""
        return self.start_date <= check_date <= self.end_date

    def is_tlc_affected(self, tlc: str, harvest_date: date, growing_area: Optional[str] = None) -> bool:
        """
        Determine if a TLC is affected by this contamination event.

        Args:
            tlc: The traceability lot code
            harvest_date: Date the lot was harvested
            growing_area: Growing area ID (if known)

        Returns:
            True if the lot should be marked as contaminated
        """
        if not self.is_date_in_range(harvest_date):
            return False

        if self.affected_growing_areas is not None and growing_area is not None:
            if growing_area not in self.affected_growing_areas:
                return False

        return True


class ContaminationSeeder:
    """
    Seeds contamination into the supply chain simulation.

    The seeder marks specific lots as contaminated based on contamination
    events, then propagates contamination probability through the lot graph
    to downstream products.
    """

    def __init__(self, lot_graph: LotGraph):
        """
        Initialize the contamination seeder.

        Args:
            lot_graph: The lot tracking graph to seed contamination into
        """
        self.lot_graph = lot_graph
        self.contamination_events: list[ContaminationEvent] = []
        self.contaminated_source_tlcs: set[str] = set()
        self.contamination_propagation: dict[str, float] = {}

    def add_contamination_event(self, event: ContaminationEvent) -> None:
        """Add a contamination event to the seeder."""
        self.contamination_events.append(event)

    def create_contamination_event(
        self,
        farm_id: UUID,
        farm_name: str,
        start_date: date,
        end_date: date,
        pathogen: str = "Salmonella",
        contamination_source: str = "Irrigation water",
        affected_growing_areas: Optional[list[str]] = None,
        contamination_rate: float = 1.0
    ) -> ContaminationEvent:
        """
        Create and register a new contamination event.

        Args:
            farm_id: ID of the contaminated farm
            farm_name: Name of the farm for reporting
            start_date: Start of contamination period
            end_date: End of contamination period
            pathogen: Name of the pathogen
            contamination_source: Description of contamination source
            affected_growing_areas: Specific growing areas affected (None = all)
            contamination_rate: Probability that product is contaminated (0-1)

        Returns:
            The created ContaminationEvent
        """
        event = ContaminationEvent(
            farm_id=farm_id,
            farm_name=farm_name,
            start_date=start_date,
            end_date=end_date,
            pathogen=pathogen,
            contamination_source=contamination_source,
            affected_growing_areas=affected_growing_areas,
            contamination_rate=contamination_rate
        )
        self.add_contamination_event(event)
        return event

    def seed_contamination(
        self,
        lot_metadata: dict[str, dict]  # TLC -> {farm_id, harvest_date, growing_area}
    ) -> dict[str, float]:
        """
        Seed contamination into lots based on registered contamination events.

        Args:
            lot_metadata: Dictionary mapping TLCs to their metadata including
                         farm_id, harvest_date, and optionally growing_area

        Returns:
            Dictionary mapping TLCs to contamination probability (source lots only)
        """
        source_contamination: dict[str, float] = {}

        for tlc, metadata in lot_metadata.items():
            farm_id = metadata.get("farm_id")
            harvest_date = metadata.get("harvest_date")
            growing_area = metadata.get("growing_area")

            if farm_id is None or harvest_date is None:
                continue

            # Check each contamination event
            for event in self.contamination_events:
                if str(event.farm_id) != str(farm_id):
                    continue

                if event.is_tlc_affected(tlc, harvest_date, growing_area):
                    # Mark as contaminated
                    contamination_prob = event.contamination_rate
                    source_contamination[tlc] = contamination_prob
                    self.contaminated_source_tlcs.add(tlc)
                    if tlc not in event.contaminated_tlcs:
                        event.contaminated_tlcs.append(tlc)

                    # Update lot graph if lot exists
                    if tlc in self.lot_graph.lots:
                        self.lot_graph.lots[tlc].is_contaminated = True
                        self.lot_graph.lots[tlc].contamination_probability = contamination_prob
                        self.lot_graph.lots[tlc].contamination_source = event.contamination_source

        return source_contamination

    def propagate_contamination(self) -> dict[str, float]:
        """
        Propagate contamination through the lot graph to downstream products.

        Uses the lot graph's forward edges to calculate contamination
        probability for all downstream lots based on source contamination
        and edge weights (which represent lot code certainty).

        Returns:
            Dictionary mapping all TLCs to their contamination probability
        """
        self.contamination_propagation = {}

        # Start with source contamination
        for source_tlc in self.contaminated_source_tlcs:
            if source_tlc in self.lot_graph.lots:
                source_prob = self.lot_graph.lots[source_tlc].contamination_probability
            else:
                source_prob = 1.0

            # Propagate forward through graph
            propagation = self.lot_graph.propagate_contamination(source_tlc, source_prob)

            # Merge with existing propagation using probabilistic union
            # P(A OR B) = P(A) + P(B) - P(A)*P(B) = 1 - (1-P(A))*(1-P(B))
            # This correctly models independent contamination events
            for tlc, prob in propagation.items():
                if tlc not in self.contamination_propagation:
                    self.contamination_propagation[tlc] = prob
                else:
                    existing = self.contamination_propagation[tlc]
                    # Probabilistic union: probability of contamination from at least one source
                    self.contamination_propagation[tlc] = existing + prob - (existing * prob)

        return self.contamination_propagation

    def get_contaminated_tlcs(self, min_probability: float = 0.0) -> list[str]:
        """
        Get all TLCs with contamination probability above threshold.

        Args:
            min_probability: Minimum contamination probability to include

        Returns:
            List of TLCs that may be contaminated
        """
        return [
            tlc for tlc, prob in self.contamination_propagation.items()
            if prob > min_probability
        ]

    def get_source_farm_ids(self) -> set[UUID]:
        """Get IDs of farms that are contamination sources."""
        return {event.farm_id for event in self.contamination_events}

    def get_contamination_summary(self) -> dict:
        """
        Get a summary of contamination seeding results.

        Returns:
            Dictionary with contamination statistics
        """
        return {
            "num_contamination_events": len(self.contamination_events),
            "source_farms": [
                {"id": str(e.farm_id), "name": e.farm_name, "pathogen": e.pathogen}
                for e in self.contamination_events
            ],
            "num_source_tlcs": len(self.contaminated_source_tlcs),
            "source_tlcs": list(self.contaminated_source_tlcs),
            "num_affected_tlcs": len(self.contamination_propagation),
            "contamination_by_probability": {
                "high (>0.75)": len([p for p in self.contamination_propagation.values() if p > 0.75]),
                "medium (0.25-0.75)": len([p for p in self.contamination_propagation.values() if 0.25 <= p <= 0.75]),
                "low (<0.25)": len([p for p in self.contamination_propagation.values() if p < 0.25]),
            }
        }
