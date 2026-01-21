"""
Simulation API routes.

Endpoints for starting, monitoring, and retrieving simulation results.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any

from ..schemas.simulation import (
    SimulationConfigRequest,
    SimulationStartResponse,
    SimulationStatusResponse,
)
from ..services.simulation_service import simulation_service, SimulationStatus

router = APIRouter()


@router.post("/run", response_model=SimulationStartResponse)
async def run_simulation(
    config: SimulationConfigRequest,
    background_tasks: BackgroundTasks,
) -> SimulationStartResponse:
    """
    Start a new simulation with the given configuration.

    The simulation runs asynchronously. Use the status endpoint to poll for completion.
    """
    # Create simulation run
    simulation_id = simulation_service.create_simulation(config.model_dump())

    # Start simulation in background
    background_tasks.add_task(simulation_service.run_simulation, simulation_id)

    return SimulationStartResponse(
        simulation_id=simulation_id,
        status="started",
        message="Simulation started. Poll /status for progress.",
    )


@router.get("/{simulation_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(simulation_id: str) -> SimulationStatusResponse:
    """
    Get the status of a running or completed simulation.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return SimulationStatusResponse(
        simulation_id=run.id,
        status=run.status.value,
        progress=run.progress,
        message=run.error if run.status == SimulationStatus.ERROR else None,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


@router.get("/{simulation_id}/result")
async def get_simulation_result(simulation_id: str) -> dict[str, Any]:
    """
    Get the results of a completed simulation.

    Returns the full comparison between deterministic and calculated lot code scenarios.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Simulation not completed. Status: {run.status.value}",
        )

    if not run.result:
        raise HTTPException(status_code=500, detail="Simulation completed but no results available")

    return run.result
