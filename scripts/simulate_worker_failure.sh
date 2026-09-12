#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Simulate a worker outage.
#
# This demonstrates the failure-to-recovery flow required by the assessment.
# The worker container is stopped intentionally, then restarted after a short
# delay so the evaluator can observe queue growth and recovery behavior.
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

printf '[INFO] Stopping worker to simulate infrastructure failure...\n'
docker compose stop worker

printf '[INFO] Worker stopped. Queue will grow while processing is paused.\n'
sleep 10

printf '[INFO] Restarting worker to demonstrate recovery...\n'
docker compose start worker

printf '[INFO] Recovery initiated. Check logs and queue depth to confirm resumed processing.\n'
