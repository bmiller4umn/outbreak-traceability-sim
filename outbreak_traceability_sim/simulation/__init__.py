"""
Outbreak simulation engine for FSMA 204 traceability comparison.

This package provides a complete simulation pipeline for comparing
FDA FSMA 204 food traceability effectiveness under two scenarios:
1. Full compliance with deterministic lot code tracking
2. Calculated lot codes at distribution centers

Components:
- contamination: Seeds contamination events at farms
- network: Builds supply chain network structures
- flow: Simulates product flow and lot tracking
- exposure: Generates consumer exposures and illness cases
- investigation: Performs traceback and convergence analysis
- runner: Orchestrates complete simulation runs
"""

from .contamination import (
    ContaminationEvent,
    ContaminationSeeder,
)

from .network import (
    NetworkConfig,
    NetworkBuilder,
    SupplyChainNetwork,
    SupplyChainEdge,
)

from .flow import (
    Shipment,
    ProductionBatch,
    ProductFlowSimulator,
)

from .exposure import (
    Consumer,
    Exposure,
    ExposureType,
    IllnessCase,
    CaseStatus,
    ExposureGenerator,
    CaseGenerator,
)

from .investigation import (
    TracebackNode,
    TracebackPath,
    ConvergenceResult,
    InvestigationResult,
    InvestigationEngine,
    compare_investigation_modes,
)

from .runner import (
    SimulationConfig,
    SimulationMetrics,
    ComparisonResult,
    OutbreakSimulator,
    run_outbreak_simulation,
)

__all__ = [
    # Contamination
    "ContaminationEvent",
    "ContaminationSeeder",

    # Network
    "NetworkConfig",
    "NetworkBuilder",
    "SupplyChainNetwork",
    "SupplyChainEdge",

    # Flow
    "Shipment",
    "ProductionBatch",
    "ProductFlowSimulator",

    # Exposure
    "Consumer",
    "Exposure",
    "ExposureType",
    "IllnessCase",
    "CaseStatus",
    "ExposureGenerator",
    "CaseGenerator",

    # Investigation
    "TracebackNode",
    "TracebackPath",
    "ConvergenceResult",
    "InvestigationResult",
    "InvestigationEngine",
    "compare_investigation_modes",

    # Runner
    "SimulationConfig",
    "SimulationMetrics",
    "ComparisonResult",
    "OutbreakSimulator",
    "run_outbreak_simulation",
]
