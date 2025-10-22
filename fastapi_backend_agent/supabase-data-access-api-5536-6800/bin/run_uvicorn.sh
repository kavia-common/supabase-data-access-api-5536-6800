#!/usr/bin/env bash
# Start Uvicorn pointing at the correct FastAPI app import path for this repo.
# Usage:
#   ./bin/run_uvicorn.sh                  # default host 0.0.0.0, port 3001
#   APP_PORT=8080 ./bin/run_uvicorn.sh    # custom port
#   RELOAD=true ./bin/run_uvicorn.sh      # enable --reload for local dev
#   ./bin/run_uvicorn.sh --log-level debug  # pass extra args to uvicorn

set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${APP_PORT:-3001}"
APP_IMPORT="fastapi_backend_agent.src.api.main:app"

RELOAD_FLAG=""
if [[ "${RELOAD:-false}" =~ ^(1|true|yes)$ ]]; then
  RELOAD_FLAG="--reload"
fi

exec uvicorn "${APP_IMPORT}" --host "${HOST}" --port "${PORT}" ${RELOAD_FLAG} "$@"
