import json
import logging
import sys
import time
import uuid
from typing import Any, Dict, Optional

from .config import get_settings


class JsonLogFormatter(logging.Formatter):
    """
    A structured JSON log formatter.

    Produces JSON logs with standard keys and seamlessly integrates with uvicorn log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include uvicorn/access attributes if present
        for attr in ("method", "path", "status_code", "client_addr"):
            if hasattr(record, attr):
                base[attr] = getattr(record, attr)

        # Optional extras
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "trace_id"):
            base["trace_id"] = getattr(record, "trace_id")

        return json.dumps(base, ensure_ascii=False)


def _ensure_root_configured(level: str) -> None:
    """
    Configure the root logger once with stream handler and JSON formatter.
    """
    root = logging.getLogger()
    if getattr(root, "_json_configured", False):
        return

    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(JsonLogFormatter())
    root.handlers = [handler]
    root.propagate = False
    setattr(root, "_json_configured", True)

    # Configure uvicorn loggers to align with our format/level
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.setLevel(level)
        lg.handlers = [handler]
        lg.propagate = False


# PUBLIC_INTERFACE
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a configured logger. Ensures a structured JSON logging setup is applied.

    - Respects LOG_LEVEL from Settings
    - Formats logs as JSON
    - Compatible with uvicorn loggers
    """
    # Be resilient if settings are not yet available or invalid at import-startup
    try:
        level = get_settings().log_level
    except Exception:
        level = "INFO"
    _ensure_root_configured(level)
    return logging.getLogger(name or "app")


# PUBLIC_INTERFACE
def generate_trace_id() -> str:
    """
    Generate a random trace ID for correlation in logs and error responses.
    """
    return uuid.uuid4().hex
