#!/usr/bin/env bash
# Put the arena back to its original, fully vulnerable state and clear the
# scoreboard. Run this before every new match or demo recording.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cp "$ROOT/arena/pristine/app.py" "$ROOT/arena/app/app.py"
rm -f "$ROOT/arena/app/data/chaicart.db"
python3 "$ROOT/referee/scoreboard.py" reset
# Restart so the fresh database gets created.
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^chaicart-arena$'; then
  docker restart chaicart-arena >/dev/null
  sleep 2
fi
echo "Arena reset. All 5 vulnerabilities are back. Scoreboard cleared."
