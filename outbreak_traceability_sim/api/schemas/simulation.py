"""Schemas for simulation endpoints."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class SimulationConfigRequest(BaseModel):
    """Request schema for starting a simulation."""

    num_farms: int = Field(default=5, ge=1, le=20, description="Number of farms")
    num_packers: int = Field(default=2, ge=1, le=10, description="Number of packers")
    num_distribution_centers: int = Field(default=3, ge=1, le=10, description="Number of DCs")
    num_retailers: int = Field(default=20, ge=5, le=100, description="Number of retailers")
    retailers_with_delis_pct: float = Field(default=0.3, ge=0, le=1, description="Percent of retailers with delis")

    contamination_rate: float = Field(default=1.0, ge=0, le=1, description="Contamination rate")
    contamination_duration_days: int = Field(default=7, ge=1, le=14, description="Duration of contamination event in days")
    pathogen: str = Field(default="Salmonella", description="Pathogen name")

    inventory_strategy: Literal["FIFO", "LIFO", "ALL_IN_WINDOW", "INVENTORY_WEIGHTED"] = Field(
        default="FIFO",
        description="DC inventory assignment strategy"
    )
    date_window_days: int = Field(default=7, ge=1, le=30, description="Date window for calculated lot codes")

    simulation_days: int = Field(default=90, ge=7, le=180, description="Simulation duration in days")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

    # Investigation parameters
    interview_success_rate: float = Field(
        default=0.7, ge=0.1, le=1.0,
        description="Fraction of cases successfully interviewed by epidemiologists"
    )
    record_collection_window_days: int = Field(
        default=14, ge=7, le=30,
        description="Days of records FDA requests from retail locations"
    )
    num_investigators: int = Field(
        default=5, ge=1, le=20,
        description="Number of investigators assigned to traceback"
    )

    # Timing parameters for realistic supply chain delays
    transit_speed_factor: float = Field(
        default=1.0, ge=0.5, le=2.0,
        description="Multiplier for all transit times (lower = faster)"
    )
    cooling_hold_hours: float = Field(
        default=12.0, ge=0, le=48,
        description="Hours product is held for cooling after harvest"
    )
    dc_inspection_hours: float = Field(
        default=6.0, ge=0, le=24,
        description="Hours for QA inspection at distribution centers"
    )
    retail_stocking_delay_hours: float = Field(
        default=4.0, ge=0, le=24,
        description="Hours between receiving and shelf availability at retail"
    )


class SimulationStartResponse(BaseModel):
    """Response when starting a simulation."""

    simulation_id: str
    status: str = "started"
    message: str = "Simulation started"


class SimulationStatusResponse(BaseModel):
    """Response for simulation status polling."""

    simulation_id: str
    status: Literal["pending", "running", "completed", "error"]
    progress: float = Field(ge=0, le=1, description="Progress from 0 to 1")
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
