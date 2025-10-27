#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$SCRIPT_DIR
DEFAULT_CONFIG_DIR="$PROJECT_ROOT/config/deploy"
DEFAULT_COMPOSE_FILE="deploy/docker-compose.yml"
DEFAULT_ENV_FILE="deploy/.env"

usage() {
  cat <<'USAGE'
Usage: deploy.sh <environment> [options]

Options:
  -c, --config <file>    Path to a specific deploy configuration file.
  -m, --mode <mode>      One of deploy (default), pull, build, or down.
  --arch <arch>          Limit deployment to the provided architecture (amd64 or arm64). Repeatable.
  --skip-sync            Do not synchronise project files to the remote hosts.
  --skip-build           Skip docker compose build steps even if enabled.
  --skip-pull            Skip docker compose pull steps even if enabled.
  -h, --help             Show this help message.

Examples:
  ./deploy.sh production
  ./deploy.sh staging --mode pull --skip-build
  ./deploy.sh prod --arch arm64 --arch amd64
USAGE
}

log() {
  local level=$1
  shift
  printf '[%s] %s\n' "$level" "$*"
}

abort() {
  log "ERROR" "$*"
  exit 1
}

on_error() {
  local exit_code=$1
  local line_no=$2
  log "ERROR" "Deployment script failed at line ${line_no} (exit code ${exit_code})."
}

trap 'on_error $? $LINENO' ERR

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    abort "Required command '$1' is not available on PATH."
  fi
}

parse_bool() {
  local value=${1:-false}
  case "${value,,}" in
    1|true|yes|y|on) echo "true" ;;
    *) echo "false" ;;
  esac
}

build_ssh_target() {
  local host=$1
  if [[ -n ${SSH_USER:-} ]]; then
    printf '%s@%s' "$SSH_USER" "$host"
  else
    printf '%s' "$host"
  fi
}

