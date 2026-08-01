#!/usr/bin/env bash
# One-time host setup on jlee@192.168.3.3 — run after DNS + cert expand.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/deploy/config.sh"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG — copy deploy/config.example.sh to deploy/config.sh"
  exit 1
fi

# shellcheck source=/dev/null
source "$CONFIG"

echo "==> Creating document roots..."
ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
sudo mkdir -p ${REMOTE_PROD}/{app,api,uploads,_wordpress_backup} \
             ${REMOTE_DEV}/{app,api,uploads}
sudo chown -R jlee:www-data ${REMOTE_PROD} ${REMOTE_DEV}
sudo chmod -R 775 ${REMOTE_PROD} ${REMOTE_DEV}
EOF

echo "==> Installing Postgres compose file (prod + dev)..."
scp "$ROOT/deploy/docker-compose.postgres.yml" \
  "$SSH_HOST:/tmp/rideconnect-docker-compose.postgres.yml"
ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
sudo cp /tmp/rideconnect-docker-compose.postgres.yml ${REMOTE_PROD}/docker-compose.postgres.yml
sudo cp /tmp/rideconnect-docker-compose.postgres.yml ${REMOTE_DEV}/docker-compose.postgres.yml
rm -f /tmp/rideconnect-docker-compose.postgres.yml
EOF

echo "==> Installing Apache vhost configs..."
for conf in pe-web-prod pe-web-dev pe-api-prod pe-api-dev pe-shop-prod pe-shop-dev; do
  scp "$ROOT/deploy/apache/${conf}.conf" "$SSH_HOST:/tmp/${conf}.conf"
done
ssh "$SSH_HOST" bash -s <<'EOF'
set -euo pipefail
for conf in pe-web-prod pe-web-dev pe-api-prod pe-api-dev pe-shop-prod pe-shop-dev; do
  sudo cp "/tmp/${conf}.conf" "/etc/apache2/sites-available/${conf}.conf"
  sudo a2ensite "${conf}.conf" 2>/dev/null || true
  rm -f "/tmp/${conf}.conf"
done
sudo a2enmod ssl headers proxy proxy_http 2>/dev/null || true
sudo apachectl configtest
sudo systemctl reload apache2
EOF

echo "==> Ensuring Node.js + Python3 venv tooling..."
ssh "$SSH_HOST" bash -s <<'EOF'
set -euo pipefail
if ! command -v node >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
fi
if ! python3 -c "import venv" 2>/dev/null; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv python3-pip
fi
command -v docker >/dev/null 2>&1 || echo "WARNING: docker not found — install before starting Postgres"
EOF

echo "==> Server setup complete."
echo
echo "Next steps:"
echo "  1. Expand certs (on server as root): sudo /root/renew-apache-certs.sh"
echo "     Include: phantomequestrian.com www shop shop.dev api api.dev (and www/dev)"
echo "  2. Bootstrap Postgres (system package — Docker is not on this host):"
echo "       ./scripts/server-db.sh dev"
echo "       ./scripts/server-db.sh prod   # when ready; use a separate DB name"
echo "  3. Copy deploy/env.example.sh → deploy/env.{dev,prod}.sh and fill secrets"
echo "     DATABASE_URL must use 127.0.0.1:5432 (not Docker ports 5439/5440)"
echo "  4. Deploy: ./scripts/deploy.sh dev"
echo "  5. Before prod cutover: backup WordPress, then ./scripts/deploy.sh prod"
