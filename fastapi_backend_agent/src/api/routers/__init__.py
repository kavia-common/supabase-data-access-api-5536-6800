"""
API routers package. Add new routers here and include them in the application in main.py.
"""

from .health import router as health_router
from .metrics import router as metrics_router
from .records import router as records_router

__all__ = ["health_router", "metrics_router", "records_router"]
