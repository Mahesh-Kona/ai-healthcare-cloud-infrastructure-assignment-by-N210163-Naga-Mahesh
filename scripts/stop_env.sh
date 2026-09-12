#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

printf '\n[INFO] Stopping cloud simulation environment...\n'
docker compose down

printf '\n[INFO] Environment stopped.\n'
