"""
Application configuration loaded from environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration with sensible defaults."""

    # Monte Carlo limits
    max_monte_carlo_iterations: int = 10000  # Default allows up to 10000
    default_monte_carlo_iterations: int = 1000

    # CORS origins (comma-separated list)
    cors_origins: list[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        max_mc = int(os.getenv("MAX_MONTE_CARLO_ITERATIONS", "10000"))
        default_mc = int(os.getenv("DEFAULT_MONTE_CARLO_ITERATIONS", "1000"))

        # Ensure default doesn't exceed max
        default_mc = min(default_mc, max_mc)

        # Parse CORS origins
        cors_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

        # Support "*" for all origins (when frontend served from same origin)
        if cors_str.strip() == "*":
            cors_origins = ["*"]
        else:
            cors_origins = [origin.strip() for origin in cors_str.split(",") if origin.strip()]

        # Auto-add Render's external URL if available
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url and render_url not in cors_origins and cors_origins != ["*"]:
            cors_origins.append(render_url)

        return cls(
            max_monte_carlo_iterations=max_mc,
            default_monte_carlo_iterations=default_mc,
            cors_origins=cors_origins,
        )


# Global config instance - loaded once at startup
config = AppConfig.from_env()
