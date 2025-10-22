from __future__ import annotations

from fastapi import APIRouter, Response

from ...core.logging import get_logger
from ...observability.metrics import metrics_exposition, prometheus_available

router = APIRouter(
    prefix="",
    tags=["Metrics"],
)


class MetricsInfo:
    """
    Metrics router providing Prometheus exposition or JSON fallback.

    - GET /metrics: Prometheus text/plain if prometheus_client is installed,
      otherwise JSON payload with minimal aggregates.
    """


# PUBLIC_INTERFACE
@router.get(
    "/metrics",
    summary="Operational metrics",
    description=(
        "Returns Prometheus metrics in text/plain exposition format if prometheus_client "
        "is installed; otherwise returns a JSON summary of counters and histograms."
    ),
    responses={
        200: {
            "description": "Metrics returned",
            "content": {
                "text/plain": {"example": "# HELP requests_total Total number of HTTP requests\n# TYPE requests_total counter"},
                "application/json": {"example": {"counters": {"requests_total{route=/,method=GET,status=200}": 1}}},
            },
        }
    },
)
def get_metrics() -> Response:
    """
    Metrics endpoint.

    Returns:
    - Response: A Starlette Response with appropriate content type and payload depending on availability of prometheus_client.
    """
    logger = get_logger(__name__)
    ctype, body = metrics_exposition()
    logger.info("Serving /metrics", extra={"prometheus_available": prometheus_available(), "content_type": ctype})
    return Response(content=body, media_type=ctype)


# PUBLIC_INTERFACE
@router.get(
    "/metrics/info",
    summary="Metrics router info",
    description="Returns a short message describing metrics router integration status.",
    responses={200: {"description": "Metrics router is available"}},
)
def metrics_info() -> dict:
    """
    Informational endpoint for metrics router.

    Returns:
    - dict: Minimal payload indicating that metrics router is wired.
    """
    return {
        "message": "Metrics router is available.",
        "prometheus_available": prometheus_available(),
        "endpoints": ["/metrics", "/metrics/info"],
    }
