"""
Supply chain node models for FSMA 204 traceability simulation.

Each node type has specific Key Data Elements (KDEs) and Critical Tracking
Event (CTE) responsibilities per FDA FSMA 204 requirements.

Node Types:
- Farm: Origin point, responsible for Harvesting CTE
- Packer: First receiver, responsible for Cooling and Initial Packing CTEs
- DistributionCenter: Hub for Receiving/Shipping CTEs - key for lot code scenarios
- Processor: Transformation CTE handler (e.g., deli salad production)
- Retailer: Endpoint, responsible for Receiving CTE
"""

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .base import (
    BaseNodeModel,
    ContactInfo,
    Location,
    NodeType,
    ProductCategory,
    ProductDescription,
    Quantity,
    UnitOfMeasure,
)


class GrowingArea(BaseModel):
    """
    Growing area identification for farm traceability.

    Per FSMA 204, farms must identify growing areas for FTL commodities
    to enable traceback to specific fields or greenhouses.
    """
    area_id: str = Field(..., description="Internal growing area identifier")
    name: str
    coordinates: Optional[tuple[float, float]] = Field(
        None, description="GPS coordinates (lat, lon)"
    )
    acreage: Optional[float] = None
    growing_method: str = Field(
        default="field",
        description="Growing method: field, greenhouse, hydroponic, etc."
    )


class HarvestRecord(BaseModel):
    """Record of a harvest event for lot code generation."""
    harvest_date: date
    growing_area_id: str
    crew_id: Optional[str] = None
    quantity: Quantity
    tlc: str = Field(..., description="Traceability Lot Code assigned at harvest")


class Farm(BaseNodeModel):
    """
    Farm supply chain node.

    Farms are the origin point for food traceability. Per FSMA 204,
    farms growing FTL commodities must:
    - Assign Traceability Lot Codes at harvest
    - Record growing area information
    - Maintain harvest records with dates and quantities
    """
    node_type: NodeType = Field(default=NodeType.FARM, frozen=True)
    growing_areas: list[GrowingArea] = Field(default_factory=list)
    commodities_grown: list[ProductCategory] = Field(default_factory=list)
    harvest_records: list[HarvestRecord] = Field(default_factory=list)

    # Farm-specific KDEs per FSMA 204
    farm_name: str
    responsible_party: ContactInfo

    def generate_lot_code(self, harvest_date: date, growing_area_id: str) -> str:
        """
        Generate a deterministic TLC based on harvest date and growing area.

        Format: FARM_ID-YYYYMMDD-AREA_ID
        """
        date_str = harvest_date.strftime("%Y%m%d")
        farm_prefix = str(self.id)[:8].upper()
        return f"{farm_prefix}-{date_str}-{growing_area_id}"


class CoolingMethod(str, Enum):
    """Cooling methods used at packing facilities."""
    FORCED_AIR = "forced_air"
    HYDROCOOLING = "hydrocooling"
    VACUUM = "vacuum"
    ROOM_COOLING = "room_cooling"
    ICE = "ice"


class PackingConfiguration(BaseModel):
    """Configuration for a packing line/operation."""
    line_id: str
    product_categories: list[ProductCategory]
    cooling_method: CoolingMethod
    typical_pack_size: Quantity


class Packer(BaseNodeModel):
    """
    Packer/First Receiver supply chain node.

    Packers are the first receivers of harvested produce and are responsible
    for cooling and initial packing CTEs. Per FSMA 204, packers must:
    - Record receipt of product with source TLC
    - Perform and record cooling operations
    - Assign new TLCs for packed product (or maintain source TLCs)
    - Create shipping records with TLC linkage
    """
    node_type: NodeType = Field(default=NodeType.PACKER, frozen=True)
    packing_configurations: list[PackingConfiguration] = Field(default_factory=list)

    # Packer-specific KDEs
    facility_name: str
    responsible_party: ContactInfo
    fda_registration_number: Optional[str] = None

    # Lot code assignment strategy
    maintains_source_tlc: bool = Field(
        default=True,
        description="If True, maintains farm TLC through packing. If False, assigns new TLC."
    )

    def generate_pack_lot_code(
        self,
        pack_date: date,
        source_tlc: str,
        line_id: str
    ) -> str:
        """
        Generate a TLC for packed product.

        If maintains_source_tlc is True, returns source TLC.
        Otherwise generates new TLC linking back to source.
        """
        if self.maintains_source_tlc:
            return source_tlc

        date_str = pack_date.strftime("%Y%m%d")
        packer_prefix = str(self.id)[:8].upper()
        return f"{packer_prefix}-{date_str}-{line_id}-{source_tlc[-8:]}"


