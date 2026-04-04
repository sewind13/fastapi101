#!/usr/bin/env bash
set -euo pipefail

python -m app.jobs.cleanup_revoked_tokens
