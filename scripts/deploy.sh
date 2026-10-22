#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"
BACKEND="$ROOT/backend"
CONFIG="$ROOT/deploy/config.sh"

# Load KEY=VALUE lines without bash parameter expansion (safe for passwords containing $).
load_deploy_env() {
  local file="$1"
  local line key val
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      if [[ "$val" =~ ^\"(.*)\"$ ]]; then
        val="${BASH_REMATCH[1]}"
      elif [[ "$val" =~ ^\'(.*)\'$ ]]; then
        val="${BASH_REMATCH[1]}"
      fi
      export "${key}=${val}"
    fi
  done < "$file"
}

usage() {
  echo "Usage: $0 <dev|prod>"
  exit 1
}

[[ $# -eq 1 ]] || usage
TARGET="$1"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG — copy deploy/config.example.sh to deploy/config.sh"
  exit 1
fi

# shellcheck source=/dev/null
source "$CONFIG"

case "$TARGET" in
  dev)
    DOCROOT="$REMOTE_DEV"
    APP_DIR="${REMOTE_DEV}/app"
    API_DIR="${REMOTE_DEV}/api"
    WEB_SERVICE="rideconnect-web-dev"
    API_SERVICE="rideconnect-api-dev"
    WEB_URL="https://dev.phantomequestrian.com"
    API_URL="https://api.dev.phantomequestrian.com"
    DEFAULT_WEB_PORT="3010"
    DEFAULT_API_PORT="8010"
    WEB_UNIT_EXAMPLE="$ROOT/deploy/systemd/rideconnect-web-dev.service.example"
    API_UNIT_EXAMPLE="$ROOT/deploy/systemd/rideconnect-api-dev.service.example"
    ;;
  prod)
    DOCROOT="$REMOTE_PROD"
    APP_DIR="${REMOTE_PROD}/app"
    API_DIR="${REMOTE_PROD}/api"
    WEB_SERVICE="rideconnect-web"
    API_SERVICE="rideconnect-api"
    WEB_URL="https://phantomequestrian.com"
    API_URL="https://api.phantomequestrian.com"
    DEFAULT_WEB_PORT="3009"
    DEFAULT_API_PORT="8009"
    WEB_UNIT_EXAMPLE="$ROOT/deploy/systemd/rideconnect-web.service.example"
    API_UNIT_EXAMPLE="$ROOT/deploy/systemd/rideconnect-api.service.example"
    ;;
  *)
    usage
    ;;
esac

ENV_FILE="$ROOT/deploy/env.${TARGET}.sh"
WEB_PORT="${PORT:-$DEFAULT_WEB_PORT}"
API_PORT="${API_PORT:-$DEFAULT_API_PORT}"

ensure_node() {
  echo "==> Ensuring Node.js on server..."
  local node_info
  node_info="$(ssh "$SSH_HOST" bash -s <<'EOF'
set -euo pipefail
NODE_BIN="$(command -v node || command -v nodejs || true)"
if [[ -z "$NODE_BIN" ]]; then
  echo "Installing Node.js via apt..." >&2
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
  NODE_BIN="$(command -v node || command -v nodejs)"
fi
NODE_VER="$("$NODE_BIN" --version)"
printf '%s %s' "$NODE_BIN" "$NODE_VER"
EOF
)"
  NODE_BIN="${node_info%% *}"
  NODE_VER="${node_info#* }"
  echo "    Node: ${NODE_BIN} (${NODE_VER})"
}

find_standalone_server() {
  local candidates=(
    "$FRONTEND/.next/standalone/server.js"
    "$FRONTEND/.next/standalone/frontend/server.js"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      echo "$(dirname "$c")"
      return 0
    fi
  done
  return 1
}

ensure_app_env() {
  echo "==> Ensuring web + API .env on server..."
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "    Warning: $ENV_FILE missing — create from deploy/env.example.sh"
    return 0
  fi

  local rendered_web="/tmp/rideconnect-web.${TARGET}.env"
  local rendered_api="/tmp/rideconnect-api.${TARGET}.env"
  python3 "$ROOT/scripts/render-app-env.py" next "$ENV_FILE" "$rendered_web"
  python3 "$ROOT/scripts/render-app-env.py" api "$ENV_FILE" "$rendered_api"
  scp "$rendered_web" "$SSH_HOST:/tmp/rideconnect-web.${TARGET}.env"
  scp "$rendered_api" "$SSH_HOST:/tmp/rideconnect-api.${TARGET}.env"
  ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
sudo mv /tmp/rideconnect-web.${TARGET}.env '${APP_DIR}/.env'
sudo chown www-data:www-data '${APP_DIR}/.env'
sudo chmod 640 '${APP_DIR}/.env'
sudo mv /tmp/rideconnect-api.${TARGET}.env '${API_DIR}/.env'
sudo chown www-data:www-data '${API_DIR}/.env'
sudo chmod 640 '${API_DIR}/.env'
# Persistent uploads outside rsync overwrite of api tree code
sudo mkdir -p '${DOCROOT}/uploads'
sudo chown www-data:www-data '${DOCROOT}/uploads'
if [[ ! -e '${API_DIR}/uploads' ]]; then
  sudo ln -sfn '${DOCROOT}/uploads' '${API_DIR}/uploads'
fi
EOF
  rm -f "$rendered_web" "$rendered_api"
}

ensure_api_venv() {
  echo "==> Ensuring API Python venv + dependencies on server..."
  ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
cd '${API_DIR}'
VENV_PY='${API_DIR}/.venv/bin/python'
need_venv=0
if [[ ! -x "\$VENV_PY" ]]; then
  need_venv=1
elif ! sudo -u www-data "\$VENV_PY" -m pip --version >/dev/null 2>&1; then
  need_venv=1
fi
if [[ "\$need_venv" -eq 1 ]]; then
  echo "    Recreating API venv (missing or incomplete)..."
  sudo rm -rf '${API_DIR}/.venv'
  sudo -u www-data python3 -m venv '${API_DIR}/.venv'
fi
# Absolute path + python -m pip (incomplete venvs lack bin/pip; sudo PATH quirks)
sudo -u www-data "\$VENV_PY" -m pip install --upgrade pip -q
sudo -u www-data "\$VENV_PY" -m pip install -r '${API_DIR}/requirements.txt' -q
if [[ -f '${API_DIR}/.env' ]]; then
  # Do not bash-source .env — secrets may contain # ^ $ etc. Alembic/pydantic load .env from cwd.
  sudo -u www-data bash -c 'cd "${API_DIR}" && exec .venv/bin/alembic upgrade head' || {
    echo "WARNING: alembic upgrade failed — check DATABASE_URL / Postgres" >&2
  }
fi
EOF
}

ensure_runtime() {
  ensure_node
  echo "==> Ensuring Apache proxy + systemd runtime..."
  scp "$ROOT/deploy/apache/pe-web-${TARGET}.conf" "$SSH_HOST:/tmp/pe-web-${TARGET}.conf"
  scp "$ROOT/deploy/apache/pe-api-${TARGET}.conf" "$SSH_HOST:/tmp/pe-api-${TARGET}.conf"
  scp "$WEB_UNIT_EXAMPLE" "$SSH_HOST:/tmp/${WEB_SERVICE}.service"
  scp "$API_UNIT_EXAMPLE" "$SSH_HOST:/tmp/${API_SERVICE}.service"
  ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
NODE_BIN="\$(command -v node || command -v nodejs)"
sudo sed -i "s|ExecStart=.*node server.js|ExecStart=\${NODE_BIN} server.js|" /tmp/${WEB_SERVICE}.service
# Next.js must listen on loopback only (Apache is the only client).
if ! grep -q "^Environment=HOSTNAME=127.0.0.1\$" /tmp/${WEB_SERVICE}.service; then
  sudo sed -i "/^Environment=PORT=/a Environment=HOSTNAME=127.0.0.1" /tmp/${WEB_SERVICE}.service
fi
grep -q "^Environment=HOSTNAME=127.0.0.1\$" /tmp/${WEB_SERVICE}.service || { echo "web unit is missing HOSTNAME=127.0.0.1" >&2; exit 1; }
sudo cp /tmp/pe-web-${TARGET}.conf /etc/apache2/sites-available/pe-web-${TARGET}.conf
sudo cp /tmp/pe-api-${TARGET}.conf /etc/apache2/sites-available/pe-api-${TARGET}.conf
sudo a2ensite pe-web-${TARGET}.conf pe-api-${TARGET}.conf 2>/dev/null || true
sudo cp /tmp/${WEB_SERVICE}.service /etc/systemd/system/${WEB_SERVICE}.service
sudo cp /tmp/${API_SERVICE}.service /etc/systemd/system/${API_SERVICE}.service
rm -f /tmp/pe-web-${TARGET}.conf /tmp/pe-api-${TARGET}.conf \
      /tmp/${WEB_SERVICE}.service /tmp/${API_SERVICE}.service
if [[ "${TARGET}" == "prod" ]]; then
  # Legacy WordPress vhost shares ServerName — disable on cutover.
  for legacy in phantomequestrian.com.conf phantomequestrian-le-ssl.conf 000-phantomequestrian.conf; do
    if [[ -e "/etc/apache2/sites-enabled/\${legacy}" ]]; then
      echo "Disabling legacy WordPress vhost: \${legacy}"
      sudo a2dissite "\${legacy}" 2>/dev/null || true
      sudo rm -f "/etc/apache2/sites-enabled/\${legacy}"
    fi
  done
fi
sudo a2enmod ssl headers proxy proxy_http 2>/dev/null || true
sudo apachectl configtest
sudo systemctl reload apache2
sudo systemctl daemon-reload
sudo systemctl enable ${WEB_SERVICE} ${API_SERVICE}
sudo systemctl restart ${WEB_SERVICE} ${API_SERVICE}
EOF
}

verify_deploy() {
  local verify_json attempt max_attempts=20

  for attempt in $(seq 1 "$max_attempts"); do
    verify_json="$(ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
WEB_PORT="${WEB_PORT}"
API_PORT="${API_PORT}"
WEB_SERVICE="${WEB_SERVICE}"
API_SERVICE="${API_SERVICE}"
WEB_ACTIVE="\$(systemctl is-active "\${WEB_SERVICE}" 2>/dev/null || echo missing)"
API_ACTIVE="\$(systemctl is-active "\${API_SERVICE}" 2>/dev/null || echo missing)"
WEB_LISTEN=0
API_LISTEN=0
ss -tln 2>/dev/null | grep -q ":\${WEB_PORT} " && WEB_LISTEN=1 || true
ss -tln 2>/dev/null | grep -q ":\${API_PORT} " && API_LISTEN=1 || true
WEB_CODE="\$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:\${WEB_PORT}/" 2>/dev/null || true)"
WEB_CODE="\${WEB_CODE:-000}"
API_CODE="\$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:\${API_PORT}/health" 2>/dev/null || true)"
API_CODE="\${API_CODE:-000}"
python3 -c "import json; print(json.dumps({
  'webActive': '\${WEB_ACTIVE}',
  'apiActive': '\${API_ACTIVE}',
  'webListen': int('\${WEB_LISTEN}'),
  'apiListen': int('\${API_LISTEN}'),
  'webCode': '\${WEB_CODE}',
  'apiCode': '\${API_CODE}',
}))"
EOF
)"

    local web_active api_active web_listen api_listen web_code api_code
    web_active="$(printf '%s' "$verify_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('webActive',''))")"
    api_active="$(printf '%s' "$verify_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('apiActive',''))")"
    web_listen="$(printf '%s' "$verify_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('webListen',0))")"
    api_listen="$(printf '%s' "$verify_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('apiListen',0))")"
    web_code="$(printf '%s' "$verify_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('webCode',''))")"
    api_code="$(printf '%s' "$verify_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('apiCode',''))")"

    if [[ "$web_active" == "active" && "$api_active" == "active" \
       && "$web_listen" == "1" && "$api_listen" == "1" \
       && "$web_code" == "200" && "$api_code" == "200" ]]; then
      return 0
    fi

    if [[ "$attempt" -lt "$max_attempts" ]]; then
      sleep 1
    fi
  done

  echo "Deploy verification failed after ${max_attempts} attempts:"
  echo "$verify_json" | python3 -m json.tool
  return 1
}

