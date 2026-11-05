#!/usr/bin/env bash
# Start the ChaiCart arena on http://127.0.0.1:5050 (needs Docker running).
set -euo pipefail
cd "$(dirname "$0")/../arena"
docker compose up -d --build
echo "Waiting for ChaiCart to come up..."
for i in $(seq 1 30); do
  if curl -fs http://127.0.0.1:5050/health >/dev/null 2>&1; then
    echo "ChaiCart is live at http://127.0.0.1:5050"
    exit 0
  fi
  sleep 1
done
echo "ChaiCart did not start. Run: docker compose -f arena/docker-compose.yml logs"
exit 1
