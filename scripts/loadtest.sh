#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-core}"

run_step() {
  local label="$1"
  local command="$2"

  echo
  echo "==> ${label}"
  eval "${command}"
}

print_usage() {
  cat <<'EOF'
Usage:
  ./scripts/loadtest.sh [core|worker|full]

Modes:
  core
    Starts API + monitoring stack and runs:
    smoke -> read -> auth

  worker
    Starts API + monitoring + worker stack and runs:
    smoke -> read -> auth -> write

  full
    Starts API + monitoring + worker stack and runs:
    smoke -> read -> auth -> write -> soak
EOF
}

case "${MODE}" in
  core)
    trap 'make down-loadtest' EXIT
    run_step "Starting load-test stack" "make up-loadtest"
    run_step "Smoke scenario" "make loadtest-smoke"
    run_step "Read baseline scenario" "make loadtest-read"
    run_step "Auth burst scenario" "make loadtest-auth"
    ;;
  worker)
    trap 'make down-loadtest-worker' EXIT
    run_step "Starting load-test worker stack" "make up-loadtest-worker"
    run_step "Smoke scenario" "make loadtest-smoke"
    run_step "Read baseline scenario" "make loadtest-read"
    run_step "Auth burst scenario" "make loadtest-auth"
    run_step "Write + async scenario" "make loadtest-write"
    ;;
  full)
    trap 'make down-loadtest-worker' EXIT
    run_step "Starting full load-test worker stack" "make up-loadtest-worker"
    run_step "Smoke scenario" "make loadtest-smoke"
    run_step "Read baseline scenario" "make loadtest-read"
    run_step "Auth burst scenario" "make loadtest-auth"
    run_step "Write + async scenario" "make loadtest-write"
    run_step "Soak scenario" "make loadtest-soak"
    ;;
  -h|--help|help)
    print_usage
    ;;
  *)
    echo "Unknown mode: ${MODE}" >&2
    echo >&2
    print_usage >&2
    exit 1
    ;;
esac
