#!/usr/bin/env sh
# Wait until DATABASE_URL is reachable (snap Docker may need host.docker.internal routing).
set -eu

attempts="${DB_WAIT_ATTEMPTS:-30}"
sleep_secs="${DB_WAIT_SLEEP:-2}"

echo "Waiting for Postgres via DATABASE_URL (max ${attempts} attempts)..."

python - <<'PY'
import os
import sys
import time

import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    print("DATABASE_URL is not set", file=sys.stderr)
    sys.exit(1)

attempts = int(os.environ.get("DB_WAIT_ATTEMPTS", "30"))
sleep_secs = float(os.environ.get("DB_WAIT_SLEEP", "2"))

for attempt in range(1, attempts + 1):
    try:
        conn = psycopg2.connect(url, connect_timeout=3)
        conn.close()
        print(f"Postgres ready (attempt {attempt}/{attempts})")
        sys.exit(0)
    except psycopg2.OperationalError as exc:
        print(f"Postgres not ready (attempt {attempt}/{attempts}): {exc}")
        if attempt < attempts:
            time.sleep(sleep_secs)

print(f"Postgres not reachable after {attempts} attempts", file=sys.stderr)
sys.exit(1)
PY
