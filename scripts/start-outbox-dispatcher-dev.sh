#!/usr/bin/env bash

set -euo pipefail

echo "Syncing development dependencies..."
uv sync --frozen

echo "Starting outbox dispatcher..."
exec python -m app.jobs.dispatch_outbox
