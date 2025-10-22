# Supabase Data Access API (fastapi_backend_agent)

A FastAPI backend agent that connects to a Supabase PostgreSQL database, exposes REST endpoints for reading/querying data, and includes structured logging, modular architecture, and basic observability.

Key points
- Uses the Supabase Python SDK (supabase-py v2). Do not introduce SQLAlchemy.
- Runs on port 3001 by default.
- Correct Uvicorn app import path: fastapi_backend_agent.src.api.main:app
- Health endpoint: GET /health (for preview probes and readiness checks)

Quick start (local)
1) Create your .env from the example:
   cp .env.example .env
   # Or, if running from fastapi_backend_agent directory:
   cp fastapi_backend_agent/.env.example fastapi_backend_agent/.env

2) Install dependencies:
   pip install -r fastapi_backend_agent/requirements.txt

3) Start the server (choose one):
   Option A (recommended):
     python fastapi_backend_agent/run_server.py
   Option B (explicit uvicorn with reload for verbose errors):
     uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001 --reload
   Option C (provided shell helper):
     chmod +x bin/run_uvicorn.sh
     ./bin/run_uvicorn.sh
     # You can enable reload via: RELOAD=true ./bin/run_uvicorn.sh

4) Visit endpoints:
   - Health:   http://localhost:3001/health
   - Docs:     http://localhost:3001/docs
   - Metrics:  http://localhost:3001/metrics

Environment variables (.env)
Required
- SUPABASE_URL=
- SUPABASE_SERVICE_ROLE_KEY=    # or set SUPABASE_ANON_KEY=
Optional
- SUPABASE_SCHEMA=public
- CORS_ALLOW_ORIGINS=*
- LOG_LEVEL=INFO
- APP_PORT=3001

Note: The application reads .env from the current working directory. If you run commands from the repo root, place .env at the repo root. If you run from fastapi_backend_agent/, you can also put .env there.

Docker
Build and run:
- docker build -t supabase-data-access-api ./fastapi_backend_agent
- docker run --rm -p 3001:3001 --env-file ./.env supabase-data-access-api

The image exposes port 3001 and starts Uvicorn with:
  uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001

Preview system notes
- The preview expects the backend to listen on port 3001.
- Health probe: GET /health must return 200.
- If you need to run on a different port locally, set APP_PORT in .env and adjust your local tooling accordingly. The preview environment will still target 3001.

Configuration hints (do not create/modify these files here)
If your project uses a config file like kavia.yaml or project.yaml, document the backend port as 3001. Example snippet (for documentation only):
  backend:
    port: 3001

Troubleshooting
- Import path error or "app not found":
  Ensure you use the correct import path:
    uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001 --reload

- Missing dependencies:
  pip install -r fastapi_backend_agent/requirements.txt

- Environment variables not applying:
  Ensure .env is in the same directory where you run the command from. Health and docs will work without Supabase configured, but data routes will return a structured error with code=config_error until SUPABASE_URL and a key are provided.

- Need more detailed error output during development:
  Use --reload with uvicorn or set RELOAD=true when running ./bin/run_uvicorn.sh.

Additional documentation
A more detailed README is available at:
  fastapi_backend_agent/supabase-data-access-api-5536-6800/README.md
