#!/usr/bin/env bash

set -euo pipefail

echo "Starting outbox dispatcher..."
exec python -m app.jobs.dispatch_outbox