# --- build + sync ---

if [[ -f "$ENV_FILE" ]]; then
  echo "==> Loaded env from deploy/env.${TARGET}.sh"
  set -a
  load_deploy_env "$ENV_FILE"
  set +a
else
  echo "    Warning: deploy/env.${TARGET}.sh not found — fill before production use."
fi

# Target ports are defined by Apache/systemd units — never trust a mismatched PORT in env.
if [[ -n "${PORT:-}" && "$PORT" != "$DEFAULT_WEB_PORT" ]]; then
  echo "    WARNING: env PORT=$PORT overridden to $DEFAULT_WEB_PORT for target=$TARGET"
fi
if [[ -n "${API_PORT:-}" && "$API_PORT" != "$DEFAULT_API_PORT" ]]; then
  echo "    WARNING: env API_PORT=$API_PORT overridden to $DEFAULT_API_PORT for target=$TARGET"
fi
export PORT="$DEFAULT_WEB_PORT"
export API_PORT="$DEFAULT_API_PORT"
export API_INTERNAL_URL="http://127.0.0.1:${DEFAULT_API_PORT}"
WEB_PORT="$DEFAULT_WEB_PORT"
API_PORT="$DEFAULT_API_PORT"

echo "==> Building Next.js standalone..."
cd "$FRONTEND"
npm ci
npm run build