split_csv() {
  local csv=$1
  local -n _result=$2
  _result=()
  IFS=',' read -r -a raw <<< "${csv:-}"
  for item in "${raw[@]}"; do
    if [[ -n ${item// /} ]]; then
      _result+=("${item// /}")
    fi
  done
}

upper() {
  local input=$1
  printf '%s' "${input^^}"
}

sync_with_rsync() {
  local target=$1
  local remote_dir=$2
  local -a excludes
  IFS=',' read -r -a excludes <<< "${RSYNC_EXCLUDES:-}"

  local -a args=("-az" "--delete")
  for pattern in "${excludes[@]}"; do
    if [[ -n $pattern ]]; then
      args+=("--exclude" "$pattern")
    fi
  done

  rsync "${args[@]}" "$PROJECT_ROOT/" "$target:$remote_dir/"
}

sync_with_tar() {
  local target=$1
  local remote_dir=$2
  local -a excludes
  IFS=',' read -r -a excludes <<< "${RSYNC_EXCLUDES:-}"

  local -a tar_excludes=()
  for pattern in "${excludes[@]}"; do
    if [[ -n $pattern ]]; then
      tar_excludes+=("--exclude=$pattern")
    fi
  done

  (cd "$PROJECT_ROOT" && tar -czf - "${tar_excludes[@]}" .) | \
    ssh "$target" "mkdir -p $(printf '%q' "$remote_dir") && tar -xzf - -C $(printf '%q' "$remote_dir")"
}

sync_repository() {
  local host=$1
  local arch=$2
  local target
  target=$(build_ssh_target "$host")

  log "INFO" "Synchronising repository to $target ($arch)"
  ssh "$target" "mkdir -p $(printf '%q' "$REMOTE_WORKDIR")"

  if [[ $(parse_bool "${SYNC_WITH_RSYNC:-true}") == "true" ]]; then
    sync_with_rsync "$target" "$REMOTE_WORKDIR"
  else
    sync_with_tar "$target" "$REMOTE_WORKDIR"
  fi
}

build_compose_flags() {
  local arch=$1
  local flags=" -f $(printf '%q' "${COMPOSE_FILE:-$DEFAULT_COMPOSE_FILE}")"

  if [[ $arch == "amd64" && -n ${AMD64_COMPOSE_FILE:-} ]]; then
    flags+=" -f $(printf '%q' "$AMD64_COMPOSE_FILE")"
  fi
  if [[ $arch == "arm64" && -n ${ARM64_COMPOSE_FILE:-} ]]; then
    flags+=" -f $(printf '%q' "$ARM64_COMPOSE_FILE")"
  fi
  echo "$flags"
}

compose_exec() {
  local host=$1
  local arch=$2
  shift 2
  local target
  target=$(build_ssh_target "$host")

  local flags
  flags=$(build_compose_flags "$arch")

  local env_flag=""
  if [[ -n ${COMPOSE_ENV_FILE:-} ]]; then
    env_flag=" --env-file $(printf '%q' "$COMPOSE_ENV_FILE")"
  fi

  local extra_flags=""
  if [[ -n ${GLOBAL_COMPOSE_FLAGS:-} ]]; then
    extra_flags=" ${GLOBAL_COMPOSE_FLAGS}"
  fi

  local cmd=""
  for arg in "$@"; do
    cmd+=" $(printf '%q' "$arg")"
  done

  local project_name=${COMPOSE_PROJECT_NAME:-monorepo}

  local remote_cmd
  printf -v remote_cmd 'cd %s && DOCKER_DEFAULT_PLATFORM=linux/%s docker compose --project-name %s%s%s%s%s' \
    "$(printf '%q' "$REMOTE_WORKDIR")" \
    "$arch" \
    "$(printf '%q' "$project_name")" \
    "$flags" \
    "$env_flag" \
    "$extra_flags" \
    "$cmd"

  log "INFO" "[$host] docker compose${cmd}"
  ssh "$target" "$remote_cmd"
}

deploy_host() {
  local host=$1
  local arch=$2

  if [[ ${SKIP_SYNC} == "false" ]]; then
    sync_repository "$host" "$arch"
  fi

  case $MODE in
    pull)
      if [[ ${SKIP_PULL} == "false" && $(parse_bool "${DEPLOY_PULL:-true}") == "true" ]]; then
        compose_exec "$host" "$arch" pull
      else
        log "INFO" "[$host] Skipping pull step"
      fi
      ;;
    build)
      if [[ ${SKIP_BUILD} == "false" && $(parse_bool "${DEPLOY_BUILD:-true}") == "true" ]]; then
        compose_exec "$host" "$arch" build "--pull"
      else
        log "INFO" "[$host] Skipping build step"
      fi
      ;;
    down)
      compose_exec "$host" "$arch" down "--remove-orphans"
      ;;
    deploy)
      if [[ ${SKIP_PULL} == "false" && $(parse_bool "${DEPLOY_PULL:-true}") == "true" ]]; then
        compose_exec "$host" "$arch" pull
      fi
      if [[ ${SKIP_BUILD} == "false" && $(parse_bool "${DEPLOY_BUILD:-true}") == "true" ]]; then
        compose_exec "$host" "$arch" build "--pull"
      fi
      compose_exec "$host" "$arch" up "-d" "--remove-orphans"
      ;;
    *)
      abort "Unsupported mode: $MODE"
      ;;
  esac
}

