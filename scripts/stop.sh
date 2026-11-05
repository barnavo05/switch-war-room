#!/usr/bin/env bash
# Stop the ChaiCart arena.
set -euo pipefail
cd "$(dirname "$0")/../arena"
docker compose down
