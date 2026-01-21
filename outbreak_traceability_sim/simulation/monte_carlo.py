"""
Monte Carlo simulation data structures.

Dataclasses for configuration, metrics, and aggregated results.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import date


@dataclass
class MetricStatistics:
    """Statistical summary for a single metric across Monte Carlo runs."""
    mean: float
    std: float
    min: float
    max: float
    median: float
    p5: float   # 5th percentile
    p25: float  # 25th percentile
    p75: float  # 75th percentile
    p95: float  # 95th percentile
    values: List[float] = field(default_factory=list)  # Raw values for histograms


@dataclass
class IdentificationStatistics:
    """Statistics for source identification accuracy."""
    # Outcome counts
    yes_count: int = 0  # Correct source identified with clear margin
    no_count: int = 0  # Wrong source identified with clear margin
    inconclusive_count: int = 0  # Top farms too close to determine
    total_count: int = 0

    # Rates
    yes_rate: float = 0.0  # Proportion with correct identification
    no_rate: float = 0.0  # Proportion with wrong identification
    inconclusive_rate: float = 0.0  # Proportion inconclusive

    # Rank statistics
    rank_distribution: Dict[int, int] = field(default_factory=dict)  # rank -> count
    mean_rank: float = 0.0
    median_rank: float = 0.0


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation."""
    # Network configuration
    num_farms: int = 5
    num_packers: int = 2
    num_distribution_centers: int = 3
    num_retailers: int = 20
    retailers_with_delis_pct: float = 0.3

    # Contamination
    contamination_rate: float = 1.0
    contamination_duration_days: int = 7
    pathogen: str = "Salmonella"

    # Strategy
    inventory_strategy: str = "FIFO"
    date_window_days: int = 7
    simulation_days: int = 90

    # Investigation parameters
    interview_success_rate: float = 0.7
    record_collection_window_days: int = 14

    # Monte Carlo specific
    num_iterations: int = 1000
    base_random_seed: Optional[int] = None  # If set, seeds are base_seed + iteration
    parallel_workers: Optional[int] = None  # None = auto-detect


@dataclass
class IterationResult:
    """Results from a single Monte Carlo iteration."""
    iteration: int
    random_seed: Optional[int]

    # Expansion metrics
    farm_scope_expansion: float
    tlc_scope_expansion: float
    tlcs_location_expansion: float
    path_expansion: float

    # Absolute scope metrics
    det_farms_in_scope: int
    det_tlcs_in_scope: int
    det_tlcs_locations: int  # TLCS - unique GLNs where TLCs were assigned (deterministic)
    prob_farms_in_scope: int
    prob_tlcs_in_scope: int
    prob_tlcs_locations: int  # TLCS - unique GLNs where TLCs were assigned (probabilistic)

    # Identification results
    det_correctly_identified: bool
    det_source_rank: int
    prob_correctly_identified: bool
    prob_source_rank: int

    # Case metrics
    total_cases: int

    # Investigation timing metrics
    det_investigation_days: float = 0.0
    det_investigation_work_hours: float = 0.0
    prob_investigation_days: float = 0.0
    prob_investigation_work_hours: float = 0.0
    timing_expansion: float = 1.0


@dataclass
class MonteCarloAggregateResult:
    """Aggregated results from Monte Carlo simulation."""
    config: MonteCarloConfig
    num_iterations_completed: int
    num_iterations_failed: int

    # Expansion metrics
    farm_scope_expansion: MetricStatistics
    tlc_scope_expansion: MetricStatistics
    tlcs_location_expansion: MetricStatistics
    path_expansion: MetricStatistics

    # Absolute scope metrics
    det_farms_in_scope: MetricStatistics
    det_tlcs_in_scope: MetricStatistics
    det_tlcs_locations: MetricStatistics  # TLCS - unique GLNs where TLCs were assigned (deterministic)
    prob_farms_in_scope: MetricStatistics
    prob_tlcs_in_scope: MetricStatistics
    prob_tlcs_locations: MetricStatistics  # TLCS - unique GLNs where TLCs were assigned (probabilistic)

    # Case metrics
    total_cases: MetricStatistics

    # Identification accuracy
    deterministic_identification: IdentificationStatistics
    probabilistic_identification: IdentificationStatistics

    # Statistical comparison
    expansion_confidence_interval_95: tuple  # 95% CI for mean farm expansion

    # Fields with defaults must come after fields without defaults
    # Investigation timing metrics (optional)
    det_investigation_days: Optional[MetricStatistics] = None
    det_investigation_work_hours: Optional[MetricStatistics] = None
    prob_investigation_days: Optional[MetricStatistics] = None
    prob_investigation_work_hours: Optional[MetricStatistics] = None
    timing_expansion: Optional[MetricStatistics] = None
    identification_difference_pvalue: Optional[float] = None  # McNemar's test p-value
