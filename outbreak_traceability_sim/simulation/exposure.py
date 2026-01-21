"""
Exposure and case generator for outbreak simulation.

Simulates consumer exposures at retail locations and generates
illness cases based on contamination probability.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
import random

from ..models.base import ProductCategory
from ..models.lots import LotGraph
from .network import SupplyChainNetwork


class ExposureType(str, Enum):
    """Type of consumer exposure."""
    RETAIL_PURCHASE = "retail_purchase"  # Bought whole cucumbers
    DELI_CONSUMPTION = "deli_consumption"  # Ate deli salad at store
    RESTAURANT = "restaurant"  # Ate at restaurant


class CaseStatus(str, Enum):
    """Status of an illness case."""
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    SUSPECTED = "suspected"


@dataclass
class Consumer:
    """Represents a consumer who may be exposed to contaminated product."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""  # Anonymized
    age: int = 35
    location_city: str = ""
    location_state: str = ""


@dataclass
class Exposure:
    """
    Represents a consumer's exposure to product at a retail location.

    An exposure occurs when a consumer purchases or consumes a product
    that may be linked to contaminated lots.
    """
    id: UUID = field(default_factory=uuid4)
    consumer_id: UUID = field(default_factory=uuid4)
    location_id: UUID = field(default_factory=uuid4)
    location_name: str = ""

    exposure_date: datetime = field(default_factory=datetime.now)
    exposure_type: ExposureType = ExposureType.RETAIL_PURCHASE

    # Product information
    product_category: ProductCategory = ProductCategory.FRESH_CUCUMBERS
    tlc: Optional[str] = None  # TLC if known (for deterministic tracking)
    possible_tlcs: list[str] = field(default_factory=list)  # For probabilistic

    # Contamination probability based on lot tracking
    contamination_probability: float = 0.0

    # Was consumer actually exposed to contamination?
    was_exposed: bool = False


@dataclass
class IllnessCase:
    """
    Represents a confirmed or probable illness case.

    Cases are generated from exposures where the consumer became ill
    after exposure to contaminated product.

    Note: For bulk produce like cucumbers, consumers do NOT have TLC
    information. Investigation relies on interviewing patients to
    determine exposure location and estimated purchase date, then
    requesting records from retailers for a time window.
    """
    id: UUID = field(default_factory=uuid4)
    consumer_id: UUID = field(default_factory=uuid4)
    exposure_id: UUID = field(default_factory=uuid4)

    # Timing
    exposure_date: date = field(default_factory=date.today)  # Actual (ground truth)
    onset_date: date = field(default_factory=date.today)
    report_date: date = field(default_factory=date.today)

    # Case details
    status: CaseStatus = CaseStatus.CONFIRMED
    pathogen: str = "Salmonella"
    hospitalized: bool = False

    # Interview results (what investigation knows)
    was_interviewed: bool = False
    interview_date: Optional[date] = None
    reported_exposure_location_id: Optional[UUID] = None  # Where patient says they bought
    reported_exposure_location_name: str = ""
    estimated_purchase_date: Optional[date] = None  # Patient's recollection (may be off)
    purchase_date_uncertainty_days: int = 3  # How uncertain the patient is

    # Exposure location (ground truth for simulation)
    exposure_location_id: UUID = field(default_factory=uuid4)
    exposure_location_name: str = ""
    exposure_product: ProductCategory = ProductCategory.FRESH_CUCUMBERS

    # Note: Consumers do NOT have TLC info for bulk produce
    # These fields removed - investigation uses record window lookup instead

    # For simulation tracking (ground truth only)
    actual_contamination_source_tlc: Optional[str] = None


