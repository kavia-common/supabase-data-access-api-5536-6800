#!/bin/bash
cd /home/kavia/workspace/code-generation/supabase-data-access-api-5536-6800/fastapi_backend_agent
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

