"""Schemas for Monte Carlo simulation endpoints."""

from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator

from ..config import config


class MonteCarloConfigRequest(BaseModel):
    """Request schema for starting a Monte Carlo simulation."""
    # Network configuration
    num_farms: int = Field(default=5, ge=1, le=20)
    num_packers: int = Field(default=2, ge=1, le=10)
    num_distribution_centers: int = Field(default=3, ge=1, le=10)
    num_retailers: int = Field(default=20, ge=5, le=100)
    retailers_with_delis_pct: float = Field(default=0.3, ge=0, le=1)

    # Contamination
    contamination_rate: float = Field(default=1.0, ge=0, le=1)
    contamination_duration_days: int = Field(default=7, ge=1, le=14)
    pathogen: str = Field(default="Salmonella")

    # Strategy
    inventory_strategy: Literal["FIFO", "LIFO", "ALL_IN_WINDOW", "INVENTORY_WEIGHTED"] = "FIFO"
    date_window_days: int = Field(default=7, ge=1, le=30)
    simulation_days: int = Field(default=90, ge=7, le=180)

    # Investigation
    interview_success_rate: float = Field(default=0.7, ge=0.1, le=1.0)
    record_collection_window_days: int = Field(default=14, ge=7, le=30)

    # Monte Carlo specific
    num_iterations: int = Field(default=1000, ge=10)
    base_random_seed: Optional[int] = Field(default=None)

    @field_validator("num_iterations")
    @classmethod
    def validate_num_iterations(cls, v: int) -> int:
        """Validate num_iterations against configured maximum."""
        max_iterations = config.max_monte_carlo_iterations
        if v > max_iterations:
            raise ValueError(f"num_iterations cannot exceed {max_iterations}")
        return v


class MonteCarloStartResponse(BaseModel):
    """Response when starting a Monte Carlo simulation."""
    monte_carlo_id: str
    status: str = "started"
    message: str = "Monte Carlo simulation started"
    num_iterations: int


class MonteCarloStatusResponse(BaseModel):
    """Response for Monte Carlo status polling."""
    monte_carlo_id: str
    status: Literal["pending", "running", "completed", "cancelled", "error"]
    iterations_completed: int
    iterations_total: int
    progress: float = Field(ge=0, le=1)
    estimated_time_remaining_seconds: Optional[float] = None
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class HistogramBin(BaseModel):
    """Single histogram bin."""
    bin_start: float
    bin_end: float
    count: int


class MetricStatisticsResponse(BaseModel):
    """Statistical summary for a metric."""
    mean: float
    std: float
    min: float
    max: float
    median: float
    p5: float
    p25: float
    p75: float
    p95: float
    histogram: List[HistogramBin]


class IdentificationStatisticsResponse(BaseModel):
    """Identification accuracy statistics with three-state outcomes."""
    yes_rate: float  # Rate of correct identifications with clear margin
    no_rate: float  # Rate of incorrect identifications with clear margin
    inconclusive_rate: float  # Rate of inconclusive results (top farms too close)
    yes_count: int
    no_count: int
    inconclusive_count: int
    total_count: int
    rank_distribution: Dict[int, int]
    mean_rank: float
    median_rank: float


class MonteCarloResultResponse(BaseModel):
    """Full Monte Carlo result response."""
    monte_carlo_id: str
    config: dict
    iterations_completed: int
    iterations_failed: int

    # Expansion metrics
    farm_scope_expansion: MetricStatisticsResponse
    tlc_scope_expansion: MetricStatisticsResponse
    tlcs_location_expansion: MetricStatisticsResponse
    path_expansion: MetricStatisticsResponse

    # Absolute scope metrics
    det_farms_in_scope: MetricStatisticsResponse
    det_tlcs_in_scope: MetricStatisticsResponse
    det_tlcs_locations: MetricStatisticsResponse  # TLCS - unique GLNs where TLCs were assigned
    prob_farms_in_scope: MetricStatisticsResponse
    prob_tlcs_in_scope: MetricStatisticsResponse
    prob_tlcs_locations: MetricStatisticsResponse  # TLCS - unique GLNs where TLCs were assigned

    # Case metrics
    total_cases: MetricStatisticsResponse

    # Identification accuracy
    deterministic_identification: IdentificationStatisticsResponse
    probabilistic_identification: IdentificationStatisticsResponse

    # Investigation timing metrics
    det_investigation_days: Optional[MetricStatisticsResponse] = None
    det_investigation_work_hours: Optional[MetricStatisticsResponse] = None
    prob_investigation_days: Optional[MetricStatisticsResponse] = None
    prob_investigation_work_hours: Optional[MetricStatisticsResponse] = None
    timing_expansion: Optional[MetricStatisticsResponse] = None

    # Statistical tests
    mean_expansion_95ci: List[float]  # [lower, upper]
    identification_difference_significant: bool
    identification_pvalue: Optional[float]
