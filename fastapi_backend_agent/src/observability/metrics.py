from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional, Tuple

from ..core.logging import get_logger

logger = get_logger(__name__)

# Attempt to import prometheus_client; if unavailable, use fallback
try:
    from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST  # type: ignore

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover - safe guard on optional dependency
    Counter = object  # type: ignore
    Histogram = object  # type: ignore
    CollectorRegistry = object  # type: ignore

    def generate_latest(_: Any) -> bytes:  # type: ignore
        return b""

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"  # type: ignore
    _PROM_AVAILABLE = False


# A single shared registry (Prometheus) or a fallback store
_registry: Optional["CollectorRegistry"] = None

# Fallback store with thread safety
_fallback_lock = threading.RLock()
_fallback_counters: Dict[str, float] = {}
# For histogram fallback, we will track simple aggregates: count, sum, min, max
_fallback_histograms: Dict[str, Dict[str, float]] = {}

# Metric names (acceptance criteria)
REQUESTS_TOTAL_NAME = "requests_total"
ERRORS_TOTAL_NAME = "errors_total"
REQUEST_LATENCY_SECONDS_NAME = "request_latency_seconds"

# Label sets we plan to support minimally (route/method/status)
_DEFAULT_LABELS = ("route", "method", "status")


def _init_prom_registry() -> "CollectorRegistry":
    """
    Initialize or return a shared Prometheus CollectorRegistry.
    """
    global _registry
    if _registry is None:
        if _PROM_AVAILABLE:
            _registry = CollectorRegistry()
        else:
            _registry = None
    return _registry  # type: ignore


def _fallback_counter_inc(name: str, value: float = 1.0, labels: Optional[Tuple[str, ...]] = None) -> None:
    """
    Increment a counter in the fallback store. Labels are flattened into the name for simplicity.
    """
    key = name
    if labels:
        key = f"{name}{{" + ",".join(labels) + "}}"
    with _fallback_lock:
        _fallback_counters[key] = _fallback_counters.get(key, 0.0) + float(value)


def _fallback_histogram_observe(name: str, value: float, labels: Optional[Tuple[str, ...]] = None) -> None:
    """
    Observe a value in the fallback histogram store, maintaining simple aggregates.
    """
    key = name
    if labels:
        key = f"{name}{{" + ",".join(labels) + "}}"
    v = float(value)
    with _fallback_lock:
        agg = _fallback_histograms.get(key) or {"count": 0.0, "sum": 0.0, "min": v, "max": v}
        agg["count"] += 1.0
        agg["sum"] += v
        if v < agg["min"]:
            agg["min"] = v
        if v > agg["max"]:
            agg["max"] = v
        _fallback_histograms[key] = agg


# PUBLIC_INTERFACE
def prometheus_available() -> bool:
    """
    Return True if prometheus_client is installed and usable.
    """
    return _PROM_AVAILABLE


# Initialize metrics
if _PROM_AVAILABLE:
    _reg = _init_prom_registry()
    # Define metrics using the shared registry
    requests_total = Counter(
        REQUESTS_TOTAL_NAME,
        "Total number of HTTP requests",
        labelnames=_DEFAULT_LABELS,
        registry=_reg,
    )
    errors_total = Counter(
        ERRORS_TOTAL_NAME,
        "Total number of HTTP requests that resulted in error responses (5xx/4xx as applicable)",
        labelnames=_DEFAULT_LABELS,
        registry=_reg,
    )
    request_latency_seconds = Histogram(
        REQUEST_LATENCY_SECONDS_NAME,
        "Latency of HTTP requests in seconds",
        labelnames=_DEFAULT_LABELS,
        # Default buckets are fine; could customize if needed
        registry=_reg,
    )
else:
    # Placeholders for attribute presence; functions below will use fallback operations.
    requests_total = None  # type: ignore
    errors_total = None  # type: ignore
    request_latency_seconds = None  # type: ignore


# PUBLIC_INTERFACE
def inc_requests(route: str, method: str, status: str, value: float = 1.0) -> None:
    """
    Increment the requests_total counter.

    Parameters:
    - route: Route path template (e.g., /records)
    - method: HTTP method (GET/POST/...)
    - status: HTTP status code as string (e.g., "200")
    - value: Increment amount (default 1.0)
    """
    labels = (route, method.upper(), status)
    if _PROM_AVAILABLE and requests_total is not None:
        try:
            requests_total.labels(*labels).inc(value)
            return
        except Exception as exc:  # safety net
            logger.error("Prometheus requests_total increment failed", exc_info=exc)
    _fallback_counter_inc(REQUESTS_TOTAL_NAME, value=value, labels=labels)


# PUBLIC_INTERFACE
def inc_errors(route: str, method: str, status: str, value: float = 1.0) -> None:
    """
    Increment the errors_total counter.

    Parameters mirror inc_requests.
    """
    labels = (route, method.upper(), status)
    if _PROM_AVAILABLE and errors_total is not None:
        try:
            errors_total.labels(*labels).inc(value)
            return
        except Exception as exc:
            logger.error("Prometheus errors_total increment failed", exc_info=exc)
    _fallback_counter_inc(ERRORS_TOTAL_NAME, value=value, labels=labels)


# PUBLIC_INTERFACE
def observe_latency(route: str, method: str, status: str, seconds: float) -> None:
    """
    Observe request latency in seconds.

    Parameters:
    - seconds: Duration of the request in seconds
    """
    labels = (route, method.upper(), status)
    if _PROM_AVAILABLE and request_latency_seconds is not None:
        try:
            request_latency_seconds.labels(*labels).observe(seconds)
            return
        except Exception as exc:
            logger.error("Prometheus request_latency_seconds observe failed", exc_info=exc)
    _fallback_histogram_observe(REQUEST_LATENCY_SECONDS_NAME, value=seconds, labels=labels)


# PUBLIC_INTERFACE
def metrics_exposition() -> Tuple[str, bytes]:
    """
    Generate the metrics payload and content type.

    Returns:
    - content_type: MIME type string
    - body: bytes payload

    If Prometheus is available, returns text/plain Prometheus exposition.
    Otherwise, returns a minimal JSON payload summarizing counters and histogram aggregates.
    """
    if _PROM_AVAILABLE and _registry is not None:
        try:
            payload = generate_latest(_registry)
            return CONTENT_TYPE_LATEST, payload
        except Exception as exc:
            logger.error("Failed to generate Prometheus metrics; falling back to JSON", exc_info=exc)

    # Fallback JSON: expose current counters and histograms
    with _fallback_lock:
        data: Dict[str, Any] = {
            "counters": dict(_fallback_counters),
            "histograms": dict(_fallback_histograms),
            "generated_at": time.time(),
        }
    import json

    return "application/json", json.dumps(data, ensure_ascii=False).encode("utf-8")