STANDALONE_DIR="$(find_standalone_server)" || {
  echo "Build failed: standalone server.js not found under frontend/.next/standalone"
  exit 1
}
echo "    Standalone root: ${STANDALONE_DIR}"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_BASE="$(dirname "$DOCROOT")/_backups/$(basename "$DOCROOT")"
echo "==> Backing up remote app+api to ${BACKUP_BASE}/${STAMP}"
ssh "$SSH_HOST" "sudo mkdir -p '${BACKUP_BASE}/${STAMP}/app' '${BACKUP_BASE}/${STAMP}/api' && \
  if [ -d '${APP_DIR}' ]; then sudo rsync -a '${APP_DIR}/' '${BACKUP_BASE}/${STAMP}/app/'; fi && \
  if [ -d '${API_DIR}' ] && [ -f '${API_DIR}/requirements.txt' ]; then sudo rsync -a --exclude '.venv' --exclude 'uploads' '${API_DIR}/' '${BACKUP_BASE}/${STAMP}/api/'; fi"

echo "==> Syncing web standalone + API source to staging..."
ssh "$SSH_HOST" "mkdir -p ${REMOTE_STAGING}/app ${REMOTE_STAGING}/static ${REMOTE_STAGING}/public ${REMOTE_STAGING}/api"
rsync -avz --delete "$STANDALONE_DIR/" "$SSH_HOST:${REMOTE_STAGING}/app/"
rsync -avz --delete "$FRONTEND/.next/static/" "$SSH_HOST:${REMOTE_STAGING}/static/"
if [[ -d "$FRONTEND/public" ]]; then
  rsync -avz --delete "$FRONTEND/public/" "$SSH_HOST:${REMOTE_STAGING}/public/"
