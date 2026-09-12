#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[ROLLBACK] Restoring the last locally built release..."
rm -f .env.local
docker compose up -d --no-build

for url in \
  http://localhost:18080/health \
  http://localhost:19001/health \
  http://localhost:19000/health; do
  curl --fail --silent --show-error "$url" >/dev/null
  echo "[ROLLBACK] $url -> healthy"
done

echo "[ROLLBACK] Previous healthy local release is available."
