# Python base image
FROM python:3.12-slim

# Ensure Python output is unbuffered and no .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# Install dependencies first for better cache utilization
COPY fastapi_backend_agent/requirements.txt ./fastapi_backend_agent/requirements.txt
RUN pip install --no-cache-dir -r fastapi_backend_agent/requirements.txt

# Copy application source
COPY fastapi_backend_agent ./fastapi_backend_agent

# Expose application port
EXPOSE 3001

# Start Uvicorn with the correct app import path and port
CMD ["uvicorn", "fastapi_backend_agent.src.api.main:app", "--host", "0.0.0.0", "--port", "3001"]
