#!/usr/bin/env bash
# Run alembic or seed against Docker Postgres, with host fallback when api is down.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOCAL_DATABASE_URL="${LOCAL_DATABASE_URL:-postgresql://rideconnect:rideconnect@localhost:5432/rideconnect}"
TASK="${1:?usage: db-task.sh migrate|seed}"

API_HEALTHY=false
if curl -sf --max-time 2 http://localhost:8000/health >/dev/null 2>&1; then
  API_HEALTHY=true
fi

DB_HOST_OK=false
if command -v pg_isready >/dev/null 2>&1; then
  pg_isready -h localhost -p 5432 -U rideconnect -d rideconnect >/dev/null 2>&1 && DB_HOST_OK=true
elif python3 -c "import socket; s=socket.create_connection(('localhost',5432),2); s.close()" 2>/dev/null; then
  DB_HOST_OK=true
fi

_run_host() {
  local py="python3"
  if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
    py="$ROOT/backend/.venv/bin/python"
  fi
  export DATABASE_URL="$LOCAL_DATABASE_URL"
  export SEED_DEV_DATA=true
  cd "$ROOT/backend"
  case "$TASK" in
    migrate) "$py" -m alembic upgrade head ;;
    seed) "$py" -m app.seed_dev ;;
    *) echo "unknown task: $TASK" >&2; exit 1 ;;
  esac
}

if [[ "$API_HEALTHY" == true ]]; then
  case "$TASK" in
    migrate) timeout 60 docker-compose exec api alembic upgrade head ;;
    seed) timeout 60 docker-compose exec -e SEED_DEV_DATA=true api python -m app.seed_dev ;;
  esac
  exit 0
fi

if [[ "$DB_HOST_OK" == true ]]; then
  echo "api not healthy; using host fallback ($LOCAL_DATABASE_URL)"
  _run_host
  exit 0
fi

echo "ERROR: API is not healthy and Postgres is not reachable on localhost:5432." >&2
echo "Start the stack first: make up   (or API+DB only: make dev-split)" >&2
echo "If api keeps crashing, run: make doctor" >&2
exit 1
