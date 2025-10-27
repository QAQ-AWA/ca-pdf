#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
ca-pdf deployment helper

Usage: ./deploy.sh <command> [options]

Commands:
  up [--no-build]      Build images (if needed) and start the stack in the background
  down                 Stop containers and keep named volumes
  destroy              Stop containers and remove named volumes
  restart              Restart backend and frontend containers
  logs [service]       Tail logs (default: all services)
  ps                   Show container status
  help                 Show this help message

Environment variables:
  TARGET_PLATFORMS     Comma-separated list of build targets (default: detected host arch)
  COMPOSE_FILE         Override docker-compose file (default: docker-compose.yml)

Examples:
  ./deploy.sh up
  TARGET_PLATFORMS=linux/amd64,linux/arm64 ./deploy.sh up
  ./deploy.sh logs backend
USAGE
}

require_env_files() {
  if [[ ! -f .env ]]; then
    echo "[deploy] Missing .env. Copy .env.example and update the values before deploying." >&2
    exit 1
  fi
  if [[ ! -f .env.docker ]]; then
    echo "[deploy] Missing .env.docker. Copy .env.docker.example and update overrides before deploying." >&2
    exit 1
  fi
}

set_platform_defaults() {
  if [[ -n "${TARGET_PLATFORMS:-}" ]]; then
    export DOCKER_DEFAULT_PLATFORM="${TARGET_PLATFORMS}"
    return
  fi

  local arch
  arch=$(uname -m || echo "unknown")
  case "${arch}" in
    x86_64|amd64)
      export DOCKER_DEFAULT_PLATFORM="linux/amd64"
      ;;
    arm64|aarch64)
      export DOCKER_DEFAULT_PLATFORM="linux/arm64"
      ;;
    *)
      unset DOCKER_DEFAULT_PLATFORM
      ;;
  esac
}

compose() {
  docker compose "$@"
}

command=${1:-help}
shift || true

if [[ "${command}" == "help" || "${command}" == "--help" || "${command}" == "-h" ]]; then
  usage
  exit 0
fi

export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

require_env_files
set_platform_defaults

case "${command}" in
  up)
    compose up -d "$@"
    ;;
  down)
    compose down "$@"
    ;;
  destroy)
    compose down --volumes "$@"
    ;;
  restart)
    compose restart backend frontend "$@"
    ;;
  logs)
    if [[ $# -eq 0 ]]; then
      compose logs -f
    else
      compose logs -f "$@"
    fi
    ;;
  ps)
    compose ps "$@"
    ;;
  *)
    echo "[deploy] Unknown command: ${command}" >&2
    echo >&2
    usage
    exit 1
    ;;
 esac
