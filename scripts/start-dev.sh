#!/usr/bin/env bash

set -euo pipefail

echo "Syncing development dependencies..."
uv sync --frozen

echo "Applying database migrations..."
alembic upgrade head

echo "Starting FastAPI development server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
