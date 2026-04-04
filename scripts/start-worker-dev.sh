#!/usr/bin/env bash

set -euo pipefail

echo "Syncing development dependencies..."
uv sync --frozen

echo "Starting background worker..."
exec python -m app.worker.runner
