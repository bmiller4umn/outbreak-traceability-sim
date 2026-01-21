"""
Monte Carlo simulation API routes.
"""

from datetime import datetime
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..schemas.monte_carlo import (
    MonteCarloConfigRequest,
    MonteCarloStartResponse,
    MonteCarloStatusResponse,
    MonteCarloResultResponse,
    MetricStatisticsResponse,
    IdentificationStatisticsResponse,
    HistogramBin,
)
from ..services.monte_carlo_service import (
    monte_carlo_service,
    MonteCarloStatus,
)

router = APIRouter()


@router.post("/run", response_model=MonteCarloStartResponse)
async def run_monte_carlo(
    config: MonteCarloConfigRequest,
    background_tasks: BackgroundTasks,
) -> MonteCarloStartResponse:
    """Start a new Monte Carlo simulation."""
    mc_id = monte_carlo_service.create_monte_carlo(config.model_dump())
    background_tasks.add_task(monte_carlo_service.run_monte_carlo, mc_id)

    return MonteCarloStartResponse(
        monte_carlo_id=mc_id,
        status="started",
        message="Monte Carlo simulation started",
        num_iterations=config.num_iterations,
    )


@router.get("/{mc_id}/status", response_model=MonteCarloStatusResponse)
async def get_monte_carlo_status(mc_id: str) -> MonteCarloStatusResponse:
    """Get status of a Monte Carlo simulation."""
    run = monte_carlo_service.get_run(mc_id)
    if not run:
        raise HTTPException(status_code=404, detail="Monte Carlo run not found")

    progress = run.iterations_completed / run.config.num_iterations if run.config.num_iterations > 0 else 0

    # Estimate time remaining
    eta = None
    if run.iterations_completed > 0 and run.started_at:
        elapsed = (datetime.now() - run.started_at).total_seconds()
        rate = run.iterations_completed / elapsed
        remaining = run.config.num_iterations - run.iterations_completed
        if rate > 0:
            eta = remaining / rate

    return MonteCarloStatusResponse(
        monte_carlo_id=run.id,
        status=run.status.value,
        iterations_completed=run.iterations_completed,
        iterations_total=run.config.num_iterations,
        progress=progress,
        estimated_time_remaining_seconds=eta,
        message=run.error if run.status == MonteCarloStatus.ERROR else None,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


@router.post("/{mc_id}/cancel")
async def cancel_monte_carlo(mc_id: str) -> dict:
    """Cancel a running Monte Carlo simulation."""
    run = monte_carlo_service.get_run(mc_id)
    if not run:
        raise HTTPException(status_code=404, detail="Monte Carlo run not found")

    success = monte_carlo_service.cancel_run(mc_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel this run")
    return {"status": "cancelled"}


def _stats_to_response(stats) -> MetricStatisticsResponse:
    """Convert MetricStatistics to response model."""
    # Generate histogram
    if stats.values:
        hist, bin_edges = np.histogram(stats.values, bins=20)
        histogram = [
            HistogramBin(
                bin_start=float(bin_edges[i]),
                bin_end=float(bin_edges[i + 1]),
                count=int(hist[i])
            )
            for i in range(len(hist))
        ]
    else:
        histogram = []

    return MetricStatisticsResponse(
        mean=stats.mean,
        std=stats.std,
        min=stats.min,
        max=stats.max,
        median=stats.median,
        p5=stats.p5,
        p25=stats.p25,
        p75=stats.p75,
        p95=stats.p95,
        histogram=histogram,
    )


def _id_stats_to_response(stats) -> IdentificationStatisticsResponse:
    """Convert IdentificationStatistics to response model."""
    return IdentificationStatisticsResponse(
        yes_rate=stats.yes_rate,
        no_rate=stats.no_rate,
        inconclusive_rate=stats.inconclusive_rate,
        yes_count=stats.yes_count,
        no_count=stats.no_count,
        inconclusive_count=stats.inconclusive_count,
        total_count=stats.total_count,
        rank_distribution=stats.rank_distribution,
        mean_rank=stats.mean_rank,
        median_rank=stats.median_rank,
    )


@router.get("/{mc_id}/result", response_model=MonteCarloResultResponse)
async def get_monte_carlo_result(mc_id: str) -> MonteCarloResultResponse:
    """Get results of a completed Monte Carlo simulation."""
    run = monte_carlo_service.get_run(mc_id)
    if not run:
        raise HTTPException(status_code=404, detail="Monte Carlo run not found")

    if run.status != MonteCarloStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Results not available. Status: {run.status.value}",
        )

    if not run.result:
        raise HTTPException(status_code=500, detail="Results missing")

    result = run.result

    # Convert config to dict
    config_dict = {
        "num_farms": result.config.num_farms,
        "num_packers": result.config.num_packers,
        "num_distribution_centers": result.config.num_distribution_centers,
        "num_retailers": result.config.num_retailers,
        "retailers_with_delis_pct": result.config.retailers_with_delis_pct,
        "contamination_rate": result.config.contamination_rate,
        "contamination_duration_days": result.config.contamination_duration_days,
        "pathogen": result.config.pathogen,
        "inventory_strategy": result.config.inventory_strategy,
        "simulation_days": result.config.simulation_days,
        "interview_success_rate": result.config.interview_success_rate,
        "record_collection_window_days": result.config.record_collection_window_days,
        "num_iterations": result.config.num_iterations,
        "base_random_seed": result.config.base_random_seed,
    }

    return MonteCarloResultResponse(
        monte_carlo_id=mc_id,
        config=config_dict,
        iterations_completed=result.num_iterations_completed,
        iterations_failed=result.num_iterations_failed,
        farm_scope_expansion=_stats_to_response(result.farm_scope_expansion),
        tlc_scope_expansion=_stats_to_response(result.tlc_scope_expansion),
        tlcs_location_expansion=_stats_to_response(result.tlcs_location_expansion),
        path_expansion=_stats_to_response(result.path_expansion),
        det_farms_in_scope=_stats_to_response(result.det_farms_in_scope),
        det_tlcs_in_scope=_stats_to_response(result.det_tlcs_in_scope),
        det_tlcs_locations=_stats_to_response(result.det_tlcs_locations),
        prob_farms_in_scope=_stats_to_response(result.prob_farms_in_scope),
        prob_tlcs_in_scope=_stats_to_response(result.prob_tlcs_in_scope),
        prob_tlcs_locations=_stats_to_response(result.prob_tlcs_locations),
        total_cases=_stats_to_response(result.total_cases),
        deterministic_identification=_id_stats_to_response(result.deterministic_identification),
        probabilistic_identification=_id_stats_to_response(result.probabilistic_identification),
        # Investigation timing metrics
        det_investigation_days=_stats_to_response(result.det_investigation_days) if result.det_investigation_days else None,
        det_investigation_work_hours=_stats_to_response(result.det_investigation_work_hours) if result.det_investigation_work_hours else None,
        prob_investigation_days=_stats_to_response(result.prob_investigation_days) if result.prob_investigation_days else None,
        prob_investigation_work_hours=_stats_to_response(result.prob_investigation_work_hours) if result.prob_investigation_work_hours else None,
        timing_expansion=_stats_to_response(result.timing_expansion) if result.timing_expansion else None,
        mean_expansion_95ci=list(result.expansion_confidence_interval_95),
        identification_difference_significant=(
            result.identification_difference_pvalue is not None
            and result.identification_difference_pvalue < 0.05
        ),
        identification_pvalue=result.identification_difference_pvalue,
    )
