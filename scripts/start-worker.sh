#!/usr/bin/env bash

set -euo pipefail

echo "Starting background worker..."
exec python -m app.worker.runner
