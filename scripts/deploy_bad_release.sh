#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Demonstrate a failed deployment scenario.
#
# This script intentionally uses a known bad configuration value in a simulated
# deployment to show how the pipeline can stop unsafe releases before traffic is
# shifted to broken versions.
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

cat <<'EOF' > .env.local
DB_PASSWORD=bad-secret-value
EOF

printf '[INFO] A deliberately unsafe configuration is now active.\n'
printf '[INFO] Run the pipeline to observe that the release should be blocked.\n'