class LotCodeAssignmentMode(str, Enum):
    """
    Lot code assignment modes for distribution centers.

    This is the key differentiator for the simulation:
    - DETERMINISTIC: Full FSMA 204 compliance with exact TLC tracking
    - CALCULATED: Uses date-based or inventory-based approximations
    """
    DETERMINISTIC = "deterministic"
    CALCULATED = "calculated"


class CalculatedLotCodeMethod(str, Enum):
    """Methods for calculating/approximating lot codes when exact tracking unavailable."""
    FIFO_DATE_RANGE = "fifo_date_range"  # First-in-first-out with date window
    LIFO_DATE_RANGE = "lifo_date_range"  # Last-in-first-out with date window
    ALL_IN_WINDOW = "all_in_window"      # All lots received in date window
    INVENTORY_WEIGHTED = "inventory_weighted"  # Probability based on inventory levels


class InventoryRecord(BaseModel):
    """Inventory record for tracking product in storage."""
    tlc: str
    product: ProductDescription
    quantity_received: Quantity
    quantity_remaining: Quantity
    received_date: datetime
    source_node_id: UUID
    expiration_date: Optional[date] = None
    # When product becomes available for outbound shipping (after inspection/processing)
    available_date: Optional[datetime] = None


class DistributionCenter(BaseNodeModel):
    """
    Distribution Center supply chain node.

    Distribution centers are critical hubs where lot code tracking can
    break down. This is the primary focus of the simulation comparison:

    FULL COMPLIANCE (deterministic):
    - Each outbound shipment linked to specific inbound TLCs
    - Exact quantity tracking per TLC
    - Real-time inventory by TLC

    CALCULATED LOT CODES:
    - Outbound shipments linked to date-range of possible TLCs
    - Probabilistic assignment based on inventory assumptions
    - Results in wider traceback scope during investigations
    """
    node_type: NodeType = Field(default=NodeType.DISTRIBUTION_CENTER, frozen=True)

    # DC-specific KDEs
    facility_name: str
    responsible_party: ContactInfo
    fda_registration_number: Optional[str] = None

    # Lot code assignment configuration
    assignment_mode: LotCodeAssignmentMode = Field(
        default=LotCodeAssignmentMode.DETERMINISTIC,
        description="How this DC tracks/assigns lot codes for outbound shipments"
    )
    calculated_method: Optional[CalculatedLotCodeMethod] = Field(
        default=None,
        description="Method used when assignment_mode is CALCULATED"
    )
    date_window_days: int = Field(
        default=7,
        description="Number of days in lookback window for calculated methods"
    )

    # Inventory tracking
    inventory: list[InventoryRecord] = Field(default_factory=list)

    def get_deterministic_lots(
        self,
        product_category: ProductCategory,
        quantity_needed: Quantity,
        ship_date: datetime
    ) -> list[tuple[str, Quantity]]:
        """
        Get exact TLCs for a shipment using FIFO (deterministic/full compliance).

        Returns list of (TLC, quantity) tuples that sum to quantity_needed.
        """
        result = []
        remaining = quantity_needed.value

        # Sort by received date (FIFO)
        eligible = sorted(
            [inv for inv in self.inventory
             if inv.product.category == product_category
             and inv.quantity_remaining.value > 0],
            key=lambda x: x.received_date
        )

        for inv in eligible:
            if remaining <= 0:
                break

            take = min(remaining, inv.quantity_remaining.value)
            result.append((inv.tlc, Quantity(value=take, unit=quantity_needed.unit)))
            remaining -= take

        return result

    def get_calculated_lots(
        self,
        product_category: ProductCategory,
        quantity_needed: Quantity,
        ship_date: datetime
    ) -> list[tuple[str, float]]:
        """
        Get candidate TLCs with probabilities for a shipment (calculated mode).

        Returns list of (TLC, probability) tuples representing possible
        source lots. Probabilities may sum to > 1.0 as multiple lots
        could contribute to the shipment.
        """
        window_start = ship_date - timedelta(days=self.date_window_days)

        # Get all lots received in window
        eligible = [
            inv for inv in self.inventory
            if inv.product.category == product_category
            and window_start <= inv.received_date <= ship_date
        ]

        if self.calculated_method == CalculatedLotCodeMethod.ALL_IN_WINDOW:
            # All lots in window are equally likely
            return [(inv.tlc, 1.0) for inv in eligible]

        elif self.calculated_method == CalculatedLotCodeMethod.FIFO_DATE_RANGE:
            # Weight by age (older = more likely shipped first)
            total_age = sum(
                (ship_date - inv.received_date).total_seconds()
                for inv in eligible
            )
            if total_age == 0:
                return [(inv.tlc, 1.0 / len(eligible)) for inv in eligible]

            return [
                (inv.tlc, (ship_date - inv.received_date).total_seconds() / total_age)
                for inv in eligible
            ]

        elif self.calculated_method == CalculatedLotCodeMethod.INVENTORY_WEIGHTED:
            # Weight by inventory quantity
            total_qty = sum(inv.quantity_remaining.value for inv in eligible)
            if total_qty == 0:
                return [(inv.tlc, 1.0 / len(eligible)) for inv in eligible]

            return [
                (inv.tlc, inv.quantity_remaining.value / total_qty)
                for inv in eligible
            ]

        elif self.calculated_method == CalculatedLotCodeMethod.LIFO_DATE_RANGE:
            # Weight by inverse age (newer = more likely shipped first)
            # Use days since receipt, with newer items having higher weight
            now_seconds = ship_date.timestamp()
            ages = [(now_seconds - inv.received_date.timestamp()) for inv in eligible]
            max_age = max(ages) if ages else 1

            # Invert: newer items (smaller age) get higher weight
            inverse_ages = [(max_age - age + 1) for age in ages]
            total_inverse = sum(inverse_ages)

            if total_inverse == 0:
                return [(inv.tlc, 1.0 / len(eligible)) for inv in eligible]

            return [
                (inv.tlc, inverse_age / total_inverse)
                for inv, inverse_age in zip(eligible, inverse_ages)
            ]

        # Default: all equally likely
        return [(inv.tlc, 1.0) for inv in eligible]


