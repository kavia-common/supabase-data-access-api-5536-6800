from __future__ import annotations

import threading
from typing import Optional

from supabase import Client, create_client  # type: ignore

from ..core.config import get_settings
from ..core.errors import AppError
from ..core.logging import get_logger

_logger = get_logger(__name__)

# Thread-safety for singleton initialization
_lock = threading.RLock()
_client: Optional[Client] = None
_client_schema: Optional[str] = None  # track schema used to allow reload on change


def _build_client() -> Client:
    """
    Internal factory to create a new Supabase Client using settings.
    """
    settings = get_settings()
    url = settings.supabase_url
    key = settings.supabase_key
    if not url or not key:
        raise AppError(
            "Supabase configuration missing: ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY are set",
            code="config_error",
        )
    try:
        client = create_client(url, key)
        return client
    except Exception as exc:
        _logger.error("Failed to create Supabase client", exc_info=exc)
        raise AppError("Failed to initialize Supabase client", code="supabase_init_error") from exc


# PUBLIC_INTERFACE
def get_client() -> Client:
    """
    Return a singleton Supabase Client instance configured from environment settings.

    This function ensures a single shared client is used across the app. If settings change
    during runtime (e.g., in tests), call reload_client() to rebuild with new settings.
    """
    global _client, _client_schema
    if _client is not None:
        return _client

    with _lock:
        if _client is None:
            _logger.info("Initializing Supabase client singleton")
            _client = _build_client()
            _client_schema = get_settings().supabase_schema or "public"
    return _client


# PUBLIC_INTERFACE
def get_schema() -> str:
    """
    Return the configured target Postgres schema (defaults to 'public').
    """
    try:
        schema = get_settings().supabase_schema or "public"
    except Exception:
        schema = "public"
    return schema


# PUBLIC_INTERFACE
def reload_client() -> None:
    """
    Rebuild the Supabase client using current settings.

    Useful for tests or when environment variables change.
    """
    global _client, _client_schema
    with _lock:
        _logger.info("Reloading Supabase client")
        _client = _build_client()
        _client_schema = get_settings().supabase_schema or "public"


# PUBLIC_INTERFACE
def close_client() -> None:
    """
    Close the Supabase client if underlying transport supports explicit closing.

    Currently, supabase-py uses httpx under the hood for async sync clients; there is
    no public close on client. We null out the singleton to allow GC and recreation.
    """
    global _client
    with _lock:
        _logger.info("Closing Supabase client (noop for current SDK); clearing singleton")
        _client = None
