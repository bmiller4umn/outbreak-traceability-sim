"""
Supply chain network builder for outbreak simulation.

Creates a realistic supply chain network for cucumbers flowing from
farms through packers, distribution centers, and to retailers/delis.
Supports configuration of lot code tracking modes at each node.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID, uuid4
import random

from ..models.base import (
    Location,
    ContactInfo,
    ProductCategory,
    ProductDescription,
    Quantity,
    UnitOfMeasure,
)
from ..models.nodes import (
    Farm,
    Packer,
    DistributionCenter,
    Processor,
    Deli,
    Retailer,
    GrowingArea,
    LotCodeAssignmentMode,
    CalculatedLotCodeMethod,
    InventoryRecord,
    SupplyChainNode,
)
from ..models.lots import LotTracker, TrackingMode
from .timing import CITY_COORDINATES, haversine_distance


def generate_gln(company_prefix: str = "001234567") -> str:
    """
    Generate a valid GS1 Global Location Number (GLN).

    GLN is a 13-digit identifier used as the Traceability Lot Code Source (TLCS)
    per FSMA 204 requirements. The last digit is a check digit.

    Args:
        company_prefix: 7-9 digit GS1 company prefix (default is a sample prefix)

    Returns:
        13-digit GLN string with valid check digit
    """
    # Pad company prefix and add random location reference
    prefix = company_prefix[:9].ljust(9, '0')
    location_ref = f"{random.randint(0, 999):03d}"

    # First 12 digits
    digits_12 = prefix + location_ref

    # Calculate GS1 check digit
    # Multiply alternating digits by 1 and 3, sum, then 10 - (sum mod 10)
    total = 0
    for i, digit in enumerate(digits_12):
        multiplier = 3 if i % 2 == 0 else 1
        total += int(digit) * multiplier

    check_digit = (10 - (total % 10)) % 10

    return digits_12 + str(check_digit)


@dataclass
class NetworkConfig:
    """Configuration for supply chain network generation."""
    # Node counts
    num_farms: int = 5
    num_packers: int = 2
    num_distribution_centers: int = 3
    num_processors: int = 2  # Standalone processors
    num_retailers: int = 20
    retailers_with_delis_pct: float = 0.3  # 30% of retailers have delis

    # Lot code tracking mode for DCs
    dc_tracking_mode: LotCodeAssignmentMode = LotCodeAssignmentMode.DETERMINISTIC
    dc_calculated_method: CalculatedLotCodeMethod = CalculatedLotCodeMethod.FIFO_DATE_RANGE
    dc_date_window_days: int = 7

    # Product configuration
    cucumber_product: ProductDescription = field(default_factory=lambda: ProductDescription(
        category=ProductCategory.FRESH_CUCUMBERS,
        commodity="Cucumbers",
        variety="Persian",
        description="Fresh Persian Cucumbers",
    ))

    # Random seed for reproducibility
    random_seed: Optional[int] = None


@dataclass
class SupplyChainEdge:
    """Edge connecting two supply chain nodes."""
    source_id: UUID
    destination_id: UUID
    product_categories: list[ProductCategory]
    typical_volume_per_shipment: Quantity
    shipments_per_week: float = 3.0
    distance_miles: float = 0.0  # Calculated from source/dest coordinates


class SupplyChainNetwork:
    """
    Represents the complete supply chain network for simulation.

    Contains all nodes (farms, packers, DCs, processors, delis, retailers)
    and the edges (supply relationships) between them.
    """

    def __init__(self, config: Optional[NetworkConfig] = None):
        """
        Initialize the supply chain network.

        Args:
            config: Network configuration (uses defaults if None)
        """
        self.config = config or NetworkConfig()

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        # Node storage by type
        self.farms: dict[UUID, Farm] = {}
        self.packers: dict[UUID, Packer] = {}
        self.distribution_centers: dict[UUID, DistributionCenter] = {}
        self.processors: dict[UUID, Processor] = {}
        self.delis: dict[UUID, Deli] = {}
        self.retailers: dict[UUID, Retailer] = {}

        # All nodes indexed by ID
        self.nodes: dict[UUID, SupplyChainNode] = {}

        # Supply chain edges
        self.edges: list[SupplyChainEdge] = []

        # Adjacency lists
        self.suppliers: dict[UUID, list[UUID]] = {}  # node -> its suppliers
        self.customers: dict[UUID, list[UUID]] = {}  # node -> its customers

        # Lot tracker
        self.lot_tracker = LotTracker()

    def get_node(self, node_id: UUID) -> Optional[SupplyChainNode]:
        """Get a node by its ID."""
        return self.nodes.get(node_id)

    def get_node_name(self, node_id: UUID) -> str:
        """Get a human-readable name for a node."""
        node = self.nodes.get(node_id)
        if node is None:
            return f"Unknown ({node_id})"

        if isinstance(node, Farm):
            return node.farm_name
        elif isinstance(node, Packer):
            return node.facility_name
        elif isinstance(node, DistributionCenter):
            return node.facility_name
        elif isinstance(node, Processor):
            return node.facility_name
        elif isinstance(node, Deli):
            return node.facility_name
        elif isinstance(node, Retailer):
            return f"{node.store_name} #{node.store_number}"
        return str(node_id)[:8]

    def _calculate_node_distance(self, source_id: UUID, dest_id: UUID) -> float:
        """Calculate distance in miles between two nodes based on their coordinates."""
        source_node = self.get_node(source_id)
        dest_node = self.get_node(dest_id)

        if source_node is None or dest_node is None:
            return 100.0  # Default distance

        source_loc = source_node.location
        dest_loc = dest_node.location

        # Check if both have coordinates
        if (source_loc.latitude is None or source_loc.longitude is None or
            dest_loc.latitude is None or dest_loc.longitude is None):
            return 100.0  # Default distance if coordinates missing

        return haversine_distance(
            source_loc.latitude, source_loc.longitude,
            dest_loc.latitude, dest_loc.longitude
        )

    def add_edge(
        self,
        source_id: UUID,
        dest_id: UUID,
        product_categories: list[ProductCategory],
        volume: Quantity,
        shipments_per_week: float = 3.0
    ) -> None:
        """Add a supply chain edge between two nodes."""
        # Calculate distance between source and destination
        distance = self._calculate_node_distance(source_id, dest_id)

        edge = SupplyChainEdge(
            source_id=source_id,
            destination_id=dest_id,
            product_categories=product_categories,
            typical_volume_per_shipment=volume,
            shipments_per_week=shipments_per_week,
            distance_miles=distance
        )
        self.edges.append(edge)

        # Update adjacency lists
        if dest_id not in self.suppliers:
            self.suppliers[dest_id] = []
        self.suppliers[dest_id].append(source_id)

        if source_id not in self.customers:
            self.customers[source_id] = []
        self.customers[source_id].append(dest_id)

    def get_suppliers(self, node_id: UUID) -> list[UUID]:
        """Get supplier node IDs for a given node."""
        return self.suppliers.get(node_id, [])

    def get_customers(self, node_id: UUID) -> list[UUID]:
        """Get customer node IDs for a given node."""
        return self.customers.get(node_id, [])

    def get_retailers_and_delis(self) -> list[UUID]:
        """Get all retail endpoint node IDs (retailers and delis)."""
        endpoints = list(self.retailers.keys()) + list(self.delis.keys())
        return endpoints

    def get_farms(self) -> list[UUID]:
        """Get all farm node IDs."""
        return list(self.farms.keys())


class NetworkBuilder:
    """
    Builder for creating supply chain networks.

    Creates a realistic cucumber supply chain with farms, packers,
    distribution centers, processors, delis, and retailers.
    """

    # Sample location data for realistic networks
    # Expanded to support up to 20 farms - major US cucumber/produce growing regions
    FARM_LOCATIONS = [
        # California - major cucumber producing state
        ("Salinas", "CA"), ("Oxnard", "CA"), ("Imperial Valley", "CA"),
        ("Bakersfield", "CA"), ("Fresno", "CA"), ("Stockton", "CA"),
        ("Watsonville", "CA"), ("Gilroy", "CA"), ("Coachella", "CA"),
        ("Santa Maria", "CA"), ("Hollister", "CA"), ("Modesto", "CA"),
        # Arizona - second major producer
        ("Yuma", "AZ"), ("Nogales", "AZ"), ("Willcox", "AZ"), ("Buckeye", "AZ"),
        # Florida - East coast production
        ("Immokalee", "FL"), ("Homestead", "FL"),
        # Georgia and other southeastern states
        ("Tifton", "GA"), ("Moultrie", "GA"),
    ]

    PACKER_LOCATIONS = [
        ("Salinas", "CA"), ("Yuma", "AZ"), ("Nogales", "AZ"),
        ("Oxnard", "CA"), ("Phoenix", "AZ"),
    ]

    DC_LOCATIONS = [
        ("Phoenix", "AZ"), ("Los Angeles", "CA"), ("Denver", "CO"),
        ("Dallas", "TX"), ("Chicago", "IL"), ("Atlanta", "GA"),
        ("Portland", "OR"), ("Seattle", "WA"),
    ]

    RETAIL_CITIES = [
        ("Phoenix", "AZ"), ("Tucson", "AZ"), ("Los Angeles", "CA"),
        ("San Diego", "CA"), ("San Francisco", "CA"), ("Denver", "CO"),
        ("Las Vegas", "NV"), ("Albuquerque", "NM"), ("Dallas", "TX"),
        ("Houston", "TX"), ("Austin", "TX"), ("Chicago", "IL"),
        ("Seattle", "WA"), ("Portland", "OR"), ("Salt Lake City", "UT"),
    ]

    def __init__(self, config: Optional[NetworkConfig] = None):
        """
        Initialize the network builder.

        Args:
            config: Network configuration
        """
        self.config = config or NetworkConfig()
        self.network = SupplyChainNetwork(config)

    def _make_location(self, name: str, city: str, state: str, address_num: int = 100, company_prefix: str = "001234567") -> Location:
        """Create a location with realistic address, GLN, and coordinates.

        Args:
            name: Location/business name
            city: City name
            state: 2-letter state code
            address_num: Street address number
            company_prefix: GS1 company prefix for GLN generation

        Returns:
            Location with GLN assigned for use as Traceability Lot Code Source (TLCS)
        """
        # Look up coordinates for city
        city_key = f"{city}, {state}"
        coords = CITY_COORDINATES.get(city_key)
        latitude = coords[0] if coords else None
        longitude = coords[1] if coords else None

        return Location(
            gln=generate_gln(company_prefix),
            name=name,
            street_address=f"{address_num} Industrial Way",
            city=city,
            state=state,
            zip_code=f"{random.randint(10000, 99999)}",
            latitude=latitude,
            longitude=longitude,
        )

    def _make_contact(self, role: str) -> ContactInfo:
        """Create a contact for a facility."""
        return ContactInfo(
            name=f"{role} Manager",
            phone=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        )

    def build_farms(self) -> list[Farm]:
        """Build farm nodes."""
        farms = []
        locations = random.sample(
            self.FARM_LOCATIONS,
            min(self.config.num_farms, len(self.FARM_LOCATIONS))
        )

        for i, (city, state) in enumerate(locations):
            farm_name = f"{city} Cucumber Farm {i + 1}"
            farm = Farm(
                location=self._make_location(farm_name, city, state),
                contact=self._make_contact("Farm"),
                farm_name=farm_name,
                responsible_party=self._make_contact("Owner"),
                commodities_grown=[ProductCategory.FRESH_CUCUMBERS],
                growing_areas=[
                    GrowingArea(area_id=f"FIELD_{chr(65 + j)}", name=f"Field {chr(65 + j)}")
                    for j in range(random.randint(2, 4))
                ],
            )
            farms.append(farm)
            self.network.farms[farm.id] = farm
            self.network.nodes[farm.id] = farm

        return farms

    def build_packers(self) -> list[Packer]:
        """Build packer nodes."""
        packers = []
        locations = random.sample(
            self.PACKER_LOCATIONS,
            min(self.config.num_packers, len(self.PACKER_LOCATIONS))
        )

        for i, (city, state) in enumerate(locations):
            facility_name = f"{city} Packing Co {i + 1}"
            packer = Packer(
                location=self._make_location(facility_name, city, state),
                contact=self._make_contact("Packing"),
                facility_name=facility_name,
                responsible_party=self._make_contact("Director"),
                maintains_source_tlc=True,  # Pass through farm TLCs
            )
            packers.append(packer)
            self.network.packers[packer.id] = packer
            self.network.nodes[packer.id] = packer

        return packers

    def build_distribution_centers(self) -> list[DistributionCenter]:
        """Build distribution center nodes with configured tracking mode."""
        dcs = []
        locations = random.sample(
            self.DC_LOCATIONS,
            min(self.config.num_distribution_centers, len(self.DC_LOCATIONS))
        )

        for i, (city, state) in enumerate(locations):
            facility_name = f"{city} Distribution Center"
            dc = DistributionCenter(
                location=self._make_location(facility_name, city, state),
                contact=self._make_contact("DC"),
                facility_name=facility_name,
                responsible_party=self._make_contact("Operations"),
                assignment_mode=self.config.dc_tracking_mode,
                calculated_method=self.config.dc_calculated_method
                    if self.config.dc_tracking_mode == LotCodeAssignmentMode.CALCULATED
                    else None,
                date_window_days=self.config.dc_date_window_days,
            )
            dcs.append(dc)
            self.network.distribution_centers[dc.id] = dc
            self.network.nodes[dc.id] = dc

            # Set mode in lot tracker
            mode = (TrackingMode.PROBABILISTIC
                    if self.config.dc_tracking_mode == LotCodeAssignmentMode.CALCULATED
                    else TrackingMode.DETERMINISTIC)
            self.network.lot_tracker.set_node_mode(dc.id, mode)

        return dcs

    def build_processors(self) -> list[Processor]:
        """Build standalone processor nodes (e.g., salad manufacturers)."""
        processors = []

        for i in range(self.config.num_processors):
            city, state = random.choice(self.DC_LOCATIONS)
            facility_name = f"Fresh Salads Inc - {city}"
            processor = Processor(
                location=self._make_location(facility_name, city, state),
                contact=self._make_contact("Processing"),
                facility_name=facility_name,
                responsible_party=self._make_contact("QA Manager"),
                lot_code_prefix="SAL",
            )
            processors.append(processor)
            self.network.processors[processor.id] = processor
            self.network.nodes[processor.id] = processor

        return processors

    def build_retailers(self) -> tuple[list[Retailer], list[Deli]]:
        """Build retailer nodes, some with in-store delis."""
        retailers = []
        delis = []

        cities = random.choices(
            self.RETAIL_CITIES,
            k=self.config.num_retailers
        )

        for i, (city, state) in enumerate(cities):
            store_name = f"FreshMart"
            store_number = f"{random.randint(100, 999)}"

            retailer = Retailer(
                location=self._make_location(f"{store_name} #{store_number}", city, state),
                contact=self._make_contact("Store"),
                store_name=store_name,
                store_number=store_number,
                responsible_party=self._make_contact("Store Manager"),
                has_deli=False,
            )

            # Some retailers have delis
            if random.random() < self.config.retailers_with_delis_pct:
                deli = Deli(
                    location=retailer.location,
                    contact=retailer.contact,
                    facility_name=f"{store_name} #{store_number} Deli",
                    responsible_party=retailer.responsible_party,
                    parent_retailer_id=retailer.id,
                    lot_code_prefix="DELI",
                )
                retailer.has_deli = True
                retailer.deli_id = deli.id

                delis.append(deli)
                self.network.delis[deli.id] = deli
                self.network.nodes[deli.id] = deli

            retailers.append(retailer)
            self.network.retailers[retailer.id] = retailer
            self.network.nodes[retailer.id] = retailer

        return retailers, delis

    def build_edges(self) -> None:
        """Build supply chain edges connecting nodes."""
        farms = list(self.network.farms.values())
        packers = list(self.network.packers.values())
        dcs = list(self.network.distribution_centers.values())
        processors = list(self.network.processors.values())
        retailers = list(self.network.retailers.values())
        delis = list(self.network.delis.values())

        # Farms -> Packers (each farm supplies 1-2 packers)
        for farm in farms:
            num_packers = min(random.randint(1, 2), len(packers))
            selected_packers = random.sample(packers, num_packers)
            for packer in selected_packers:
                self.network.add_edge(
                    farm.id, packer.id,
                    [ProductCategory.FRESH_CUCUMBERS],
                    Quantity(value=random.randint(5000, 15000), unit=UnitOfMeasure.POUNDS),
                    shipments_per_week=random.uniform(2, 5)
                )

        # Packers -> Processors (for cucumbers going to salad production)
        # Processors transform fresh cucumbers into salads
        if processors:
            for processor in processors:
                num_packer_suppliers = min(random.randint(1, 2), len(packers))
                selected_packers = random.sample(packers, num_packer_suppliers)
                for packer in selected_packers:
                    self.network.add_edge(
                        packer.id, processor.id,
                        [ProductCategory.FRESH_CUCUMBERS],
                        Quantity(value=random.randint(500, 2000), unit=UnitOfMeasure.POUNDS),
                        shipments_per_week=random.uniform(3, 5)
                    )

        # Packers -> DCs (for fresh cucumbers going direct to distribution)
        for packer in packers:
            num_dcs = min(random.randint(2, 4), len(dcs))
            selected_dcs = random.sample(dcs, num_dcs)
            for dc in selected_dcs:
                self.network.add_edge(
                    packer.id, dc.id,
                    [ProductCategory.FRESH_CUCUMBERS],
                    Quantity(value=random.randint(2000, 8000), unit=UnitOfMeasure.POUNDS),
                    shipments_per_week=random.uniform(3, 7)
                )

        # Processors -> DCs (processed salads go to distribution)
        if processors:
            for processor in processors:
                num_dcs = min(random.randint(1, 3), len(dcs))
                selected_dcs = random.sample(dcs, num_dcs)
                for dc in selected_dcs:
                    self.network.add_edge(
                        processor.id, dc.id,
                        [ProductCategory.CUCUMBER_SALAD],
                        Quantity(value=random.randint(300, 1000), unit=UnitOfMeasure.POUNDS),
                        shipments_per_week=random.uniform(3, 5)
                    )

        # DCs -> Retailers (fresh cucumbers)
        retailers_per_dc = max(1, len(retailers) // len(dcs))
        for i, dc in enumerate(dcs):
            start_idx = i * retailers_per_dc
            end_idx = start_idx + retailers_per_dc + random.randint(0, 3)
            dc_retailers = retailers[start_idx:min(end_idx, len(retailers))]

            for retailer in dc_retailers:
                self.network.add_edge(
                    dc.id, retailer.id,
                    [ProductCategory.FRESH_CUCUMBERS],
                    Quantity(value=random.randint(100, 500), unit=UnitOfMeasure.POUNDS),
                    shipments_per_week=random.uniform(2, 4)
                )

        # DCs -> Delis (processed salads from processors via DC)
        for deli in delis:
            # Find DC(s) to supply this deli
            num_dc_suppliers = min(random.randint(1, 2), len(dcs))
            selected_dcs = random.sample(dcs, num_dc_suppliers)
            for dc in selected_dcs:
                self.network.add_edge(
                    dc.id, deli.id,
                    [ProductCategory.CUCUMBER_SALAD],
                    Quantity(value=random.randint(20, 100), unit=UnitOfMeasure.POUNDS),
                    shipments_per_week=random.uniform(2, 3)
                )

    def build(self) -> SupplyChainNetwork:
        """
        Build the complete supply chain network.

        Returns:
            Fully constructed SupplyChainNetwork
        """
        self.build_farms()
        self.build_packers()
        self.build_distribution_centers()
        self.build_processors()
        self.build_retailers()
        self.build_edges()

        return self.network

    def get_network_summary(self) -> dict:
        """Get a summary of the built network."""
        return {
            "num_farms": len(self.network.farms),
            "num_packers": len(self.network.packers),
            "num_distribution_centers": len(self.network.distribution_centers),
            "num_processors": len(self.network.processors),
            "num_retailers": len(self.network.retailers),
            "num_delis": len(self.network.delis),
            "num_edges": len(self.network.edges),
            "dc_tracking_mode": self.config.dc_tracking_mode.value,
            "total_nodes": len(self.network.nodes),
        }
