from __future__ import annotations

import time
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...core.dependencies import get_logger, get_settings
from ...core.logging import get_logger as _get_logger

# Track app start time for uptime reporting
_START_TIME = time.time()

router = APIRouter(
    prefix="",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    """
    Response model for service health status.

    Provides high-level service status and metadata suitable for uptime checks and monitoring dashboards.
    """

    status: Literal["ok"] = Field(..., description="Service status. 'ok' indicates the API is healthy.")
    version: str = Field(..., description="Application semantic version.")
    uptime_seconds: float = Field(..., description="Seconds since the process started.")
    message: str = Field(..., description="Human-readable health message")


# PUBLIC_INTERFACE
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health",
    description="Returns service health status, version, and uptime.",
    responses={200: {"description": "Service is healthy"}},
)
def get_health(
    logger=Depends(get_logger),
    settings=Depends(get_settings),
) -> HealthResponse:
    """
    Health endpoint.

    Parameters:
    - logger: Injected application logger
    - settings: Injected application settings

    Returns:
    - HealthResponse: Status payload including version and uptime for basic monitoring.
    """
    # Local logger to ensure availability even if dependency injection not used outside FastAPI
    _log = logger or _get_logger(__name__)
    _log.info("Health endpoint requested")

    uptime = max(0.0, time.time() - _START_TIME)
    return HealthResponse(
        status="ok",
        version="0.1.0",
        uptime_seconds=uptime,
        message="Healthy",
    )
