#!/usr/bin/env bash
set -euo pipefail

# Start the local cloud simulation environment.
# This script is intentionally simple and readable for coursework demonstrations.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

printf '\n[INFO] Starting cloud simulation environment...\n'
docker compose up --build -d

printf '\n[INFO] Services are starting. Checking health...\n'

for i in {1..30}; do
  if docker compose ps | grep -q 'healthy'; then
    break
  fi
  sleep 2
done

printf '\n[INFO] Environment started.\n'
printf '[INFO] API: http://localhost:18080\n'
printf '[INFO] Prometheus: http://localhost:19090\n'
printf '[INFO] Grafana: http://localhost:13000\n'