class TransformationType(str, Enum):
    """Types of food transformation operations."""
    SLICING = "slicing"
    DICING = "dicing"
    MIXING = "mixing"
    COOKING = "cooking"
    ASSEMBLING = "assembling"


class Recipe(BaseModel):
    """Recipe for transformed food products."""
    recipe_id: str
    output_product: ProductDescription
    output_quantity: Quantity
    ingredients: list[tuple[ProductDescription, Quantity]]
    transformation_type: TransformationType


class Processor(BaseNodeModel):
    """
    Processor supply chain node (includes deli operations).

    Processors transform input products into new products, creating
    transformation CTEs. Per FSMA 204, processors must:
    - Record all input TLCs used in transformation
    - Assign new TLC to output product
    - Maintain linkage between input and output TLCs
    - Record transformation date/time and quantity

    For the cucumber outbreak scenario, this represents the deli
    making cucumber salad from whole cucumbers.
    """
    node_type: NodeType = Field(default=NodeType.PROCESSOR, frozen=True)

    # Processor-specific KDEs
    facility_name: str
    responsible_party: ContactInfo
    fda_registration_number: Optional[str] = None

    # Transformation capabilities
    recipes: list[Recipe] = Field(default_factory=list)

    # Lot code generation for transformed products
    lot_code_prefix: str = Field(
        default="TRN",
        description="Prefix for transformed product lot codes"
    )

    def generate_transformation_lot_code(
        self,
        transformation_date: date,
        recipe_id: str,
        input_tlcs: list[str]
    ) -> str:
        """
        Generate a TLC for transformed product that links to input TLCs.

        Format: PREFIX-YYYYMMDD-RECIPE-HASH
        Where HASH is derived from input TLCs for linkage.
        """
        date_str = transformation_date.strftime("%Y%m%d")
        # Create a hash from input TLCs
        tlc_hash = hash(tuple(sorted(input_tlcs))) % 100000
        return f"{self.lot_code_prefix}-{date_str}-{recipe_id}-{tlc_hash:05d}"


class Deli(Processor):
    """
    Deli - specialized processor within a retail location.

    Delis are processors that typically operate within retail stores,
    transforming products for immediate sale. In the cucumber outbreak
    scenario, delis receive whole cucumbers and transform them into
    deli salads.
    """
    node_type: NodeType = Field(default=NodeType.DELI, frozen=True)
    parent_retailer_id: Optional[UUID] = Field(
        None,
        description="ID of parent retailer if deli is in-store"
    )
    lot_code_prefix: str = Field(default="DELI")


class Retailer(BaseNodeModel):
    """
    Retailer supply chain node.

    Retailers are endpoints in the supply chain for direct consumer sales.
    Per FSMA 204, retailers must:
    - Maintain receiving records with TLCs
    - Be able to provide traceability information within 24 hours
    - Link products on shelf to TLCs (for FTL items)

    Note: Retailers with in-store delis may have associated Deli nodes
    for tracking transformation of products.
    """
    node_type: NodeType = Field(default=NodeType.RETAILER, frozen=True)

    # Retailer-specific KDEs
    store_name: str
    store_number: str
    responsible_party: ContactInfo

    # Associated deli if applicable
    has_deli: bool = Field(default=False)
    deli_id: Optional[UUID] = Field(None, description="Associated Deli node ID")

    # Inventory tracking
    inventory: list[InventoryRecord] = Field(default_factory=list)


# Type alias for any supply chain node
SupplyChainNode = Union[Farm, Packer, DistributionCenter, Processor, Deli, Retailer]
