"""
Outbreak Traceability Simulation

A simulation tool for comparing FDA FSMA 204 food traceability effectiveness
under two scenarios:
1. Full compliance with deterministic lot code tracking
2. Calculated lot codes at distribution centers

Designed for the cucumber outbreak scenario where contaminated cucumbers
are sold both whole and as an ingredient in deli salad.

Target audience: Food traceability experts at the Partnership for Food Traceability
"""

__version__ = "0.1.0"

from .models import (
    # Base types
    NodeType,
    CTEType,
    ProductCategory,
    UnitOfMeasure,
    ReferenceDocumentType,
    ContaminationStatus,
    Location,
    ProductDescription,
    Quantity,
    ReferenceDocument,
    ContactInfo,
    TraceabilityLotCode,

    # Supply chain nodes
    Farm,
    Packer,
    DistributionCenter,
    Processor,
    Deli,
    Retailer,
    LotCodeAssignmentMode,
    CalculatedLotCodeMethod,

    # Critical Tracking Events
    HarvestingCTE,
    CoolingCTE,
    InitialPackingCTE,
    ShippingCTE,
    ReceivingCTE,
    TransformationCTE,
    CTEChain,
    TracebackResult,

    # Lot tracking
    LotCodeRecord,
    LotGraph,
    LotTracker,
    LotAssignment,
    TrackingMode,
    TracebackPath,
    TraceforwardPath,
    OutbreakScenario,
)

__all__ = [
    # Version
    "__version__",

    # Base types
    "NodeType",
    "CTEType",
    "ProductCategory",
    "UnitOfMeasure",
    "ReferenceDocumentType",
    "ContaminationStatus",
    "Location",
    "ProductDescription",
    "Quantity",
    "ReferenceDocument",
    "ContactInfo",
    "TraceabilityLotCode",

    # Supply chain nodes
    "Farm",
    "Packer",
    "DistributionCenter",
    "Processor",
    "Deli",
    "Retailer",
    "LotCodeAssignmentMode",
    "CalculatedLotCodeMethod",

    # Critical Tracking Events
    "HarvestingCTE",
    "CoolingCTE",
    "InitialPackingCTE",
    "ShippingCTE",
    "ReceivingCTE",
    "TransformationCTE",
    "CTEChain",
    "TracebackResult",

    # Lot tracking
    "LotCodeRecord",
    "LotGraph",
    "LotTracker",
    "LotAssignment",
    "TrackingMode",
    "TracebackPath",
    "TraceforwardPath",
    "OutbreakScenario",
]
