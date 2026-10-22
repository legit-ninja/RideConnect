# Shared temp-file tracking for deploy.sh (source, do not execute).
DEPLOY_TEMP_FILES=()

deploy_tempfiles_init() {
  DEPLOY_TEMP_FILES=()
  trap deploy_tempfiles_cleanup EXIT
}

deploy_tempfiles_track() {
  DEPLOY_TEMP_FILES+=("$1")
}

deploy_tempfiles_untrack() {
  local target="$1"
  local next=()
  local f
  for f in "${DEPLOY_TEMP_FILES[@]}"; do
    [[ "$f" == "$target" ]] || next+=("$f")
  done
  DEPLOY_TEMP_FILES=("${next[@]}")
}

deploy_tempfiles_cleanup() {
  local f
  for f in "${DEPLOY_TEMP_FILES[@]:-}"; do
    [[ -n "$f" && -e "$f" ]] && rm -f "$f"
  done
  return 0
}

deploy_mktemp() {
  umask 077
  mktemp
}
