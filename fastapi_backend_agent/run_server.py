#!/usr/bin/env python3
"""
Entrypoint script to run the FastAPI application with uvicorn.

Usage:
    python run_server.py
Environment:
    Reads .env via pydantic-settings. Ensure SUPABASE_URL and a Supabase key are set if you intend to use data routes.
    Health and metrics endpoints will work without Supabase configuration.

This script uses the correct module path: fastapi_backend_agent.src.api.main:app
and binds to the port specified by APP_PORT (default 3001).
"""
import os
import uvicorn

def main() -> None:
    # PUBLIC_INTERFACE
    """
    Start the uvicorn server for the FastAPI app defined at fastapi_backend_agent.src.api.main:app.
    """
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "3001"))
    reload = os.getenv("RELOAD", "false").lower() in ("1", "true", "yes")

    uvicorn.run(
        "fastapi_backend_agent.src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        factory=False,
    )

if __name__ == "__main__":
    main()