main() {
  local environment=""
  local config_override=""
  MODE="deploy"
  SKIP_SYNC="false"
  SKIP_BUILD="false"
  SKIP_PULL="false"
  declare -a REQUESTED_ARCHES=()

  while [[ $# -gt 0 ]]; do
    case $1 in
      -c|--config)
        config_override=$2
        shift 2
        ;;
      -m|--mode)
        MODE=${2,,}
        case $MODE in
          deploy|pull|build|down) ;;
          *) abort "Unknown mode: $MODE" ;;
        esac
        shift 2
        ;;
      --arch)
        REQUESTED_ARCHES+=("${2,,}")
        shift 2
        ;;
      --skip-sync)
        SKIP_SYNC="true"
        shift
        ;;
      --skip-build)
        SKIP_BUILD="true"
        shift
        ;;
      --skip-pull)
        SKIP_PULL="true"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        break
        ;;
      -* )
        abort "Unknown option: $1"
        ;;
      *)
        if [[ -z $environment ]]; then
          environment=$1
          shift
        else
          abort "Unexpected argument: $1"
        fi
        ;;
    esac
  done

  if [[ -z $environment && -z $config_override ]]; then
    usage
    exit 1
  fi

  local config_file
  if [[ -n $config_override ]]; then
    config_file=$config_override
  else
    config_file="$DEFAULT_CONFIG_DIR/${environment}.env"
  fi

  if [[ ! -f $config_file ]]; then
    abort "Configuration file not found: $config_file"
  fi

  log "INFO" "Loading configuration from $config_file"
  # shellcheck disable=SC1090
  source "$config_file"

  REMOTE_WORKDIR=${REMOTE_WORKDIR:-/opt/monorepo}
  COMPOSE_FILE=${COMPOSE_FILE:-$DEFAULT_COMPOSE_FILE}
  COMPOSE_ENV_FILE=${COMPOSE_ENV_FILE:-$DEFAULT_ENV_FILE}
  RSYNC_EXCLUDES=${RSYNC_EXCLUDES:-.git,.github,node_modules,__pycache__,.pytest_cache,.mypy_cache,.ruff_cache,.venv,frontend/.vite,frontend/dist}
  SYNC_WITH_RSYNC=${SYNC_WITH_RSYNC:-true}

  if [[ -n ${COMPOSE_ENV_FILE:-} && ! -f "$PROJECT_ROOT/$COMPOSE_ENV_FILE" ]]; then
    log "WARN" "Compose environment file $COMPOSE_ENV_FILE not found locally; ensure the remote host provides it."
  fi

  require_command ssh
  if [[ $(parse_bool "$SYNC_WITH_RSYNC") == "true" ]]; then
    require_command rsync
  else
    require_command tar
  fi

  declare -A HOST_GROUPS
  HOST_GROUPS[amd64]=${AMD64_HOSTS:-}
  HOST_GROUPS[arm64]=${ARM64_HOSTS:-}

  if [[ ${#REQUESTED_ARCHES[@]} -eq 0 ]]; then
    REQUESTED_ARCHES=(amd64 arm64)
  fi

  declare -a FINAL_ARCHES=()
  for arch in "${REQUESTED_ARCHES[@]}"; do
    case $arch in
      amd64|arm64)
        FINAL_ARCHES+=("$arch")
        ;;
      all)
        FINAL_ARCHES=(amd64 arm64)
        ;;
      *)
        abort "Unsupported architecture filter: $arch"
        ;;
    esac
  done

  # Remove duplicates
  declare -A seen=()
  declare -a unique_arches=()
  for arch in "${FINAL_ARCHES[@]}"; do
    if [[ -z ${seen[$arch]:-} ]]; then
      seen[$arch]=1
      unique_arches+=("$arch")
    fi
  done

  if [[ ${#unique_arches[@]} -eq 0 ]]; then
    unique_arches=(amd64 arm64)
  fi

  for arch in "${unique_arches[@]}"; do
    local hosts=${HOST_GROUPS[$arch]:-}
    declare -a host_list=()
    split_csv "$hosts" host_list

    if [[ ${#host_list[@]} -eq 0 ]]; then
      log "WARN" "No hosts defined for architecture $arch; skipping."
      continue
    fi

    for host in "${host_list[@]}"; do
      log "INFO" "Processing $host ($arch)"
      deploy_host "$host" "$arch"
    done
  done

  log "INFO" "Deployment workflow completed."
}

main "$@"
