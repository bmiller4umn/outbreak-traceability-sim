"""
Network API routes.

Endpoints for retrieving supply chain network data for visualization.
"""

from fastapi import APIRouter, HTTPException

from ..schemas.network import NetworkResponse, NodeResponse, EdgeResponse
from ..services.simulation_service import simulation_service, SimulationStatus

router = APIRouter()


@router.get("/{simulation_id}", response_model=NetworkResponse)
async def get_network(simulation_id: str) -> NetworkResponse:
    """
    Get the supply chain network graph data for visualization.

    Returns nodes (farms, packers, DCs, retailers) and edges (supply relationships).
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status not in (SimulationStatus.COMPLETED, SimulationStatus.RUNNING):
        raise HTTPException(
            status_code=400,
            detail=f"Network data not available. Status: {run.status.value}",
        )

    if not run.network_data:
        raise HTTPException(status_code=500, detail="Network data not available")

    nodes = [NodeResponse(**n) for n in run.network_data["nodes"]]
    edges = [EdgeResponse(**e) for e in run.network_data["edges"]]

    return NetworkResponse(nodes=nodes, edges=edges)


@router.get("/{simulation_id}/lots")
async def get_lots(simulation_id: str) -> dict:
    """
    Get lot code tracking data for detailed visualization.

    Returns lot records with their source/destination relationships.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if run.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Lot data not available. Status: {run.status.value}",
        )

    # Extract lot data from simulator
    if not run.simulator or not run.simulator.lot_graph:
        return {"lots": {}, "forward_edges": {}, "backward_edges": {}}

    lot_graph = run.simulator.lot_graph

    lots = {}
    for tlc, lot in lot_graph.lots.items():
        lots[tlc] = {
            "tlc": lot.tlc,
            "created_at": lot.created_at.isoformat(),
            "created_by_node_id": str(lot.created_by_node_id),
            "product_category": lot.product_category,
            "is_contaminated": lot.is_contaminated,
            "contamination_probability": lot.contamination_probability,
            "source_tlcs": lot.source_tlcs,
            "source_probabilities": lot.source_tlc_probabilities,
        }

    return {
        "lots": lots,
        "forward_edges": {k: [(t, w) for t, w in v] for k, v in lot_graph.forward_edges.items()},
        "backward_edges": {k: [(t, w) for t, w in v] for k, v in lot_graph.backward_edges.items()},
    }


@router.get("/{simulation_id}/node/{node_id}")
async def get_node_details(simulation_id: str, node_id: str) -> dict:
    """
    Get detailed information about a specific supply chain node.
    """
    run = simulation_service.get_run(simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if not run.network_data:
        raise HTTPException(status_code=500, detail="Network data not available")

    # Find the node
    node = None
    for n in run.network_data["nodes"]:
        if n["id"] == node_id:
            node = n
            break

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Find connected edges
    incoming_edges = [e for e in run.network_data["edges"] if e["target"] == node_id]
    outgoing_edges = [e for e in run.network_data["edges"] if e["source"] == node_id]

    return {
        "node": node,
        "incoming_edges": incoming_edges,
        "outgoing_edges": outgoing_edges,
        "supplier_count": len(incoming_edges),
        "customer_count": len(outgoing_edges),
    }