class ExposureGenerator:
    """
    Generates consumer exposures at retail locations.

    Simulates consumers purchasing products and calculates their
    contamination probability based on lot flow through the supply chain.
    """

    def __init__(
        self,
        network: SupplyChainNetwork,
        lot_graph: LotGraph,
        contamination_propagation: dict[str, float],
        random_seed: Optional[int] = None
    ):
        """
        Initialize the exposure generator.

        Args:
            network: Supply chain network
            lot_graph: Lot tracking graph
            contamination_propagation: TLC -> contamination probability
            random_seed: Random seed for reproducibility
        """
        self.network = network
        self.lot_graph = lot_graph
        self.contamination = contamination_propagation

        if random_seed is not None:
            random.seed(random_seed)

        self.exposures: list[Exposure] = []
        self.consumers: dict[UUID, Consumer] = {}

    def _create_consumer(self, location_city: str, location_state: str) -> Consumer:
        """Create a new consumer."""
        consumer = Consumer(
            name=f"Consumer_{len(self.consumers) + 1}",
            age=random.randint(18, 80),
            location_city=location_city,
            location_state=location_state,
        )
        self.consumers[consumer.id] = consumer
        return consumer

    def _get_contamination_probability(
        self,
        tlc: str,
    ) -> tuple[float, bool]:
        """
        Calculate contamination probability for a given TLC.

        The contamination_propagation dict already contains the probability
        for each TLC, accounting for probabilistic lot graph linkages.
        We simply look up the probability and determine if exposure occurred.

        Args:
            tlc: The traceability lot code being consumed

        Returns:
            Tuple of (contamination_probability, was_actually_exposed)
        """
        # Look up contamination probability for this TLC
        # The seeder's propagation already accounts for probabilistic linkages
        contam_prob = self.contamination.get(tlc, 0.0)

        # Determine if actually exposed based on contamination probability
        was_exposed = random.random() < contam_prob
        return contam_prob, was_exposed

    def generate_exposures(
        self,
        node_inventory: dict[UUID, list],  # From flow simulator
        start_date: date,
        end_date: date,
        daily_customers_per_retailer: int = 50,
        cucumber_purchase_rate: float = 0.15,  # 15% buy cucumbers
        deli_consumption_rate: float = 0.05,  # 5% eat deli salad
    ) -> list[Exposure]:
        """
        Generate consumer exposures throughout the simulation period.

        Args:
            node_inventory: Inventory records by node ID
            start_date: Start of exposure period
            end_date: End of exposure period
            daily_customers_per_retailer: Average customers per day
            cucumber_purchase_rate: Fraction who buy cucumbers
            deli_consumption_rate: Fraction who eat deli salad

        Returns:
            List of generated exposures
        """
        exposures = []

        current_date = start_date
        while current_date <= end_date:
            # Process each retailer
            for retailer_id, retailer in self.network.retailers.items():
                # Get available TLCs at this retailer on this date
                # Note: Retailer inventory contains actual TLCs received (ground truth)
                # The DC's probabilistic tracking uncertainty is handled in investigation,
                # not at the exposure/contamination level
                available_tlcs = []

                for inv in node_inventory.get(retailer_id, []):
                    if inv.received_date.date() <= current_date:
                        available_tlcs.append(inv.tlc)

                if not available_tlcs:
                    continue

                # Generate customer exposures
                num_customers = random.randint(
                    daily_customers_per_retailer // 2,
                    daily_customers_per_retailer * 2
                )

                for _ in range(num_customers):
                    # Cucumber purchase
                    if random.random() < cucumber_purchase_rate and available_tlcs:
                        selected_tlc = random.choice(available_tlcs)
                        consumer = self._create_consumer(
                            retailer.location.city,
                            retailer.location.state
                        )

                        prob, was_exposed = self._get_contamination_probability(selected_tlc)

                        exposure = Exposure(
                            consumer_id=consumer.id,
                            location_id=retailer_id,
                            location_name=f"{retailer.store_name} #{retailer.store_number}",
                            exposure_date=datetime.combine(current_date, datetime.min.time()),
                            exposure_type=ExposureType.RETAIL_PURCHASE,
                            product_category=ProductCategory.FRESH_CUCUMBERS,
                            tlc=selected_tlc,
                            possible_tlcs=[selected_tlc],
                            contamination_probability=prob,
                            was_exposed=was_exposed,
                        )
                        exposures.append(exposure)

                # Deli consumption (if retailer has deli)
                if retailer.has_deli and retailer.deli_id:
                    # Look up inventory at the deli node (not the retailer)
                    deli_inv = node_inventory.get(retailer.deli_id, [])
                    deli_tlcs = [
                        inv.tlc for inv in deli_inv
                        if inv.product.category == ProductCategory.CUCUMBER_SALAD
                        and inv.received_date.date() <= current_date
                    ]

                    for _ in range(num_customers):
                        if random.random() < deli_consumption_rate and deli_tlcs:
                            selected_tlc = random.choice(deli_tlcs)
                            consumer = self._create_consumer(
                                retailer.location.city,
                                retailer.location.state
                            )

                            prob, was_exposed = self._get_contamination_probability(selected_tlc)

                            exposure = Exposure(
                                consumer_id=consumer.id,
                                location_id=retailer.deli_id,  # Use deli node ID for case attribution
                                location_name=f"{retailer.store_name} #{retailer.store_number} Deli",
                                exposure_date=datetime.combine(current_date, datetime.min.time()),
                                exposure_type=ExposureType.DELI_CONSUMPTION,
                                product_category=ProductCategory.CUCUMBER_SALAD,
                                tlc=selected_tlc,
                                possible_tlcs=[selected_tlc],
                                contamination_probability=prob,
                                was_exposed=was_exposed,
                            )
                            exposures.append(exposure)

            current_date += timedelta(days=1)

        self.exposures = exposures
        return exposures

    def get_exposed_consumers(self) -> list[Exposure]:
        """Get all exposures where consumer was actually exposed."""
        return [e for e in self.exposures if e.was_exposed]

    def get_exposure_summary(self) -> dict:
        """Get summary statistics of exposures."""
        exposed = self.get_exposed_consumers()
        return {
            "total_exposures": len(self.exposures),
            "total_consumers": len(self.consumers),
            "actually_exposed": len(exposed),
            "by_type": {
                "retail_purchase": len([e for e in self.exposures
                                       if e.exposure_type == ExposureType.RETAIL_PURCHASE]),
                "deli_consumption": len([e for e in self.exposures
                                        if e.exposure_type == ExposureType.DELI_CONSUMPTION]),
            },
            "by_product": {
                "cucumbers": len([e for e in self.exposures
                                 if e.product_category == ProductCategory.FRESH_CUCUMBERS]),
                "salad": len([e for e in self.exposures
                             if e.product_category == ProductCategory.CUCUMBER_SALAD]),
            },
        }


