"""
Product flow simulator for outbreak simulation.

Simulates the movement of products through the supply chain network,
creating lot code records at each step. Supports both deterministic
and probabilistic lot code assignment.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
import random

from ..models.base import ProductCategory, ProductDescription, Quantity, UnitOfMeasure
from ..models.nodes import (
    Farm,
    Packer,
    DistributionCenter,
    Processor,
    Deli,
    Retailer,
    LotCodeAssignmentMode,
    InventoryRecord,
)
from ..models.lots import LotTracker, LotGraph, TrackingMode, LotCodeRecord
from .network import SupplyChainNetwork, SupplyChainEdge
from .timing import (
    TimingConfig,
    calculate_farm_to_packer_transit,
    calculate_packer_to_dc_transit,
    calculate_dc_to_retail_transit,
    calculate_processor_to_dc_transit,
    get_random_business_hour,
    advance_to_next_business_hour,
)


@dataclass
class Shipment:
    """Represents a shipment of product between supply chain nodes."""
    id: UUID = field(default_factory=uuid4)
    source_node_id: UUID = field(default_factory=uuid4)
    dest_node_id: UUID = field(default_factory=uuid4)
    ship_date: datetime = field(default_factory=datetime.now)
    receive_date: Optional[datetime] = None

    product_category: ProductCategory = ProductCategory.FRESH_CUCUMBERS
    quantity: Quantity = field(default_factory=lambda: Quantity(value=100, unit=UnitOfMeasure.POUNDS))

    # Lot code tracking
    source_tlcs: list[str] = field(default_factory=list)
    dest_tlc: Optional[str] = None

    # For probabilistic tracking
    tlc_probabilities: dict[str, float] = field(default_factory=dict)

    # Contamination tracking
    contains_contaminated_product: bool = False
    contamination_probability: float = 0.0


@dataclass
class ProductionBatch:
    """Represents a production/transformation batch at a processor."""
    id: UUID = field(default_factory=uuid4)
    processor_id: UUID = field(default_factory=uuid4)
    production_date: datetime = field(default_factory=datetime.now)

    input_product: ProductCategory = ProductCategory.FRESH_CUCUMBERS
    output_product: ProductCategory = ProductCategory.CUCUMBER_SALAD

    input_quantity: Quantity = field(default_factory=lambda: Quantity(value=100, unit=UnitOfMeasure.POUNDS))
    output_quantity: Quantity = field(default_factory=lambda: Quantity(value=80, unit=UnitOfMeasure.POUNDS))

    input_tlcs: list[str] = field(default_factory=list)
    input_tlc_probabilities: dict[str, float] = field(default_factory=dict)
    output_tlc: str = ""

    contamination_probability: float = 0.0


class ProductFlowSimulator:
    """
    Simulates product flow through the supply chain network.

    Creates lot code records as products move from farms through the
    supply chain to retail endpoints. Supports both deterministic and
    probabilistic lot code assignment based on node configuration.
    """

    def __init__(
        self,
        network: SupplyChainNetwork,
        start_date: date,
        end_date: date,
        random_seed: Optional[int] = None,
        timing_config: Optional[TimingConfig] = None
    ):
        """
        Initialize the product flow simulator.

        Args:
            network: The supply chain network
            start_date: Simulation start date
            end_date: Simulation end date
            random_seed: Random seed for reproducibility
            timing_config: Configuration for realistic transit/processing times
        """
        self.network = network
        self.start_date = start_date
        self.end_date = end_date
        self.timing_config = timing_config or TimingConfig()

        # Validate date range
        if end_date < start_date:
            raise ValueError(
                f"end_date ({end_date}) must be >= start_date ({start_date})"
            )

        if random_seed is not None:
            random.seed(random_seed)

        # Tracking structures
        self.lot_graph = LotGraph()
        self.shipments: list[Shipment] = []
        self.production_batches: list[ProductionBatch] = []

        # Lot metadata for contamination seeding
        self.lot_metadata: dict[str, dict] = {}

        # Node inventory tracking
        self.node_inventory: dict[UUID, list[InventoryRecord]] = {}

        # Shipment tracking: (dest_node_id, tlc) -> Shipment
        # Used by investigation to look up probabilistic alternatives
        self.tlc_shipment_map: dict[tuple[UUID, str], Shipment] = {}

        # Statistics
        self.total_lots_created = 0
        self.deterministic_lot_links = 0
        self.probabilistic_lot_links = 0

    def _init_inventory(self, node_id: UUID) -> None:
        """Initialize inventory tracking for a node."""
        if node_id not in self.node_inventory:
            self.node_inventory[node_id] = []

    def _add_to_inventory(
        self,
        node_id: UUID,
        tlc: str,
        product: ProductDescription,
        quantity: Quantity,
        received_date: datetime,
        source_node_id: UUID,
        hold_hours: Optional[float] = None
    ) -> None:
        """Add product to a node's inventory.

        Args:
            node_id: Destination node ID
            tlc: Traceability Lot Code
            product: Product description
            quantity: Quantity received
            received_date: When product was received
            source_node_id: Source node ID
            hold_hours: Optional hold time before product is available (inspection, processing)
        """
        self._init_inventory(node_id)

        # Calculate when product becomes available for outbound shipping
        if hold_hours is not None and hold_hours > 0:
            available_date = received_date + timedelta(hours=hold_hours)
        else:
            available_date = received_date

        record = InventoryRecord(
            tlc=tlc,
            product=product,
            quantity_received=quantity,
            quantity_remaining=Quantity(value=quantity.value, unit=quantity.unit),
            received_date=received_date,
            source_node_id=source_node_id,
            available_date=available_date,
        )
        self.node_inventory[node_id].append(record)

    def _get_inventory_for_shipment(
        self,
        node_id: UUID,
        product_category: ProductCategory,
        quantity_needed: float,
        ship_date: datetime,
        tracking_mode: TrackingMode
    ) -> tuple[list[str], dict[str, float]]:
        """
        Get inventory TLCs for a shipment based on tracking mode.

        Args:
            node_id: Node shipping from
            product_category: Product category needed
            quantity_needed: Quantity to ship
            ship_date: Date of shipment
            tracking_mode: Deterministic or probabilistic

        Returns:
            Tuple of (definite_tlcs, tlc_probabilities)
        """
        self._init_inventory(node_id)

        # Get eligible inventory (available before ship date, has remaining quantity)
        # Use available_date if set, otherwise fall back to received_date
        eligible = [
            inv for inv in self.node_inventory[node_id]
            if inv.product.category == product_category
            and inv.quantity_remaining.value > 0
            and (inv.available_date or inv.received_date) <= ship_date
        ]

        if not eligible:
            return [], {}

        if tracking_mode == TrackingMode.DETERMINISTIC:
            # FIFO - take from oldest available first
            eligible.sort(key=lambda x: x.available_date or x.received_date)
            selected_tlcs = []
            remaining = quantity_needed

            for inv in eligible:
                if remaining <= 0:
                    break
                take = min(remaining, inv.quantity_remaining.value)
                selected_tlcs.append(inv.tlc)
                inv.quantity_remaining = Quantity(
                    value=inv.quantity_remaining.value - take,
                    unit=inv.quantity_remaining.unit
                )
                remaining -= take
                self.deterministic_lot_links += 1

            return selected_tlcs, {}

        else:  # PROBABILISTIC
            # Get node's DC configuration for date window
            node = self.network.get_node(node_id)
            date_window_days = 7
            if isinstance(node, DistributionCenter):
                date_window_days = node.date_window_days

            # Filter to date window (use available_date for eligibility)
            window_start = ship_date - timedelta(days=date_window_days)
            in_window = [
                inv for inv in eligible
                if window_start <= (inv.available_date or inv.received_date) <= ship_date
            ]

            if not in_window:
                in_window = eligible  # Fallback to all eligible

            # Calculate probabilities based on quantity
            total_qty = sum(inv.quantity_remaining.value for inv in in_window)
            if total_qty == 0:
                # Equal probability
                prob = 1.0 / len(in_window) if in_window else 0
                probabilities = {inv.tlc: prob for inv in in_window}
            else:
                probabilities = {
                    inv.tlc: inv.quantity_remaining.value / total_qty
                    for inv in in_window
                }

            self.probabilistic_lot_links += len(probabilities)

            # IMPORTANT: Also determine the ACTUAL TLC used (ground truth)
            # This simulates what actually happened vs what the traceability system knows
            # Use FIFO as the ground truth (oldest available inventory first)
            in_window_sorted = sorted(in_window, key=lambda x: x.available_date or x.received_date)
            actual_tlcs = []
            remaining = quantity_needed

            for inv in in_window_sorted:
                if remaining <= 0:
                    break
                take = min(remaining, inv.quantity_remaining.value)
                actual_tlcs.append(inv.tlc)
                inv.quantity_remaining = Quantity(
                    value=inv.quantity_remaining.value - take,
                    unit=inv.quantity_remaining.unit
                )
                remaining -= take
                self.deterministic_lot_links += 1

            # Return BOTH: actual TLCs (ground truth) AND probabilistic estimates
            return actual_tlcs, probabilities

    def simulate_farm_harvests(self) -> dict[UUID, list[str]]:
        """
        Simulate harvests at all farms for the date range.

        Returns:
            Dictionary mapping farm ID to list of TLCs created
        """
        farm_tlcs: dict[UUID, list[str]] = {}

        current_date = self.start_date
        while current_date <= self.end_date:
            for farm_id, farm in self.network.farms.items():
                # Each farm harvests from each growing area
                for area in farm.growing_areas:
                    # Generate TLC
                    tlc = farm.generate_lot_code(current_date, area.area_id)

                    # Use realistic harvest time (business hours)
                    harvest_datetime = get_random_business_hour(
                        datetime.combine(current_date, datetime.min.time()),
                        self.timing_config
                    )

                    # Create lot record
                    # TLCS (Traceability Lot Code Source) is the GLN of the location
                    # where the TLC was assigned - in this case, the farm
                    farm_gln = farm.location.gln
                    lot = LotCodeRecord(
                        tlc=tlc,
                        tlcs=farm_gln,  # FSMA 204: TLCS is GLN of initial packing location
                        created_at=harvest_datetime,
                        created_by_node_id=farm_id,
                        created_at_location_id=farm_id,  # UUID of the node
                        product_category=ProductCategory.FRESH_CUCUMBERS.value,
                        product_description="Fresh Cucumbers",
                        initial_quantity_value=random.randint(3000, 8000),
                        initial_quantity_unit=UnitOfMeasure.POUNDS.value,
                    )

                    self.lot_graph.add_lot(lot)
                    self.total_lots_created += 1

                    # Store metadata for contamination seeding
                    self.lot_metadata[tlc] = {
                        "farm_id": farm_id,
                        "harvest_date": current_date,
                        "growing_area": area.area_id,
                    }

                    # Track by farm
                    if farm_id not in farm_tlcs:
                        farm_tlcs[farm_id] = []
                    farm_tlcs[farm_id].append(tlc)

                    # Add to farm's "inventory" for shipping
                    # Product needs cooling time before it can be shipped
                    self._add_to_inventory(
                        farm_id, tlc,
                        ProductDescription(
                            category=ProductCategory.FRESH_CUCUMBERS,
                            commodity="Cucumbers",
                            description="Fresh Cucumbers"
                        ),
                        Quantity(value=lot.initial_quantity_value, unit=UnitOfMeasure.POUNDS),
                        harvest_datetime,
                        farm_id,
                        hold_hours=self.timing_config.cooling_hold_hours
                    )

            current_date += timedelta(days=1)

        return farm_tlcs

    def simulate_shipments_from_farms(self) -> list[Shipment]:
        """Simulate shipments from farms to packers."""
        shipments = []

        for edge in self.network.edges:
            source_node = self.network.get_node(edge.source_id)
            if not isinstance(source_node, Farm):
                continue

            # Simulate shipments throughout the date range
            current_date = self.start_date
            while current_date <= self.end_date:
                # Probabilistic shipment based on frequency
                if random.random() < edge.shipments_per_week / 7.0:
                    # Use realistic business hours for shipment
                    ship_datetime = get_random_business_hour(
                        datetime.combine(current_date, datetime.min.time()),
                        self.timing_config
                    )

                    # Get TLCs to ship (farms use deterministic)
                    source_tlcs, _ = self._get_inventory_for_shipment(
                        edge.source_id,
                        ProductCategory.FRESH_CUCUMBERS,
                        edge.typical_volume_per_shipment.value,
                        ship_datetime,
                        TrackingMode.DETERMINISTIC
                    )

                    if source_tlcs:
                        # Calculate transit time based on distance
                        transit_time = calculate_farm_to_packer_transit(
                            self.timing_config,
                            edge.distance_miles
                        )

                        shipment = Shipment(
                            source_node_id=edge.source_id,
                            dest_node_id=edge.destination_id,
                            ship_date=ship_datetime,
                            receive_date=ship_datetime + transit_time,
                            product_category=ProductCategory.FRESH_CUCUMBERS,
                            quantity=edge.typical_volume_per_shipment,
                            source_tlcs=source_tlcs,
                        )
                        shipments.append(shipment)

                        # Add to packer inventory (packers maintain source TLCs)
                        # Packer processing time before product is available
                        for tlc in source_tlcs:
                            self._add_to_inventory(
                                edge.destination_id, tlc,
                                ProductDescription(
                                    category=ProductCategory.FRESH_CUCUMBERS,
                                    commodity="Cucumbers",
                                    description="Fresh Cucumbers"
                                ),
                                Quantity(
                                    value=edge.typical_volume_per_shipment.value / len(source_tlcs),
                                    unit=edge.typical_volume_per_shipment.unit
                                ),
                                shipment.receive_date,
                                edge.source_id,
                                hold_hours=self.timing_config.packer_processing_hours
                            )

                current_date += timedelta(days=1)

        self.shipments.extend(shipments)
        return shipments

    def simulate_shipments_from_packers(self) -> list[Shipment]:
        """Simulate shipments from packers to distribution centers or processors."""
        shipments = []

        for edge in self.network.edges:
            source_node = self.network.get_node(edge.source_id)
            if not isinstance(source_node, Packer):
                continue

            # Start after products have had time to arrive and be processed at packer
            start_offset_days = 2
            current_date = self.start_date + timedelta(days=start_offset_days)
            while current_date <= self.end_date:
                if random.random() < edge.shipments_per_week / 7.0:
                    # Use realistic business hours
                    ship_datetime = get_random_business_hour(
                        datetime.combine(current_date, datetime.min.time()),
                        self.timing_config
                    )

                    # Packers maintain source TLCs (deterministic)
                    source_tlcs, _ = self._get_inventory_for_shipment(
                        edge.source_id,
                        ProductCategory.FRESH_CUCUMBERS,
                        edge.typical_volume_per_shipment.value,
                        ship_datetime,
                        TrackingMode.DETERMINISTIC
                    )

                    if source_tlcs:
                        # Calculate transit time based on distance
                        transit_time = calculate_packer_to_dc_transit(
                            self.timing_config,
                            edge.distance_miles
                        )

                        shipment = Shipment(
                            source_node_id=edge.source_id,
                            dest_node_id=edge.destination_id,
                            ship_date=ship_datetime,
                            receive_date=ship_datetime + transit_time,
                            product_category=ProductCategory.FRESH_CUCUMBERS,
                            quantity=edge.typical_volume_per_shipment,
                            source_tlcs=source_tlcs,
                        )
                        shipments.append(shipment)

                        # Add to DC inventory with receiving inspection hold time
                        dest_node = self.network.get_node(edge.destination_id)
                        hold_hours = self.timing_config.dc_receiving_inspection_hours if isinstance(dest_node, DistributionCenter) else 0

                        for tlc in source_tlcs:
                            self._add_to_inventory(
                                edge.destination_id, tlc,
                                ProductDescription(
                                    category=ProductCategory.FRESH_CUCUMBERS,
                                    commodity="Cucumbers",
                                    description="Fresh Cucumbers"
                                ),
                                Quantity(
                                    value=edge.typical_volume_per_shipment.value / len(source_tlcs),
                                    unit=edge.typical_volume_per_shipment.unit
                                ),
                                shipment.receive_date,
                                edge.source_id,
                                hold_hours=hold_hours
                            )

                current_date += timedelta(days=1)

        self.shipments.extend(shipments)
        return shipments

    def simulate_shipments_from_dcs(self) -> list[Shipment]:
        """
        Simulate shipments from distribution centers to retailers/delis.

        FSMA 204 Compliance: DCs do NOT create new TLCs. They pass through
        the TLCs they received from packers/processors. The difference between
        deterministic and probabilistic modes is:
        - DETERMINISTIC: DC knows exactly which TLCs are in each shipment
        - PROBABILISTIC: DC estimates which TLCs might be in the shipment
          based on inventory strategy (FIFO, date window, etc.)

        For probabilistic mode, we record the uncertainty by creating linkages
        in the lot graph that reflect possible (not definite) source TLCs.
        """
        shipments = []

        for edge in self.network.edges:
            source_node = self.network.get_node(edge.source_id)
            if not isinstance(source_node, DistributionCenter):
                continue

            # Get tracking mode for this DC
            dc_mode = self.network.lot_tracker.get_mode_for_node(edge.source_id)

            # Determine product category based on edge
            product_category = edge.product_categories[0] if edge.product_categories else ProductCategory.FRESH_CUCUMBERS

            # Start after product has arrived and been inspected at DC
            start_offset_days = 5  # Allow time for full supply chain to ramp up
            current_date = self.start_date + timedelta(days=start_offset_days)
            while current_date <= self.end_date:
                if random.random() < edge.shipments_per_week / 7.0:
                    # Use realistic business hours
                    ship_datetime = get_random_business_hour(
                        datetime.combine(current_date, datetime.min.time()),
                        self.timing_config
                    )

                    source_tlcs, tlc_probs = self._get_inventory_for_shipment(
                        edge.source_id,
                        product_category,
                        edge.typical_volume_per_shipment.value,
                        ship_datetime,
                        dc_mode
                    )

                    if source_tlcs or tlc_probs:
                        # Calculate transit time based on distance
                        transit_time = calculate_dc_to_retail_transit(
                            self.timing_config,
                            edge.distance_miles
                        )

                        # DC passes through source TLCs - does NOT create new TLCs
                        # per FSMA 204 (TLCs only created at initial packing or transformation)
                        shipment = Shipment(
                            source_node_id=edge.source_id,
                            dest_node_id=edge.destination_id,
                            ship_date=ship_datetime,
                            receive_date=ship_datetime + transit_time,
                            product_category=product_category,
                            quantity=edge.typical_volume_per_shipment,
                            source_tlcs=source_tlcs,  # Actual TLCs shipped (ground truth)
                            dest_tlc=None,  # DC does not create new TLC
                            tlc_probabilities=tlc_probs,  # DC's probability estimates (what traceability system knows)
                        )
                        shipments.append(shipment)

                        # FSMA 204 Probabilistic Tracking Model:
                        # - source_tlcs = actual TLCs shipped (ground truth for simulation)
                        # - tlc_probs = DC's traceability estimate (what investigators see)
                        #
                        # In probabilistic mode, DC can't prove exactly which TLCs were shipped.
                        # Investigators must consider ALL TLCs the DC says MIGHT have been shipped.
                        # This is stored on the shipment for the investigation engine to use.
                        #
                        # NOTE: We do NOT add graph edges between unrelated TLCs (the old alias
                        # approach was incorrect). Instead, investigation expands scope based
                        # on shipment.tlc_probabilities.

                        # Add ONLY actual TLCs to destination inventory (ground truth)
                        # The retailer physically received these TLCs and can read the labels.
                        # Probabilistic uncertainty is about DC's records, not retailer's inventory.
                        quantity_per_tlc = edge.typical_volume_per_shipment.value / len(source_tlcs) if source_tlcs else 0

                        # Retail stocking delay before product is available to consumers
                        for tlc in source_tlcs:
                            self._add_to_inventory(
                                edge.destination_id, tlc,
                                ProductDescription(
                                    category=product_category,
                                    commodity="Cucumbers" if product_category == ProductCategory.FRESH_CUCUMBERS else "Cucumber Salad",
                                    description="Fresh Cucumbers" if product_category == ProductCategory.FRESH_CUCUMBERS else "Cucumber Salad"
                                ),
                                Quantity(value=quantity_per_tlc, unit=edge.typical_volume_per_shipment.unit),
                                shipment.receive_date,
                                edge.source_id,
                                hold_hours=self.timing_config.retail_stocking_delay_hours
                            )

                            # Track which shipment delivered this TLC to this destination
                            # Used by investigation to find probabilistic alternatives
                            self.tlc_shipment_map[(edge.destination_id, tlc)] = shipment

                current_date += timedelta(days=1)

        self.shipments.extend(shipments)
        return shipments

    def simulate_deli_production(self) -> list[ProductionBatch]:
        """
        Simulate deli operations.

        FSMA 204 Compliance: Delis do NOT create new TLCs in this simulation.
        They receive pre-processed salads from DCs (which came from Processors)
        and preserve the original TLC and TLCS from the Processor.

        Transformation CTEs at delis that would create new TLCs (e.g., making
        salads and shipping to other locations) are rare and not modeled here.
        """
        # Delis receive processed salads from DCs with existing TLCs
        # No new TLCs are created - the Processor's TLC is preserved
        # The DC -> Deli shipments already handle inventory transfer
        return []

    def simulate_shipments_from_processors(self) -> list[Shipment]:
        """
        Simulate shipments from processors to distribution centers.

        Processors transform fresh cucumbers into salads and ship to DCs.
        """
        shipments = []

        for edge in self.network.edges:
            source_node = self.network.get_node(edge.source_id)
            if not isinstance(source_node, Processor):
                continue

            # Start after product has had time to arrive at processor
            start_offset_days = 4
            current_date = self.start_date + timedelta(days=start_offset_days)
            while current_date <= self.end_date:
                if random.random() < edge.shipments_per_week / 7.0:
                    # Use realistic business hours for production
                    prod_datetime = get_random_business_hour(
                        datetime.combine(current_date, datetime.min.time()),
                        self.timing_config
                    )

                    # Get input inventory (fresh cucumbers received from packers)
                    input_tlcs, input_probs = self._get_inventory_for_shipment(
                        edge.source_id,
                        ProductCategory.FRESH_CUCUMBERS,
                        edge.typical_volume_per_shipment.value * 1.2,  # Need more input than output
                        prod_datetime,
                        TrackingMode.DETERMINISTIC  # Processors track deterministically
                    )

                    if input_tlcs or input_probs:
                        # Create output TLC for processed salad
                        output_tlc = source_node.generate_transformation_lot_code(
                            current_date,
                            "cucumber_salad",
                            input_tlcs or list(input_probs.keys())
                        )

                        # Create production batch record
                        batch = ProductionBatch(
                            processor_id=edge.source_id,
                            production_date=prod_datetime,
                            input_product=ProductCategory.FRESH_CUCUMBERS,
                            output_product=ProductCategory.CUCUMBER_SALAD,
                            input_quantity=Quantity(
                                value=edge.typical_volume_per_shipment.value * 1.2,
                                unit=UnitOfMeasure.POUNDS
                            ),
                            output_quantity=edge.typical_volume_per_shipment,
                            input_tlcs=input_tlcs,
                            input_tlc_probabilities=input_probs,
                            output_tlc=output_tlc,
                        )
                        self.production_batches.append(batch)

                        # Create output lot record
                        # TLCS (Traceability Lot Code Source) is the GLN of the location
                        # where the TLC was assigned - in this case, the processor
                        processor_gln = source_node.location.gln
                        lot = LotCodeRecord(
                            tlc=output_tlc,
                            tlcs=processor_gln,  # FSMA 204: TLCS is GLN of transformation location
                            created_at=prod_datetime,
                            created_by_node_id=edge.source_id,
                            created_at_location_id=edge.source_id,  # UUID of the node
                            product_category=ProductCategory.CUCUMBER_SALAD.value,
                            product_description="Processed Cucumber Salad",
                            initial_quantity_value=edge.typical_volume_per_shipment.value,
                            initial_quantity_unit=edge.typical_volume_per_shipment.unit.value,
                            source_tlcs=input_tlcs,
                            source_tlc_probabilities=input_probs,
                        )
                        self.lot_graph.add_lot(lot)
                        self.total_lots_created += 1

                        # Link to input lots
                        for src_tlc in input_tlcs:
                            self.lot_graph.link_lots(src_tlc, output_tlc, weight=1.0)
                        for src_tlc, prob in input_probs.items():
                            self.lot_graph.link_lots(src_tlc, output_tlc, weight=prob)

                        # Calculate transit time based on distance
                        transit_time = calculate_processor_to_dc_transit(
                            self.timing_config,
                            edge.distance_miles
                        )

                        # Create shipment to DC
                        shipment = Shipment(
                            source_node_id=edge.source_id,
                            dest_node_id=edge.destination_id,
                            ship_date=prod_datetime,
                            receive_date=prod_datetime + transit_time,
                            product_category=ProductCategory.CUCUMBER_SALAD,
                            quantity=edge.typical_volume_per_shipment,
                            source_tlcs=[output_tlc],
                            dest_tlc=output_tlc,
                        )
                        shipments.append(shipment)

                        # Add processed product to DC inventory with inspection hold
                        self._add_to_inventory(
                            edge.destination_id, output_tlc,
                            ProductDescription(
                                category=ProductCategory.CUCUMBER_SALAD,
                                commodity="Cucumber Salad",
                                description="Processed Cucumber Salad"
                            ),
                            edge.typical_volume_per_shipment,
                            shipment.receive_date,
                            edge.source_id,
                            hold_hours=self.timing_config.dc_receiving_inspection_hours
                        )

                current_date += timedelta(days=1)

        self.shipments.extend(shipments)
        return shipments

    def run_simulation(self) -> dict:
        """
        Run the complete product flow simulation.

        Returns:
            Dictionary with simulation statistics
        """
        # Phase 1: Farm harvests
        farm_tlcs = self.simulate_farm_harvests()

        # Phase 2: Farm -> Packer shipments
        farm_shipments = self.simulate_shipments_from_farms()

        # Phase 3: Packer -> DC/Processor shipments
        packer_shipments = self.simulate_shipments_from_packers()

        # Phase 4: Processor -> DC shipments (processed salads)
        processor_shipments = self.simulate_shipments_from_processors()

        # Phase 5: DC -> Retailer/Deli shipments
        dc_shipments = self.simulate_shipments_from_dcs()

        # Phase 6: Deli production (in-store salads)
        deli_batches = self.simulate_deli_production()

        return {
            "simulation_period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
                "days": (self.end_date - self.start_date).days + 1,
            },
            "lots_created": self.total_lots_created,
            "farm_lots": sum(len(tlcs) for tlcs in farm_tlcs.values()),
            "shipments": {
                "from_farms": len(farm_shipments),
                "from_packers": len(packer_shipments),
                "from_processors": len(processor_shipments),
                "from_dcs": len(dc_shipments),
                "total": len(self.shipments),
            },
            "production_batches": len(deli_batches),
            "lot_linkage": {
                "deterministic": self.deterministic_lot_links,
                "probabilistic": self.probabilistic_lot_links,
            },
        }

    def get_retail_tlcs(self) -> dict[UUID, list[str]]:
        """Get TLCs available at each retail location."""
        retail_tlcs: dict[UUID, list[str]] = {}

        # Get TLCs from retailer inventory
        for retailer_id in self.network.retailers:
            tlcs = [inv.tlc for inv in self.node_inventory.get(retailer_id, [])]
            if tlcs:
                retail_tlcs[retailer_id] = tlcs

        return retail_tlcs
