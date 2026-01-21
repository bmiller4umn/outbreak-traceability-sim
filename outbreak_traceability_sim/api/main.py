"""
FastAPI application entry point for outbreak traceability simulation.
"""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import config
from .routes import simulation, network, investigation, monte_carlo, export

app = FastAPI(
    title="Outbreak Traceability Simulation API",
    description="API for simulating food supply chain outbreaks and comparing traceability scenarios",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(network.router, prefix="/api/network", tags=["network"])
app.include_router(investigation.router, prefix="/api/investigation", tags=["investigation"])
app.include_router(monte_carlo.router, prefix="/api/monte-carlo", tags=["monte-carlo"])
app.include_router(export.router, prefix="/api/export", tags=["export"])

# Static files directory (for production deployment)
STATIC_DIR = Path(__file__).parent.parent.parent / "static"


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "outbreak-traceability-sim"}


@app.get("/api/config")
async def get_config():
    """Get public configuration limits."""
    return {
        "maxMonteCarloIterations": config.max_monte_carlo_iterations,
        "defaultMonteCarloIterations": config.default_monte_carlo_iterations,
    }


@app.get("/")
async def root():
    """Root endpoint - serve frontend or API info."""
    # If static files exist (production), serve the frontend
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    # Otherwise return API info (development)
    return {
        "name": "Outbreak Traceability Simulation API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Mount static files if directory exists (production deployment)
if STATIC_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Catch-all route for SPA - must be after all API routes
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA for any non-API route."""
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return {"error": "Not found"}

        # Try to serve static file first
        static_file = STATIC_DIR / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)

        # Otherwise serve index.html for SPA routing
        return FileResponse(STATIC_DIR / "index.html")
