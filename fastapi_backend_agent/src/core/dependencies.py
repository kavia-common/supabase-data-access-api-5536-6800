from __future__ import annotations

import logging
from typing import Optional



from .config import Settings, get_settings as _get_settings
from .logging import get_logger as _get_logger


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """
    Dependency provider for Settings.
    """
    return _get_settings()


# PUBLIC_INTERFACE
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Dependency provider for a configured logger instance.
    """
    return _get_logger(name)


# PUBLIC_INTERFACE
def get_current_user():
    """
    Placeholder for authentication dependency.

    In a future iteration, integrate Supabase auth or JWT verification.
    For now, returns None to indicate unauthenticated context.
    """
    return None
