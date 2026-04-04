#!/usr/bin/env bash

set -euo pipefail

python -m app.jobs.replay_dead_letter_queue
