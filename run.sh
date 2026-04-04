#!/usr/bin/env bash

set -euo pipefail

echo "Starting FastAPI template stack..."

if [[ ! -f .env ]]; then
    echo ".env file not found. Copy .env.example to .env first."
    exit 1
fi

docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build --remove-orphans
