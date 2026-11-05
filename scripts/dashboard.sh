#!/usr/bin/env bash
# Open the live spectator dashboard (default http://127.0.0.1:8099).
# Run this in a second terminal while the arena and a match are running.
# Port taken? Use another one:  DASHBOARD_PORT=9000 ./scripts/dashboard.sh
set -euo pipefail
cd "$(dirname "$0")/.."
DASHBOARD_PORT="${DASHBOARD_PORT:-8099}" exec python3 dashboard/serve.py
