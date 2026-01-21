"""
Critical Tracking Event (CTE) models for FSMA 204 traceability simulation.

CTEs are the cornerstone of FSMA 204 traceability. Each CTE captures
specific Key Data Elements (KDEs) that must be recorded and maintained
for traceback investigations.

CTE Types per FSMA 204:
- Harvesting: Recording of initial harvest at farm
- Cooling: Recording of cooling operations at first receiver
- Initial Packing: Recording of packing operations
- Shipping: Recording of product leaving a location
- Receiving: Recording of product arriving at a location
- Transformation: Recording of product conversion (e.g., cucumber -> salad)
- Creating: Recording when new food product is created
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from .base import (
    BaseCTEModel,
    CTEType,
    ProductDescription,
    Quantity,
    ReferenceDocument,
    ReferenceDocumentType,
    ContaminationStatus,
)
from .nodes import CoolingMethod, TransformationType


class HarvestingCTE(BaseCTEModel):
    """
    Harvesting Critical Tracking Event.

    Required KDEs per FSMA 204 for harvesting:
    - Traceability Lot Code (TLC)
    - Commodity and variety
    - Quantity and UOM
    - Location of growing area
    - Harvest date
    - Reference document
    """
    event_type: CTEType = Field(default=CTEType.HARVESTING, frozen=True)

    # Harvesting-specific KDEs
    growing_area_id: str = Field(
        ...,
        description="Identifier for the specific growing area (field, greenhouse, etc.)"
    )
    harvest_date: date = Field(..., description="Date of harvest")
    harvest_crew_id: Optional[str] = Field(None, description="Harvest crew identifier")

    # For simulation tracking
    contamination_status: ContaminationStatus = Field(default=ContaminationStatus.UNKNOWN)
    contamination_source: Optional[str] = Field(
        None,
        description="Description of contamination source for simulation"
    )


class CoolingCTE(BaseCTEModel):
    """
    Cooling Critical Tracking Event.

    Required KDEs per FSMA 204 for cooling:
    - TLC of product cooled
    - Commodity and variety
    - Quantity cooled
    - Location where cooling performed
    - Date of cooling
    - Cooling method (required by some interpretations)
    - Reference document
    """
    event_type: CTEType = Field(default=CTEType.COOLING, frozen=True)

    # Cooling-specific KDEs
    cooling_date: date = Field(..., description="Date cooling was completed")
    cooling_method: CoolingMethod
    target_temperature_f: float = Field(
        ...,
        description="Target temperature in Fahrenheit"
    )
    actual_temperature_f: Optional[float] = Field(
        None,
        description="Actual achieved temperature in Fahrenheit"
    )

    # Link to source
    source_tlc: str = Field(..., description="TLC of product before cooling")


class InitialPackingCTE(BaseCTEModel):
    """
    Initial Packing Critical Tracking Event.

    Required KDEs per FSMA 204 for initial packing:
    - TLC assigned to packed product
    - Commodity and variety
    - Quantity packed
    - Location of packing
    - Pack date
    - Reference document
    """
    event_type: CTEType = Field(default=CTEType.INITIAL_PACKING, frozen=True)

    # Packing-specific KDEs
    pack_date: date = Field(..., description="Date product was packed")
    pack_line_id: Optional[str] = Field(None, description="Packing line identifier")

    # Link to source
    source_tlcs: list[str] = Field(
        ...,
        description="TLCs of input product(s) used in packing"
    )

    # Output package details
    pack_size: Quantity = Field(..., description="Size of each packed unit")
    pack_count: int = Field(..., gt=0, description="Number of units packed")


class ShippingCTE(BaseCTEModel):
    """
    Shipping Critical Tracking Event.

    Required KDEs per FSMA 204 for shipping:
    - TLC of product shipped
    - Commodity and variety
    - Quantity shipped
    - Location product shipped FROM
    - Date shipped
    - Location product shipped TO
    - Reference document (e.g., BOL, ASN)
    """
    event_type: CTEType = Field(default=CTEType.SHIPPING, frozen=True)

    # Shipping-specific KDEs
    ship_date: datetime = Field(..., description="Date and time of shipment")
    ship_from_location_id: UUID = Field(..., description="Location product shipped from")
    ship_to_location_id: UUID = Field(..., description="Destination location")

    # Multiple TLCs may be shipped together
    tlcs_shipped: list[str] = Field(
        ...,
        description="List of TLCs in this shipment"
    )

    # For calculated lot code scenarios - probability assignments
    tlc_probabilities: Optional[dict[str, float]] = Field(
        None,
        description="TLC to probability mapping for calculated lot code scenarios"
    )

    # Carrier information
    carrier_name: Optional[str] = None
    carrier_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    seal_number: Optional[str] = None


class ReceivingCTE(BaseCTEModel):
    """
    Receiving Critical Tracking Event.

    Required KDEs per FSMA 204 for receiving:
    - TLC of product received
    - Commodity and variety
    - Quantity received
    - Location product received AT
    - Date received
    - Location product received FROM (immediate previous source)
    - Reference document
    """
    event_type: CTEType = Field(default=CTEType.RECEIVING, frozen=True)

    # Receiving-specific KDEs
    receive_date: datetime = Field(..., description="Date and time of receipt")
    received_from_location_id: UUID = Field(
        ...,
        description="Location product was received from"
    )

    # Multiple TLCs may be received together
    tlcs_received: list[str] = Field(
        ...,
        description="List of TLCs received"
    )

    # For calculated lot code scenarios
    tlc_probabilities: Optional[dict[str, float]] = Field(
        None,
        description="TLC to probability mapping for calculated lot code scenarios"
    )

    # Quality check at receiving
    temperature_check_f: Optional[float] = Field(
        None,
        description="Temperature at receipt in Fahrenheit"
    )
    condition_notes: Optional[str] = Field(
        None,
        description="Notes on product condition at receipt"
    )


class TransformationCTE(BaseCTEModel):
    """
    Transformation Critical Tracking Event.

    Required KDEs per FSMA 204 for transformation:
    - New TLC assigned to transformed product
    - New product commodity/description
    - Quantity of new product
    - All TLCs of input products used
    - Location where transformation performed
    - Date of transformation
    - Reference document

    This is critical for the cucumber salad scenario where whole
    cucumbers are transformed into deli salad.
    """
    event_type: CTEType = Field(default=CTEType.TRANSFORMATION, frozen=True)

    # Transformation-specific KDEs
    transformation_date: datetime = Field(
        ...,
        description="Date and time transformation was performed"
    )
    transformation_type: TransformationType

    # Input tracking - this is the key linkage
    input_products: list["TransformationInput"] = Field(
        ...,
        description="All input products with their TLCs"
    )

    # For calculated lot code scenarios - input TLCs may be probabilistic
    input_tlc_probabilities: Optional[dict[str, float]] = Field(
        None,
        description="Input TLC to probability mapping for calculated scenarios"
    )

    # Output product gets new TLC (stored in base tlc field)
    recipe_id: Optional[str] = Field(None, description="Recipe used for transformation")
    batch_id: Optional[str] = Field(None, description="Production batch identifier")


class TransformationInput(BaseModel):
    """Input product record for a transformation event."""
    product: ProductDescription
    quantity: Quantity
    tlcs: list[str] = Field(..., description="TLCs of input product used")
    tlc_probabilities: Optional[dict[str, float]] = Field(
        None,
        description="Probability mapping for calculated lot code scenarios"
    )


class CreatingCTE(BaseCTEModel):
    """
    Creating Critical Tracking Event.

    Per FSMA 204, Creating applies when a new food is made that
    wasn't subject to another CTE at the same location. This is
    less common in produce supply chains but included for completeness.
    """
    event_type: CTEType = Field(default=CTEType.CREATING, frozen=True)

    creation_date: datetime
    creation_process: str = Field(
        ...,
        description="Description of how product was created"
    )


class CTEChain(BaseModel):
    """
    Chain of CTEs tracking a product through the supply chain.

    This is used for traceback analysis to follow a product from
    retail back to farm, or traceforward from farm to retail.
    """
    id: UUID = Field(default_factory=uuid4)
    root_tlc: str = Field(..., description="Original TLC at chain start")
    events: list[BaseCTEModel] = Field(default_factory=list)

    # For traceback analysis
    contamination_confirmed: bool = False
    contamination_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probability this chain contains contaminated product"
    )

    def add_event(self, event: BaseCTEModel) -> None:
        """Add a CTE to this chain."""
        self.events.append(event)

    def get_events_by_type(self, event_type: CTEType) -> list[BaseCTEModel]:
        """Get all events of a specific type in this chain."""
        return [e for e in self.events if e.event_type == event_type]

    @property
    def current_tlcs(self) -> set[str]:
        """Get all TLCs currently associated with this chain."""
        tlcs = {self.root_tlc}

        for event in self.events:
            if isinstance(event, TransformationCTE):
                tlcs.add(event.tlc)  # Output TLC
            elif isinstance(event, ShippingCTE):
                tlcs.update(event.tlcs_shipped)
            elif isinstance(event, ReceivingCTE):
                tlcs.update(event.tlcs_received)

        return tlcs

    @property
    def timeline(self) -> list[tuple[datetime, CTEType, str]]:
        """Get chronological timeline of events."""
        return sorted(
            [(e.event_time, e.event_type, e.tlc) for e in self.events],
            key=lambda x: x[0]
        )


class TracebackResult(BaseModel):
    """
    Result of a traceback investigation.

    Contains all identified CTEs and TLCs that could be linked to
    a contamination event, along with scope metrics comparing
    deterministic vs. calculated lot code scenarios.
    """
    id: UUID = Field(default_factory=uuid4)
    investigation_date: datetime = Field(default_factory=datetime.now)

    # Starting point
    reported_illness_location_id: UUID
    reported_illness_tlc: Optional[str] = None
    reported_illness_date: date

    # Results
    identified_chains: list[CTEChain] = Field(default_factory=list)
    suspect_farms: list[UUID] = Field(default_factory=list)
    suspect_tlcs: list[str] = Field(default_factory=list)

    # Scope metrics - key for simulation comparison
    farms_in_scope: int = Field(default=0, description="Number of farms in traceback scope")
    tlcs_in_scope: int = Field(default=0, description="Number of TLCs in traceback scope")
    total_product_volume: Optional[Quantity] = None

    # Comparison metrics
    is_calculated_scenario: bool = Field(
        default=False,
        description="True if this traceback used calculated lot codes"
    )
    scope_expansion_factor: Optional[float] = Field(
        None,
        description="How much larger scope is vs. deterministic baseline"
    )

    @property
    def scope_summary(self) -> str:
        """Human-readable summary of traceback scope."""
        scenario = "calculated" if self.is_calculated_scenario else "deterministic"
        return (
            f"Traceback ({scenario}): {self.farms_in_scope} farms, "
            f"{self.tlcs_in_scope} TLCs in scope"
        )
