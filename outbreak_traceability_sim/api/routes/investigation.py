"""
Investigation API routes.

Endpoints for traceback analysis and convergence results.
"""

from fastapi import APIRouter, HTTPException

from ..schemas.investigation import (
    InvestigationStepsResponse,
    TracebackStepResponse,
    ConvergenceResponse,
    ConvergenceResultResponse,
    CaseDataResponse,
)
from ..services.simulation_service import simulation_service, SimulationStatus

router = APIRouter()


@router.get("/{simulation_id}/steps", response_model=InvestigationStepsResponse)
async def get_investigation_steps(simulation_id: str) -> InvestigationStepsResponse:
    """
    Get step-by-step traceback data for animation.

    Returns deterministic and probabilistic traceback steps showing
    how certainty changes through the supply chain.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Investigation data not available. Status: {run.status.value}",
        )

    if not run.investigation_data:
        return InvestigationStepsResponse(
            deterministic_steps=[],
            probabilistic_steps=[],
            actual_source_farm_id=None,
        )

    det_steps = [
        TracebackStepResponse(**s) for s in run.investigation_data["deterministic_steps"]
    ]
    prob_steps = [
        TracebackStepResponse(**s) for s in run.investigation_data["probabilistic_steps"]
    ]

    return InvestigationStepsResponse(
        deterministic_steps=det_steps,
        probabilistic_steps=prob_steps,
        actual_source_farm_id=run.investigation_data.get("actual_source_farm_id"),
    )


@router.get("/{simulation_id}/convergence", response_model=ConvergenceResponse)
async def get_convergence(simulation_id: str) -> ConvergenceResponse:
    """
    Get convergence analysis results.

    Returns farms ranked by likelihood of being the contamination source,
    based on traceback convergence from multiple cases.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Convergence data not available. Status: {run.status.value}",
        )

    convergence = simulation_service.get_convergence_results(simulation_id)

    results = [ConvergenceResultResponse(**c) for c in convergence]

    primary_suspect = None
    if results:
        primary_suspect = {
            "farm_id": results[0].farm_id,
            "farm_name": results[0].farm_name,
            "probability": results[0].confidence_score,
        }

    return ConvergenceResponse(results=results, primary_suspect=primary_suspect)


@router.get("/{simulation_id}/farm-probabilities")
async def get_farm_probabilities(simulation_id: str) -> dict[str, float]:
    """
    Get probability distribution over farms as potential contamination sources.

    Returns a normalized probability for each farm based on convergence analysis.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Data not available. Status: {run.status.value}",
        )

    if not run.result:
        return {}

    # Get from calculated scenario results
    calculated = run.result.get("scenarios", {}).get("calculated", {})
    return calculated.get("farm_probabilities", {})


@router.get("/{simulation_id}/scope")
async def get_investigation_scope(simulation_id: str) -> dict:
    """
    Get nodes in investigation scope for deterministic and probabilistic modes.

    Returns which nodes are potentially involved in the contamination path
    for each investigation mode. Used for side-by-side visualization.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Scope data not available. Status: {run.status.value}",
        )

    return simulation_service.get_investigation_scope(simulation_id)


@router.get("/{simulation_id}/farm-traceback-metrics")
async def get_farm_traceback_metrics(simulation_id: str) -> dict:
    """
    Get per-farm traceback metrics for both deterministic and probabilistic modes.

    Returns FDA-style convergence analysis showing:
    - Which farms the cases trace back to
    - Case coverage (% of cases that trace to each farm)
    - Exclusive cases (cases that ONLY trace to this farm)
    - Confidence scores
    - Whether each farm is the actual source (ground truth)

    Used for the Investigate tab to compare traceback results.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Farm metrics not available. Status: {run.status.value}",
        )

    return simulation_service.get_farm_traceback_metrics(simulation_id)


@router.get("/{simulation_id}/cases", response_model=CaseDataResponse)
async def get_case_data(simulation_id: str) -> CaseDataResponse:
    """
    Get case data for visualizations.

    Returns:
    - epi_curve: Cases by onset date for epidemic curve chart
    - summary: Summary statistics (total cases, hospitalization rate, etc.)
    - node_case_counts: Case counts per exposure location for network visualization
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Case data not available. Status: {run.status.value}",
        )

    data = simulation_service.get_case_data(simulation_id)
    return CaseDataResponse(**data)
