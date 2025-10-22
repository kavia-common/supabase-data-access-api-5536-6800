from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["Metrics"],
)


class MetricsInfo:
    """
    Placeholder for metrics integration notes.

    In a future step, this router can mount a /metrics endpoint returning Prometheus text format
    or JSON metrics depending on the selected monitoring strategy.
    """


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
    return {"message": "Metrics router is available. /metrics to be implemented in a later step."}