class CaseGenerator:
    """
    Generates illness cases from consumer exposures.

    Converts exposures with contamination into illness cases with
    appropriate onset timing and reporting delays.
    """

    def __init__(
        self,
        pathogen: str = "Salmonella",
        random_seed: Optional[int] = None
    ):
        """
        Initialize the case generator.

        Args:
            pathogen: Name of the pathogen
            random_seed: Random seed for reproducibility
        """
        self.pathogen = pathogen

        if random_seed is not None:
            random.seed(random_seed)

        self.cases: list[IllnessCase] = []

        # Pathogen-specific parameters (Salmonella defaults)
        self.infection_rate = 0.3  # 30% of exposed become ill
        self.incubation_days_min = 1
        self.incubation_days_max = 3
        self.reporting_delay_min = 2
        self.reporting_delay_max = 14
        self.hospitalization_rate = 0.20

    def configure_pathogen(
        self,
        infection_rate: float = 0.3,
        incubation_min: int = 1,
        incubation_max: int = 3,
        reporting_delay_min: int = 2,
        reporting_delay_max: int = 14,
        hospitalization_rate: float = 0.20
    ) -> None:
        """Configure pathogen-specific parameters."""
        self.infection_rate = infection_rate
        self.incubation_days_min = incubation_min
        self.incubation_days_max = incubation_max
        self.reporting_delay_min = reporting_delay_min
        self.reporting_delay_max = reporting_delay_max
        self.hospitalization_rate = hospitalization_rate

    def generate_cases(
        self,
        exposures: list[Exposure],
        interview_success_rate: float = 0.7,  # 70% successfully interviewed
    ) -> list[IllnessCase]:
        """
        Generate illness cases from exposures using realistic investigation model.

        For bulk produce outbreaks:
        - Consumers do NOT have TLC info (no receipts with lot codes)
        - Epidemiologists interview patients to determine:
          - Where they purchased (exposure location)
          - Approximately when they purchased (estimated date with uncertainty)
        - FDA then requests records from retail location for a time window

        Args:
            exposures: List of consumer exposures
            interview_success_rate: Fraction of cases successfully interviewed

        Returns:
            List of generated illness cases
        """
        cases = []

        # Only consider exposures where consumer was actually exposed
        exposed = [e for e in exposures if e.was_exposed]

        for exposure in exposed:
            # Determine if this exposure becomes a case
            if random.random() > self.infection_rate:
                continue

            # Calculate timing
            exposure_date = exposure.exposure_date.date()
            incubation_days = random.randint(
                self.incubation_days_min,
                self.incubation_days_max
            )
            onset_date = exposure_date + timedelta(days=incubation_days)

            reporting_delay = random.randint(
                self.reporting_delay_min,
                self.reporting_delay_max
            )
            report_date = onset_date + timedelta(days=reporting_delay)

            # Determine if case is successfully interviewed
            was_interviewed = random.random() < interview_success_rate

            # Interview information (only available if interviewed)
            interview_date = None
            reported_location_id = None
            reported_location_name = ""
            estimated_purchase_date = None
            purchase_uncertainty = 3

            if was_interviewed:
                # Interview happens a few days after report
                interview_date = report_date + timedelta(days=random.randint(1, 5))

                # Patient correctly recalls where they bought (usually accurate)
                if random.random() < 0.95:  # 95% correctly recall location
                    reported_location_id = exposure.location_id
                    reported_location_name = exposure.location_name

                # Patient estimates purchase date (with some error)
                # Days since actual purchase when interviewed
                days_since_purchase = (interview_date - exposure_date).days
                # Patient recall error increases with time
                recall_error = random.randint(-3, 3) + (days_since_purchase // 7)
                estimated_purchase_date = exposure_date + timedelta(days=recall_error)
                # Uncertainty increases with time elapsed
                purchase_uncertainty = min(7, 2 + days_since_purchase // 5)

            case = IllnessCase(
                consumer_id=exposure.consumer_id,
                exposure_id=exposure.id,
                exposure_date=exposure_date,  # Ground truth
                onset_date=onset_date,
                report_date=report_date,
                status=CaseStatus.CONFIRMED,
                pathogen=self.pathogen,
                hospitalized=random.random() < self.hospitalization_rate,
                # Interview results
                was_interviewed=was_interviewed,
                interview_date=interview_date,
                reported_exposure_location_id=reported_location_id,
                reported_exposure_location_name=reported_location_name,
                estimated_purchase_date=estimated_purchase_date,
                purchase_date_uncertainty_days=purchase_uncertainty,
                # Ground truth (for simulation validation)
                exposure_location_id=exposure.location_id,
                exposure_location_name=exposure.location_name,
                exposure_product=exposure.product_category,
                actual_contamination_source_tlc=exposure.tlc,
            )
            cases.append(case)

        self.cases = cases
        return cases

    def get_cases_by_report_date(
        self,
        as_of_date: date
    ) -> list[IllnessCase]:
        """Get cases reported on or before a given date."""
        return [c for c in self.cases if c.report_date <= as_of_date]

    def get_case_summary(self) -> dict:
        """Get summary statistics of generated cases."""
        if not self.cases:
            return {"total_cases": 0}

        # Filter out any None onset_dates for safety
        onset_dates = [c.onset_date for c in self.cases if c.onset_date]
        interviewed_with_info = [
            c for c in self.cases
            if c.was_interviewed and c.reported_exposure_location_id and c.estimated_purchase_date
        ]

        # Build onset date range safely
        onset_date_range = {}
        if onset_dates:
            onset_date_range = {
                "first": min(onset_dates).isoformat(),
                "last": max(onset_dates).isoformat(),
            }

        return {
            "total_cases": len(self.cases),
            "hospitalized": len([c for c in self.cases if c.hospitalized]),
            "hospitalization_rate": len([c for c in self.cases if c.hospitalized]) / len(self.cases),
            "cases_interviewed": len([c for c in self.cases if c.was_interviewed]),
            "cases_with_usable_info": len(interviewed_with_info),
            "onset_date_range": onset_date_range,
            "by_product": {
                "cucumbers": len([c for c in self.cases
                                 if c.exposure_product == ProductCategory.FRESH_CUCUMBERS]),
                "salad": len([c for c in self.cases
                             if c.exposure_product == ProductCategory.CUCUMBER_SALAD]),
            },
            "exposure_locations": len(set(c.exposure_location_id for c in self.cases)),
        }

    def get_epi_curve_data(self) -> list[tuple[date, int]]:
        """Get data for epidemiological curve (onset dates)."""
        if not self.cases:
            return []

        onset_counts: dict[date, int] = {}
        for case in self.cases:
            onset_counts[case.onset_date] = onset_counts.get(case.onset_date, 0) + 1

        return sorted(onset_counts.items())
