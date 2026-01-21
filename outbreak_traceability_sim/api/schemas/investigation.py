"""Schemas for investigation endpoints."""

from typing import Optional, List
from pydantic import BaseModel


class TracebackStepResponse(BaseModel):
    """Single step in traceback animation."""

    step_index: int
    current_node_id: str
    current_tlc: str
    probability: float
    mode: str
    path_so_far: List[str]
    branching_factor: int


class ConvergenceResultResponse(BaseModel):
    """Convergence analysis result for a farm."""

    farm_id: str
    farm_name: str
    cases_converging: int
    tlcs_converging: List[str]
    convergence_probability: float
    confidence_score: float


class InvestigationStepsResponse(BaseModel):
    """Investigation steps for animation."""

    deterministic_steps: List[TracebackStepResponse]
    probabilistic_steps: List[TracebackStepResponse]
    actual_source_farm_id: Optional[str]


class ConvergenceResponse(BaseModel):
    """Convergence analysis results."""

    results: List[ConvergenceResultResponse]
    primary_suspect: Optional[dict] = None


class EpiCurveDataPoint(BaseModel):
    """Single data point for epidemiological curve."""

    date: str
    count: int


class CaseSummary(BaseModel):
    """Summary statistics for illness cases."""

    total_cases: int
    hospitalized_cases: int
    hospitalization_rate: float
    interviewed_cases: int
    interview_rate: float
    cases_with_exposure_location: int
    exposure_location_rate: float
    earliest_onset: Optional[str]
    latest_onset: Optional[str]
    outbreak_duration_days: int


class NodeCaseCount(BaseModel):
    """Case count for a specific node."""

    node_id: str
    node_name: str
    node_type: str
    case_count: int
    hospitalized_count: int


class CaseDataResponse(BaseModel):
    """Complete case data response."""

    epi_curve: List[EpiCurveDataPoint]
    summary: CaseSummary
    node_case_counts: List[NodeCaseCount]
