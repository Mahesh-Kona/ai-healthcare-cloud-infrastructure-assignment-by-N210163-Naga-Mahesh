#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Simulate an external EHR dependency outage.
#
# This script intentionally stops the mock EHR container to demonstrate that
# internal services remain reachable while the external dependency becomes
# unavailable. The evaluator can then observe retry or failure behavior.
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

printf '[INFO] Stopping EHR mock to simulate external dependency failure...\n'
docker compose stop ehr-mock

printf '[INFO] EHR mock stopped. Observe timeout, retry, or failure handling in the worker.\n'
sleep 10

printf '[INFO] Restarting EHR mock to demonstrate recovery...\n'
docker compose start ehr-mock

printf '[INFO] Recovery completed.\n'
