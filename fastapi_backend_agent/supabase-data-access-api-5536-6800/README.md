# Supabase Data Access API

FastAPI backend agent that connects to a Supabase PostgreSQL database, exposes REST endpoints to read/query data, and includes structured logging, error handling, and basic observability.

Quick start:
1) Create environment file from example:
   cp fastapi_backend_agent/.env.example fastapi_backend_agent/.env

2) Edit fastapi_backend_agent/.env and set:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY (preferred) or SUPABASE_ANON_KEY
   - Optional: CORS_ALLOW_ORIGINS, LOG_LEVEL, SUPABASE_SCHEMA

3) Install dependencies:
   pip install -r fastapi_backend_agent/requirements.txt

4) Run server:
   uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001 --reload

OpenAPI docs: /docs and /openapi.json

Optional SQL for 'records' table (run in Supabase SQL editor):
   create table if not exists public.records (
     id uuid primary key default gen_random_uuid(),
     title text not null,
     description text,
     created_at timestamp with time zone default now()
   );

Notes:
- Use service role key only on the server side. Never expose it to a browser.
- Metrics available at /metrics (Prometheus text if prometheus-client installed; otherwise JSON).
