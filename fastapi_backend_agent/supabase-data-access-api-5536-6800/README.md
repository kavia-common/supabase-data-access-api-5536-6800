# supabase-data-access-api-5536-6800

FastAPI backend agent that connects to Supabase PostgreSQL and exposes REST endpoints with structured logging and modular architecture.

## Quickstart

1. Create a .env file based on fastapi_backend_agent/.env.example and set:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY (treat SUPABASE_KEY as the active key; service role preferred if available)
   - Optionally adjust CORS_ALLOW_ORIGINS, LOG_LEVEL, SUPABASE_SCHEMA

2. Install dependencies:
   pip install -r fastapi_backend_agent/requirements.txt

3. Run server:
   uvicorn fastapi_backend_agent.src.api.main:app --host 0.0.0.0 --port 3001 --reload

OpenAPI docs at /docs and /openapi.json.

## Notes

- Logging is structured JSON and level is driven by LOG_LEVEL via core.logging setup.
- CORS is configured from CORS_ALLOW_ORIGINS (comma-separated or * for all).
- Supabase client is initialized at startup and released on shutdown via the FastAPI lifespan.
