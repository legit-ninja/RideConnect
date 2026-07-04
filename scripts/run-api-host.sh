#!/usr/bin/env bash
# Run FastAPI on the host (use when Docker api cannot reach db).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

set -a
# shellcheck disable=SC1091
source "$ROOT/.env" 2>/dev/null || true
set +a
export DATABASE_URL="postgresql://rideconnect:rideconnect@localhost:5432/rideconnect"

PY="python3"
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  PY="$ROOT/backend/.venv/bin/python"
fi

echo "Starting API on http://localhost:8000 (DATABASE_URL=$DATABASE_URL)"
"$PY" -m alembic upgrade head
exec "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