fi
rsync -avz --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude 'uploads' \
  --exclude '.env' \
  "$BACKEND/" "$SSH_HOST:${REMOTE_STAGING}/api/"

echo "==> Publishing on server..."
REMOTE_STAGING_RESOLVED="$(ssh "$SSH_HOST" "eval echo ${REMOTE_STAGING}")"
ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
STAGING_DIR="${REMOTE_STAGING_RESOLVED}"
sudo mkdir -p '${APP_DIR}' '${API_DIR}'
sudo rsync -a --delete "\${STAGING_DIR}/app/" '${APP_DIR}/'
sudo mkdir -p '${APP_DIR}/.next'
sudo rsync -a --delete "\${STAGING_DIR}/static/" '${APP_DIR}/.next/static/'
if [[ -d "\${STAGING_DIR}/public" ]]; then
  sudo rsync -a --delete "\${STAGING_DIR}/public/" '${APP_DIR}/public/'
fi
# Preserve existing .venv across publish
if [[ -d '${API_DIR}/.venv' ]]; then
  sudo mv '${API_DIR}/.venv' '/tmp/rideconnect-api-venv.${STAMP}'
fi
sudo rsync -a --delete --exclude '.venv' --exclude 'uploads' --exclude '.env' \
  "\${STAGING_DIR}/api/" '${API_DIR}/'
if [[ -d '/tmp/rideconnect-api-venv.${STAMP}' ]]; then
  sudo mv '/tmp/rideconnect-api-venv.${STAMP}' '${API_DIR}/.venv'
fi
sudo chown -R www-data:www-data '${APP_DIR}' '${API_DIR}'
test -f '${APP_DIR}/server.js'
test -f '${API_DIR}/requirements.txt'
EOF

ensure_app_env
ensure_api_venv

echo "==> Ensuring runtime (Apache + systemd)..."
ensure_runtime

echo "==> Verifying deploy (web :${WEB_PORT}, api :${API_PORT})..."
if ! verify_deploy; then
  echo "ERROR: Files synced but services are not healthy."
  echo "Check: systemctl status ${WEB_SERVICE} ${API_SERVICE}"
  echo "       curl -I http://127.0.0.1:${WEB_PORT}/"
  echo "       curl -I http://127.0.0.1:${API_PORT}/health"
  exit 1
fi

echo "==> Deployed web ${WEB_URL}"
echo "==> Deployed api ${API_URL}"
echo "Rollback: ssh ${SSH_HOST} \"sudo rsync -a ${BACKUP_BASE}/${STAMP}/app/ ${APP_DIR}/ && sudo rsync -a ${BACKUP_BASE}/${STAMP}/api/ ${API_DIR}/ && sudo systemctl restart ${WEB_SERVICE} ${API_SERVICE}\""
