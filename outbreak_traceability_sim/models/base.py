"""
Base data models and enums for FSMA 204 traceability simulation.

Contains fundamental types used across the supply chain simulation including
location identifiers, product descriptions, and reference document types
as defined in FDA FSMA 204 requirements.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    """Types of supply chain nodes in the food traceability network."""
    FARM = "farm"
    PACKER = "packer"
    DISTRIBUTION_CENTER = "distribution_center"
    PROCESSOR = "processor"
    DELI = "deli"
    RETAILER = "retailer"


class CTEType(str, Enum):
    """
    Critical Tracking Event types per FSMA 204.

    These are the key events that require traceability records to be
    created and maintained throughout the food supply chain.
    """
    HARVESTING = "harvesting"
    COOLING = "cooling"
    INITIAL_PACKING = "initial_packing"
    SHIPPING = "shipping"
    RECEIVING = "receiving"
    TRANSFORMATION = "transformation"
    CREATING = "creating"


class ProductCategory(str, Enum):
    """Food Traceability List (FTL) product categories relevant to this simulation."""
    FRESH_CUCUMBERS = "fresh_cucumbers"
    CUCUMBER_SALAD = "cucumber_salad"
    DELI_SALAD = "deli_salad"


class UnitOfMeasure(str, Enum):
    """Standard units of measure for food products."""
    POUNDS = "lbs"
    KILOGRAMS = "kg"
    CASES = "cases"
    EACH = "each"
    PALLETS = "pallets"
    BINS = "bins"
    CONTAINERS = "containers"


class ReferenceDocumentType(str, Enum):
    """
    Types of reference documents per FSMA 204 requirements.

    Reference documents link CTEs to business records and must be
    maintained for traceability purposes.
    """
    PURCHASE_ORDER = "purchase_order"
    BILL_OF_LADING = "bill_of_lading"
    INVOICE = "invoice"
    ADVANCE_SHIP_NOTICE = "advance_ship_notice"
    WORK_ORDER = "work_order"
    PRODUCTION_LOG = "production_log"


class ContaminationStatus(str, Enum):
    """Contamination status for outbreak simulation tracking."""
    CLEAN = "clean"
    CONTAMINATED = "contaminated"
    UNKNOWN = "unknown"


class Location(BaseModel):
    """
    Location identifier per FSMA 204 requirements.

    Includes GLN (Global Location Number) or alternative identifier,
    along with physical address information required for traceability.
    """
    gln: Optional[str] = Field(
        None,
        description="Global Location Number (13-digit GS1 identifier)",
        pattern=r"^\d{13}$"
    )
    fda_ffrn: Optional[str] = Field(
        None,
        description="FDA Food Facility Registration Number"
    )
    name: str = Field(..., description="Business/location name")
    street_address: str = Field(..., description="Street address")
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    country: str = Field(default="USA")

    # Geographic coordinates for distance-based transit time calculations
    latitude: Optional[float] = Field(
        None,
        description="Latitude in decimal degrees",
        ge=-90,
        le=90
    )
    longitude: Optional[float] = Field(
        None,
        description="Longitude in decimal degrees",
        ge=-180,
        le=180
    )

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        return v.upper()

    @property
    def identifier(self) -> str:
        """Return the primary location identifier (GLN preferred)."""
        return self.gln or self.fda_ffrn or self.name


class ProductDescription(BaseModel):
    """
    Product description per FSMA 204 traceability product requirements.

    Contains all required product identification information including
    commodity, variety, and any applicable product codes.
    """
    category: ProductCategory
    commodity: str = Field(..., description="Basic commodity name (e.g., 'Cucumbers')")
    variety: Optional[str] = Field(None, description="Product variety if applicable")
    brand: Optional[str] = Field(None, description="Brand name if applicable")
    gtin: Optional[str] = Field(
        None,
        description="Global Trade Item Number",
        pattern=r"^\d{14}$"
    )
    description: str = Field(..., description="Full product description")

    @property
    def display_name(self) -> str:
        """Human-readable product name."""
        parts = [self.commodity]
        if self.variety:
            parts.append(f"({self.variety})")
        if self.brand:
            parts.insert(0, self.brand)
        return " ".join(parts)


class Quantity(BaseModel):
    """Quantity with unit of measure for food products."""
    value: float = Field(..., ge=0)  # Allow zero for inventory depletion
    unit: UnitOfMeasure

    def __str__(self) -> str:
        return f"{self.value} {self.unit.value}"


class ReferenceDocument(BaseModel):
    """
    Reference document linking CTEs to business records.

    Per FSMA 204, reference documents must be maintained and
    available for traceback investigations.
    """
    document_type: ReferenceDocumentType
    document_number: str
    document_date: date

    @property
    def reference_string(self) -> str:
        return f"{self.document_type.value}:{self.document_number}"


class ContactInfo(BaseModel):
    """Contact information for traceability communications."""
    name: str
    phone: str = Field(..., pattern=r"^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$")
    email: Optional[str] = Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")


class DateTimeRange(BaseModel):
    """Date/time range for events that span a period."""
    start: datetime
    end: datetime

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if "start" in info.data and v < info.data["start"]:
            raise ValueError("end must be after start")
        return v


class TraceabilityLotCode(BaseModel):
    """
    Traceability Lot Code (TLC) per FSMA 204.

    The TLC is the fundamental unit of traceability - a code that
    identifies a lot of food and links all CTEs for that lot.

    The Traceability Lot Code Source (TLCS) is the GLN of the physical
    location where the TLC was assigned (at Initial Packing or Transformation CTE).
    TLCS does not change as product moves through the supply chain unless
    the product goes through a Transformation CTE.
    """
    code: str = Field(..., description="The lot code string")
    tlcs: Optional[str] = Field(
        None,
        description="Traceability Lot Code Source - GLN of location where TLC was assigned"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    created_by_node_id: UUID
    source_tlcs: list[str] = Field(
        default_factory=list,
        description="Source TLCs if this lot was created from transformation"
    )

    def __hash__(self) -> int:
        return hash(self.code)

    def __eq__(self, other) -> bool:
        if isinstance(other, TraceabilityLotCode):
            return self.code == other.code
        return False


class BaseNodeModel(BaseModel):
    """Base model for all supply chain nodes."""
    id: UUID = Field(default_factory=uuid4)
    node_type: NodeType
    location: Location
    contact: ContactInfo

    class Config:
        frozen = False


class BaseCTEModel(BaseModel):
    """Base model for all Critical Tracking Events."""
    id: UUID = Field(default_factory=uuid4)
    event_type: CTEType
    event_time: datetime
    location_id: UUID
    tlc: str = Field(..., description="Traceability Lot Code")
    product: ProductDescription
    quantity: Quantity
    reference_documents: list[ReferenceDocument] = Field(default_factory=list)

    class Config:
        frozen = False
