#!/usr/bin/env bash
# Ensure system PostgreSQL on the deploy host and create the app role/database.
# Docker is not available on the deploy host — use apt postgresql (same pattern as host MySQL for UU/SS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/deploy/config.sh"

usage() {
  echo "Usage: $0 <dev|prod>"
  exit 1
}

[[ $# -eq 1 ]] || usage
TARGET="$1"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG — copy deploy/config.sh.example to deploy/config.sh"
  exit 1
fi

# shellcheck source=/dev/null
source "$CONFIG"

ENV_FILE="$ROOT/deploy/env.${TARGET}.sh"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy deploy/env.example.sh and set DATABASE_URL"
  exit 1
fi

# Parse DATABASE_URL without echoing the password.
eval "$(python3 - "$ENV_FILE" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
url = None
for line in text.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("DATABASE_URL="):
        url = line.split("=", 1)[1].strip()
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1]
        break
if not url:
    raise SystemExit("DATABASE_URL missing from env file")
m = re.match(
    r"postgresql(?:\+[^:]+)?://([^:]+):([^@]*)@([^:/]+):?(\d+)?/([^?\s]+)",
    url,
)
if not m:
    raise SystemExit(f"Could not parse DATABASE_URL")
user, password, host, port, db = m.group(1), m.group(2), m.group(3), m.group(4) or "5432", m.group(5)
# Export shell-safe assignments
import shlex
print(f"PG_USER={shlex.quote(user)}")
print(f"PG_PASSWORD={shlex.quote(password)}")
print(f"PG_HOST={shlex.quote(host)}")
print(f"PG_PORT={shlex.quote(port)}")
print(f"PG_DB={shlex.quote(db)}")
PY
)"

if [[ "$PG_HOST" != "127.0.0.1" && "$PG_HOST" != "localhost" ]]; then
  echo "Refusing to manage non-local Postgres host: $PG_HOST"
  exit 1
fi

echo "==> Ensuring PostgreSQL is installed and running on ${SSH_HOST}..."
ssh "$SSH_HOST" bash -s <<'EOF'
set -euo pipefail
if ! dpkg -s postgresql >/dev/null 2>&1 && ! dpkg -s postgresql-16 >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib
fi
sudo systemctl enable --now postgresql
# Wait briefly for listen
for i in $(seq 1 20); do
  if ss -tln | grep -q ':5432 '; then
    break
  fi
  sleep 0.5
done
ss -tln | grep -q ':5432 ' || { echo "PostgreSQL is not listening on :5432"; exit 1; }
EOF

echo "==> Ensuring role + database ${PG_DB} (user ${PG_USER})..."
ssh "$SSH_HOST" \
  "PG_USER=$(printf '%q' "$PG_USER") PG_PASSWORD=$(printf '%q' "$PG_PASSWORD") PG_DB=$(printf '%q' "$PG_DB") bash -s" <<'EOF'
set -euo pipefail
# Dollar-quote password so special characters cannot break SQL.
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${PG_USER}') THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', '${PG_USER}', '${PG_PASSWORD}');
  ELSE
    EXECUTE format('ALTER ROLE %I WITH LOGIN PASSWORD %L', '${PG_USER}', '${PG_PASSWORD}');
  END IF;
END
\$\$;
SQL

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${PG_DB}'" | grep -q 1; then
  sudo -u postgres createdb -O "${PG_USER}" "${PG_DB}"
fi
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "GRANT ALL PRIVILEGES ON DATABASE \"${PG_DB}\" TO \"${PG_USER}\";"
sudo -u postgres psql -v ON_ERROR_STOP=1 -d "${PG_DB}" -c "GRANT ALL ON SCHEMA public TO \"${PG_USER}\";"
EOF

echo "==> Verifying TCP login on 127.0.0.1:5432..."
ssh "$SSH_HOST" \
  "PG_USER=$(printf '%q' "$PG_USER") PG_PASSWORD=$(printf '%q' "$PG_PASSWORD") PG_DB=$(printf '%q' "$PG_DB") bash -s" <<'EOF'
set -euo pipefail
# peer auth is default for local socket; force TCP so password auth matches DATABASE_URL
export PGPASSWORD="${PG_PASSWORD}"
psql -h 127.0.0.1 -p 5432 -U "${PG_USER}" -d "${PG_DB}" -c 'SELECT 1 AS ok;' >/dev/null
echo "TCP auth OK"
EOF

echo "==> Postgres ready for ${TARGET}: postgresql://${PG_USER}:***@127.0.0.1:5432/${PG_DB}"
echo "Update deploy/env.${TARGET}.sh DATABASE_URL to use port 5432 if it still points at 5439/5440."
