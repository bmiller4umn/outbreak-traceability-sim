"""Schemas for network data endpoints."""

from typing import Optional, List
from pydantic import BaseModel


class NodeResponse(BaseModel):
    """Supply chain node data for visualization."""

    id: str
    type: str
    name: str
    city: str
    state: str
    is_contaminated: bool = False
    contamination_probability: float = 0.0


class EdgeResponse(BaseModel):
    """Supply chain edge data for visualization."""

    id: str
    source: str
    target: str
    product_categories: List[str]
    shipment_volume: float


class NetworkResponse(BaseModel):
    """Complete network data for visualization."""

    nodes: List[NodeResponse]
    edges: List[EdgeResponse]


class LotResponse(BaseModel):
    """Lot code record data."""

    tlc: str
    created_at: str
    created_by_node_id: str
    product_category: str
    is_contaminated: bool
    contamination_probability: float
    source_tlcs: List[str]
    source_probabilities: dict[str, float]


class LotsResponse(BaseModel):
    """Lot graph data."""

    lots: dict[str, LotResponse]
    forward_edges: dict[str, List[tuple[str, float]]]
    backward_edges: dict[str, List[tuple[str, float]]]
