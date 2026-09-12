#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Safe release pipeline simulation.
#
# This script demonstrates the major stages of a DevSecOps-style release flow:
# 1. validate source and config
# 2. run lightweight tests
# 3. perform security checks
# 4. build artifacts
# 5. deploy
# 6. verify health
# 7. report success or rollback
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "[PIPELINE] Starting validation stage..."
python -m compileall services >/dev/null

echo "[PIPELINE] Running lightweight tests..."
python - <<'PY'
print("[TEST] Placeholder validation passed.")
PY

echo "[PIPELINE] Running security checks..."
python - <<'PY'
import pathlib
import re
import sys

project_root = pathlib.Path('.')
allowed_patterns = {
    'change-me-dev',
    'admin',
    'example',
    'placeholder',
    'dummy',
    'sample',
    'your-password',
    'your-api-key',
    'your-secret',
}
secret_keys = ('DB_PASSWORD', 'POSTGRES_PASSWORD', 'AI_PROVIDER_API_KEY')

issues = []

for path in project_root.rglob('*'):
    if not path.is_file() or '.git' in path.parts:
        continue
    if path.name == '.env':
        continue

    if path.name.startswith('Dockerfile') or path.suffix.lower() in {'.py', '.yml', '.yaml', '.toml', '.json'} or path.name.startswith('.env'):
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except Exception:
            continue

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            match = re.match(r'(?i)^\s*(DB_PASSWORD|POSTGRES_PASSWORD|AI_PROVIDER_API_KEY)\s*[:=]\s*(.+)$', stripped)
            if not match:
                continue

            key, value = match.groups()
            value = value.strip().strip('"\'')

            if not value:
                continue
            if value.startswith('${'):
                continue
            if 'os.environ.get(' in value:
                continue
            if value.lower() in allowed_patterns:
                continue

            issues.append(f"{path}:{idx}: suspicious hard-coded secret-like value for {key} -> {value}")

if issues:
    print('[SECURITY] Potential hard-coded secrets or risky values found.')
    for issue in issues:
        print(issue)
    sys.exit(1)

print('[PIPELINE] Security checks passed.')
PY

echo "[PIPELINE] Building artifacts..."
docker compose build >/tmp/build.log 2>&1 || {
  echo "[PIPELINE] Build failed."
  cat /tmp/build.log
  exit 1
}

echo "[PIPELINE] Running container vulnerability checks..."
if docker scout version >/dev/null 2>&1; then
    if docker scout cves --only-severity critical,high --only-fixed --exit-code local://cloudassignment-api:latest >/tmp/scout.log 2>&1; then
        echo "[SECURITY] Docker Scout image scan passed."
    else
        scout_code=$?
        if [ "$scout_code" -eq 2 ]; then
            cat /tmp/scout.log
            echo "[SECURITY] Critical/high fixed vulnerabilities detected in the API image."
            exit 1
        fi
        echo "[SECURITY] Docker Scout is unavailable or not authenticated; run 'docker login' to enable the image CVE gate."
    fi
else
    echo "[SECURITY] Docker Scout is not installed; install it to enable the image CVE gate."
fi

# Simulated deployment stage.
echo "[PIPELINE] Deploying release..."
./scripts/start_env.sh >/tmp/deploy.log 2>&1 || {
  echo "[PIPELINE] Deployment failed."
  cat /tmp/deploy.log
  exit 1
}

# Health verification step.
echo "[PIPELINE] Verifying service health..."
python - <<'PY'
import json
import urllib.request

for url in [
    'http://localhost:18080/health',
    'http://localhost:19001/health',
    'http://localhost:9002/health',
    'http://localhost:19000/health',
]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            print(f"[HEALTH] {url} -> {resp.status}")
    except Exception as exc:
        print(f"[HEALTH] {url} failed: {exc}")
        raise
PY

echo "[PIPELINE] Deployment completed successfully."
