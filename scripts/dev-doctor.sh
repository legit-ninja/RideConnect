#!/usr/bin/env bash
# Diagnose RideConnect docker-compose dev environment.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

H1_FAIL=false

# Snap Docker often cannot stop containers (permission denied).
if docker-compose ps -a 2>/dev/null | rg -qi 'permission denied|Error while Stopping'; then
  H1_FAIL=true
fi

WEB_PORTS=$(docker port rideconnect-web-1 3000 2>/dev/null || true)
API_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo "000")
WEB_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null || echo "000")

echo "=== RideConnect dev doctor ==="
docker-compose ps 2>/dev/null || true
echo ""
echo "API health:  http://localhost:8000/health → HTTP $API_CODE"
echo "Web home:    http://localhost:3000 → HTTP $WEB_CODE"
echo ""

if [[ -z "$WEB_PORTS" ]] && docker ps --format '{{.Names}}' 2>/dev/null | rg -q '^rideconnect-web-1$'; then
  echo "NOTE: web container is running but port 3000 is not published to the host."
  echo "      Run: make reset-docker  (or sudo snap restart docker && docker-compose down && docker-compose up --build -d)"
  echo ""
fi

if [[ "$H1_FAIL" == true ]]; then
  echo "ISSUE: Snap Docker cannot stop containers (permission denied)."
  echo "FIX:   make reset-docker"
  echo ""
  echo "WORKAROUND (API+DB in Docker, frontend on host):"
  echo "       make dev-split"
  exit 1
fi

if [[ "$API_CODE" == "200" && "$WEB_CODE" != "200" ]]; then
  echo "API is up; web is not reachable on :3000."
  echo "Try: docker-compose up -d --no-recreate web"
  echo "Or: make dev-split"
  exit 1
fi

if [[ "$API_CODE" == "200" && "$WEB_CODE" == "200" ]]; then
  echo "All services look healthy."
  exit 0
fi

echo "Run: make up"
exit 1
