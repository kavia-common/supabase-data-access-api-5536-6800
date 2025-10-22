"""
Observability utilities for metrics and tracing.

This package provides a thin abstraction over Prometheus client metrics,
falling back to an in-memory JSON-compatible metrics store when the
prometheus_client package is not available.
"""
