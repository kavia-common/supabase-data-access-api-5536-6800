from __future__ import annotations

from typing import Any, Dict, Optional, Union

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette import status

from .logging import generate_trace_id, get_logger


class AppError(Exception):
    """
    Base application error supporting code, message, details and HTTP status.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Union[Dict[str, Any], Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details
        self.trace_id = trace_id or generate_trace_id()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": str(self),
                "details": self.details,
                "trace_id": self.trace_id,
            }
        }


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found", *, details: Optional[Any] = None) -> None:
        super().__init__(message, code="not_found", status_code=status.HTTP_404_NOT_FOUND, details=details)


# PUBLIC_INTERFACE
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    FastAPI exception handler for AppError.
    Returns JSON in the shape: { "error": { code, message, details, trace_id } }
    """
    logger = get_logger(__name__)
    payload = exc.to_dict()
    logger.warning(f"AppError: {payload}", extra={"trace_id": exc.trace_id})
    return JSONResponse(status_code=exc.status_code, content=payload)


# PUBLIC_INTERFACE
async def validation_error_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """
    FastAPI exception handler for Pydantic ValidationError.
    Normalizes validation errors into the unified error format.
    """
    logger = get_logger(__name__)
    trace_id = generate_trace_id()

    details: Dict[str, Any] = {
        "errors": [e.model_dump() if hasattr(e, "model_dump") else dict(e) for e in exc.errors()]
    }
    payload = {
        "error": {
            "code": "validation_error",
            "message": "Request validation failed",
            "details": details,
            "trace_id": trace_id,
        }
    }
    logger.info("ValidationError", extra={"trace_id": trace_id, "details": details})
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


# PUBLIC_INTERFACE
def generic_500_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Fallback handler to avoid leaking internal details; returns generic 500 payload.
    """
    logger = get_logger(__name__)
    trace_id = generate_trace_id()
    payload = {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": None,
            "trace_id": trace_id,
        }
    }
    logger.error("Unhandled exception", exc_info=exc, extra={"trace_id": trace_id})
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
