#!/usr/bin/env bash
# Package a finished `next build` (output: standalone) into a deployable tarball.
# Usage: scripts/package-frontend-artifact.sh <label> <out-dir>
# Produces <out-dir>/rideconnect-web-<label>-<sha>.tgz (+ .sha256) whose top-level
# folder is app/ (server.js, node_modules, .next/static, public, BUILD_INFO).
# .env files are never included; the server keeps its own app/.env.
set -euo pipefail

LABEL="${1:?label (ci|dev|prod) required}"
OUT="${2:?output dir required}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"
SA="$FRONTEND/.next/standalone"
SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"

[[ -f "$SA/server.js" ]] || { echo "standalone server.js not found under frontend/.next/standalone" >&2; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/app/.next" "$OUT"
cp -a "$SA/." "$STAGE/app/"
cp -a "$FRONTEND/.next/static" "$STAGE/app/.next/static"
if [[ -d "$FRONTEND/public" ]]; then cp -a "$FRONTEND/public" "$STAGE/app/public"; fi
find "$STAGE/app" -name '.env*' -type f -print -delete

{
  echo "label=$LABEL"
  echo "commit=$SHA"
  echo "build_id=$(cat "$FRONTEND/.next/BUILD_ID")"
  echo "node=$(node --version)"
  echo "next=$(node -p "require('$FRONTEND/node_modules/next/package.json').version")"
  echo "sharp=$(node -p "require('$FRONTEND/node_modules/sharp/package.json').version")"
  echo "built_utc=$(date -u +%FT%TZ)"
} > "$STAGE/app/BUILD_INFO"

NAME="rideconnect-web-${LABEL}-${SHA:0:12}.tgz"
tar -C "$STAGE" --owner=0 --group=0 --numeric-owner -czf "$OUT/$NAME" app
( cd "$OUT" && sha256sum "$NAME" > "$NAME.sha256" )
cp "$STAGE/app/BUILD_INFO" "$OUT/BUILD_INFO"
cat "$OUT/BUILD_INFO"
cat "$OUT/$NAME.sha256"
