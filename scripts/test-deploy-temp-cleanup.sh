#!/usr/bin/env bash
# Local harness: deploy temp-file tracking must not leave RETURN traps or unbound vars.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=deploy-tempfiles.sh
source "$ROOT/scripts/deploy-tempfiles.sh"
deploy_tempfiles_init

simulate_ensure_app_env() {
  local rendered_web rendered_api
  rendered_web="$(deploy_mktemp)"
  rendered_api="$(deploy_mktemp)"
  deploy_tempfiles_track "$rendered_web"
  deploy_tempfiles_track "$rendered_api"
  [[ "$(stat -c '%a' "$rendered_web")" == 600 ]] || {
    echo "expected mode 600 on $rendered_web" >&2
    exit 1
  }
  echo "data" >"$rendered_web"
  rm -f "$rendered_web" "$rendered_api"
  deploy_tempfiles_untrack "$rendered_web"
  deploy_tempfiles_untrack "$rendered_api"
}

simulate_ensure_runtime() {
  local rendered_web_vhost rendered_api_vhost
  rendered_web_vhost="$(deploy_mktemp)"
  rendered_api_vhost="$(deploy_mktemp)"
  deploy_tempfiles_track "$rendered_web_vhost"
  deploy_tempfiles_track "$rendered_api_vhost"
  rm -f "$rendered_web_vhost" "$rendered_api_vhost"
  deploy_tempfiles_untrack "$rendered_web_vhost"
  deploy_tempfiles_untrack "$rendered_api_vhost"
}

simulate_ensure_app_env
simulate_ensure_runtime
echo "deploy temp cleanup harness: ok"
