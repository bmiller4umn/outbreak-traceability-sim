"""
Export API routes.

Endpoints for exporting simulation data to Excel format.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..services.export_service import export_simulation_to_excel, get_export_filename
from ..services.simulation_service import simulation_service, SimulationStatus

router = APIRouter()


@router.get("/{simulation_id}/excel")
async def export_simulation_excel(simulation_id: str):
    """
    Export simulation data to Excel format.

    Returns an Excel workbook containing:
    - Metadata (configuration, timestamps)
    - Network nodes
    - Traceability records (CTEs/KDEs)
    - Lot codes
    - Case data
    - Contamination events
    - Investigation results

    Args:
        simulation_id: ID of the simulation to export

    Returns:
        Excel file download
    """
    # Verify simulation exists and is completed
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot export simulation. Status: {run.status.value}. Simulation must be completed."
        )

    # Generate Excel file
    buffer = export_simulation_to_excel(simulation_id)
    if not buffer:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate export. Simulation data may be incomplete."
        )

    filename = get_export_filename(simulation_id)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
