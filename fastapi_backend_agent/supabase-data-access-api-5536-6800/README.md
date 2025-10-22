# Supabase Data Access API

FastAPI backend agent that connects to a Supabase PostgreSQL database, exposes REST endpoints to read/query data, and includes structured logging, error handling, and basic observability.

Architecture overview
- This project uses the Supabase Python SDK (supabase-py v2) for data access. It does NOT use SQLAlchemy.
- Configuration is provided via environment variables and loaded using pydantic-settings.
- API structure uses routers:
  - Health: /health
  - Metrics: /metrics (Prometheus if available, JSON fallback)
  - Records: /records (CRUD)
- Logging is structured JSON and aligned with Uvicorn logging.

Environment variables
Required
- SUPABASE_URL: Your Supabase project URL (https://<PROJECT-REF>.supabase.co)
- SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY: Use the Service Role key for server-side operations (preferred). The anon key is less privileged and can also be used according to your security model.

Optional
- SUPABASE_SCHEMA: Target schema name (default: public)
- CORS_ALLOW_ORIGINS: Comma-separated origins or * (default: *)
- LOG_LEVEL: Logging level (default: INFO)
- APP_PORT: Server port (default: 3001)

Quickstart
1) Create your environment file
   - Copy the example to a .env in the working directory you will run the app from:
     cp .env.example .env
   - Note: The application reads .env from the current working directory. If you run from the repo root, place .env at repo root. If you run from fastapi_backend_agent/, you can also use fastapi_backend_agent/.env.

2) Fill in values in .env
   - Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY).
   - Optionally set CORS_ALLOW_ORIGINS, LOG_LEVEL, SUPABASE_SCHEMA, APP_PORT.

3) Install dependencies
   pip install -r fastapi_backend_agent/requirements.txt

4) Start the server
   Option A (recommended entrypoint with correct import path):
     python fastapi_backend_agent/run_server.py
   Option B (explicit uvicorn command):
     uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001 --reload

5) Visit endpoints
   - Health:   http://localhost:3001/health
   - Docs:     http://localhost:3001/docs
   - Metrics:  http://localhost:3001/metrics

Verification (sample curl commands)
- Health
  curl -s http://localhost:3001/health
  Expected 200 JSON:
  {
    "status": "ok",
    "version": "0.1.0",
    "uptime_seconds": <float>,
    "message": "Healthy"
  }

- List records (pagination/filtering supported)
  curl -s "http://localhost:3001/records?page=1&page_size=10"
  Expected 200 JSON:
  {
    "items": [ ... ],
    "meta": { "page": 1, "page_size": 10, "total": <int>, "total_pages": <int> }
  }
  Note: If Supabase is not configured correctly, you will get a structured error:
  {
    "error": {
      "code": "config_error",
      "message": "Supabase configuration missing: ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY are set",
      "details": null,
      "trace_id": "<trace>"
    }
  }

- Create record
  curl -s -X POST http://localhost:3001/records \
    -H "Content-Type: application/json" \
    -d '{"title":"Hello","description":"World"}'
  Expected 201 JSON:
  {
    "id": "<uuid>",
    "title": "Hello",
    "description": "World",
    "created_at": "<timestamp>"
  }

- Update record (PATCH)
  curl -s -X PATCH http://localhost:3001/records/<id> \
    -H "Content-Type: application/json" \
    -d '{"title":"Updated Title"}'
  Expected 200 JSON:
  {
    "id": "<uuid>",
    "title": "Updated Title",
    "description": "World",
    "created_at": "<timestamp>"
  }

- Delete record
  curl -s -X DELETE http://localhost:3001/records/<id>
  Expected 200 JSON:
  { "success": true, "id": "<uuid>" }

- Metrics
  curl -s http://localhost:3001/metrics
  Expected:
  - If prometheus_client installed: text/plain Prometheus exposition
  - Otherwise: JSON summary with counters/histograms

Records table schema (example)
Run this in Supabase SQL editor (adjust as needed):

-- Enable pgcrypto if you want gen_random_uuid()
create extension if not exists "pgcrypto";

create table if not exists public.records (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  created_at timestamp with time zone default now()
);

Security notes
- Use the SUPABASE_SERVICE_ROLE_KEY only server-side. Never expose it to client-side/browser code.
- If you prefer least-privilege for read-only, use row-level security policies and the anon key accordingly.

Troubleshooting
- Import path error / app not found:
  Ensure you start uvicorn with the correct import path:
    uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001 --reload
  Or use:
    python fastapi_backend_agent/run_server.py

- Dependencies not installed / ImportError:
  Install required dependencies:
    pip install -r fastapi_backend_agent/requirements.txt

- Environment variables not applied:
  The app reads .env from the current working directory. If running from the repo root, place .env at the repo root and restart the server. If running from fastapi_backend_agent/, place .env there.
  Missing Supabase config will not crash startup (health/docs work), but data routes will respond with code=config_error.

- Port / preview issues:
  Use APP_PORT in .env to change the port (default 3001). If you change .env, restart your preview/server.

- Supabase temporarily unavailable:
  Startup should continue. Data routes may return errors (e.g., supabase_init_error or supabase_query_error) until connectivity is restored.

OpenAPI and docs
- OpenAPI JSON:   /openapi.json
- Swagger UI docs: /docs

License
- See project terms as applicable.
