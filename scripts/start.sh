#!/usr/bin/env bash
# Start the ChaiCart arena on http://127.0.0.1:5050 (needs Docker running).
set -euo pipefail
cd "$(dirname "$0")/../arena"
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Open Docker Desktop, wait for 'Engine running', then try again."
  exit 1
fi
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
