from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.errors import AppError, app_error_handler, generic_500_handler, validation_error_handler
from ..core.logging import get_logger
from .routers import health_router, metrics_router, records_router

app = FastAPI(
    title="Supabase Data Access API",
    description="FastAPI backend agent to read/query Supabase PostgreSQL with modular architecture and robust error handling.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Health", "description": "Service health and metadata"},
        {"name": "Metrics", "description": "Operational metrics endpoints"},
        {"name": "Records", "description": "CRUD access to records stored in Supabase"},
    ],
)

# Configure CORS from settings
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(ValueError, lambda request, exc: generic_500_handler(request, exc))  # basic catch
app.add_exception_handler(Exception, generic_500_handler)
try:
    # Pydantic v2 ValidationError import handled in errors.py
    from pydantic import ValidationError as PydanticValidationError  # noqa

    app.add_exception_handler(PydanticValidationError, validation_error_handler)
except Exception:
    pass


class HealthResponse(BaseModel):
    """Response model for health check."""

    message: str = Field(..., description="Human-readable health status message")


# PUBLIC_INTERFACE
@app.get("/", response_model=HealthResponse, tags=["Health"], summary="Health Check", description="Basic service health check.")
def health_check():
    """Return health status payload."""
    logger = get_logger(__name__)
    logger.info("Health check requested")
    return {"message": "Healthy"}


# Include API routers
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(records_router)
