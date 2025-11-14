#!/usr/bin/env bash
# verify_deploy.sh - Automated deployment verification script for ca-pdf
# This script performs a complete deployment validation cycle:
# - Clean environment (optional)
# - Deploy via docker compose
# - Wait for all containers to be healthy
# - Test all health endpoints
# - Exit non-zero on any failure

set -Eeuo pipefail

# Color codes for terminal output
if [[ -t 1 ]]; then
  BOLD="\033[1m"
  GREEN="\033[32m"
  RED="\033[31m"
  YELLOW="\033[33m"
  BLUE="\033[34m"
  RESET="\033[0m"
else
  BOLD=""
  GREEN=""
  RED=""
  YELLOW=""
  BLUE=""
  RESET=""
fi

# Logging functions
log_step() {
  printf "%b==> %s%b\n" "${BOLD}${BLUE}" "$1" "${RESET}"
}

log_info() {
  printf "%bℹ%b %s\n" "${BLUE}" "${RESET}" "$1"
}

log_warn() {
  printf "%b⚠%b %s\n" "${YELLOW}" "${RESET}" "$1"
}

log_error() {
  printf "%b✖%b %s\n" "${RED}" "${RESET}" "$1"
}

log_success() {
  printf "%b✔%b %s\n" "${GREEN}" "${RESET}" "$1"
}

# Default configuration
FORCE_CLEAN=0
SKIP_CLEAN=0
CI_MODE=0
SKIP_VALIDATION=0
TIMEOUT=600  # 10 minutes default timeout for health checks
USE_HTTPS=0  # Default to HTTP
COMPOSE_FILE="docker-compose.yml"
PROJECT_ROOT=""
EXIT_CODE=0

# Help message
show_help() {
  cat << EOF
Usage: $0 [OPTIONS]

Automated deployment verification script for ca-pdf (nginx-based stack).

OPTIONS:
  --force-clean         Automatically clean old data volumes and PostgreSQL data
  --skip-clean          Skip the clean step entirely (test existing deployment)
  --ci-mode             Non-interactive mode, skip prompts, use defaults
  --skip-validation     Skip post-deployment validation (not recommended)
  --timeout SECONDS     Timeout for health checks (default: 600)
  --use-https           Test HTTPS endpoints (requires mounted certificates)
  --project-root PATH   Path to ca-pdf project root (default: auto-detect)
  --help                Show this help message

EXAMPLES:
  # Full clean deployment verification (default)
  $0

  # CI mode with force clean
  $0 --ci-mode --force-clean

  # Test existing deployment without cleaning
  $0 --skip-clean

  # Test HTTPS deployment (with mounted certificates)
  $0 --use-https

  # Quick test with shorter timeout
  $0 --skip-clean --timeout 120

EXIT CODES:
  0 - All checks passed
  1 - Environment setup failed
  2 - Deployment failed
  3 - Container health check failed
  4 - Endpoint validation failed
  5 - Cleanup failed

EOF
  exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --force-clean)
      FORCE_CLEAN=1
      shift
      ;;
    --skip-clean)
      SKIP_CLEAN=1
      shift
      ;;
    --ci-mode)
      CI_MODE=1
      shift
      ;;
    --skip-validation)
      SKIP_VALIDATION=1
      shift
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --use-https)
      USE_HTTPS=1
      shift
      ;;
    --project-root)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    --help)
      show_help
      ;;
    *)
      log_error "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Auto-detect project root if not specified
if [[ -z "${PROJECT_ROOT}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

# Ensure project root exists
if [[ ! -d "${PROJECT_ROOT}" ]]; then
  log_error "Project root not found: ${PROJECT_ROOT}"
  exit 1
fi

# Construct URLs based on HTTPS flag
if (( USE_HTTPS )); then
  PROTOCOL="https"
  FRONTEND_URL="https://localhost"
else
  PROTOCOL="http"
  FRONTEND_URL="http://localhost"
fi

FRONTEND_HEALTH_URL="${FRONTEND_URL}/healthz"
BACKEND_HEALTH_URL="${FRONTEND_URL}/api/v1/health"
BACKEND_DOCS_URL="${FRONTEND_URL}/api/v1/docs"

# Detect docker compose command
detect_docker_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    log_error "Docker Compose not found. Please install Docker Compose."
    exit 1
  fi
  log_info "Using compose command: ${COMPOSE_CMD}"
}

# Clean existing deployment
clean_deployment() {
  if (( SKIP_CLEAN )); then
    log_info "Skipping clean step (--skip-clean specified)"
    return 0
  fi

  log_step "Cleaning existing deployment"
  
  cd "${PROJECT_ROOT}" || exit 1
  
  # Check if docker-compose.yml exists
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    log_warn "docker-compose.yml not found, skipping clean"
    return 0
  fi
  
  # Stop and remove containers
  if ${COMPOSE_CMD} ps -q 2>/dev/null | grep -q .; then
    log_info "Stopping Docker containers..."
    ${COMPOSE_CMD} down --remove-orphans || true
  fi
  
  # Remove volumes if force-clean
  if (( FORCE_CLEAN )); then
    log_info "Removing Docker volumes (--force-clean)..."
    ${COMPOSE_CMD} down -v 2>/dev/null || true
    
    # Remove PostgreSQL data directory if it exists
    if [[ -d "${PROJECT_ROOT}/data/postgres" ]]; then
      log_info "Removing PostgreSQL data directory..."
      rm -rf "${PROJECT_ROOT}/data/postgres" || true
    fi
    
    # Clean matching Docker volumes
    docker volume ls --format '{{.Name}}' | grep -E 'ca_pdf|ca-pdf' | while read -r vol; do
      log_info "Removing volume: ${vol}"
      docker volume rm "${vol}" 2>/dev/null || true
    done
  else
    if (( CI_MODE )); then
      log_info "Skipping volume removal in CI mode (use --force-clean to enable)"
    else
      read -r -p "Remove data volumes? This will delete all data. [y/N] " response
      if [[ "${response}" =~ ^([Yy])$ ]]; then
        log_info "Removing Docker volumes..."
        ${COMPOSE_CMD} down -v 2>/dev/null || true
      fi
    fi
  fi
  
  log_success "Cleanup completed"
}

# Deploy using docker compose directly
deploy_with_compose() {
  log_step "Deploying with docker compose"
  
  cd "${PROJECT_ROOT}" || exit 1
  
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    log_error "docker-compose.yml not found in ${PROJECT_ROOT}"
    return 2
  fi
  
  # Ensure .env files exist
  if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
      log_info "Copying .env.example to .env"
      cp .env.example .env
    else
      log_error ".env file not found and no .env.example to copy"
      return 2
    fi
  fi
  
  if [[ ! -f .env.docker ]]; then
    if [[ -f .env.docker.example ]]; then
      log_info "Copying .env.docker.example to .env.docker"
      cp .env.docker.example .env.docker
    fi
  fi
  
  # Pull base images (only db since frontend/backend are built)
  log_info "Pulling base images..."
  ${COMPOSE_CMD} pull --quiet db 2>/dev/null || true
  
  # Build and start containers
  log_info "Building and starting containers..."
  export COMPOSE_PROJECT_NAME=ca_pdf
  export COMPOSE_DOCKER_CLI_BUILD=1
  export DOCKER_BUILDKIT=1
  
  if ${COMPOSE_CMD} up -d --build; then
    log_success "Containers started"
    return 0
  else
    log_error "Failed to start containers"
    return 2
  fi
}

# Wait for a container to be healthy
wait_for_container_health() {
  local service="$1"
  local timeout="${2:-${TIMEOUT}}"
  local elapsed=0
  local check_interval=5
  
  log_info "Waiting for ${service} to be healthy (timeout: ${timeout}s)..."
  
  while (( elapsed < timeout )); do
    # Get container ID
    local container_id
    container_id=$(${COMPOSE_CMD} ps -q "${service}" 2>/dev/null || true)
    
    if [[ -z "${container_id}" ]]; then
      log_warn "${service}: Container not found yet (${elapsed}s elapsed)"
      sleep ${check_interval}
      elapsed=$((elapsed + check_interval))
      continue
    fi
    
    # Check health status
    local status
    status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}" 2>/dev/null || echo "unknown")
    
    case "${status}" in
      healthy)
        log_success "${service}: Healthy"
        return 0
        ;;
      unhealthy)
        log_error "${service}: Unhealthy"
        return 3
        ;;
      starting)
        log_info "${service}: Starting... (${elapsed}s elapsed)"
        ;;
      running)
        # Container running but no health check defined
        log_warn "${service}: Running (no health check defined)"
        return 0
        ;;
      exited|dead)
        log_error "${service}: Container exited or died"
        return 3
        ;;
      *)
        log_info "${service}: Status=${status} (${elapsed}s elapsed)"
        ;;
    esac
    
    sleep ${check_interval}
    elapsed=$((elapsed + check_interval))
  done
  
  log_error "${service}: Timeout after ${timeout}s"
  return 3
}

# Wait for all containers to be healthy
wait_for_all_containers() {
  log_step "Waiting for all containers to be healthy"
  
  cd "${PROJECT_ROOT}" || exit 1
  
  # Only 3 services in the simplified stack
  local services=("db" "backend" "frontend")
  local failed=0
  
  for service in "${services[@]}"; do
    if ! wait_for_container_health "${service}"; then
      log_error "Failed to wait for ${service}"
      failed=1
    fi
  done
  
  if (( failed )); then
    log_error "Some containers failed health checks"
    return 3
  fi
  
  # Verify exactly 3 containers are running
  local running_count
  running_count=$(${COMPOSE_CMD} ps -q 2>/dev/null | wc -l)
  if [[ "${running_count}" -eq 3 ]]; then
    log_success "All 3 containers are healthy"
  else
    log_warn "Expected 3 running containers, found ${running_count}"
  fi
  
  return 0
}

# Test an HTTP endpoint
test_endpoint() {
  local name="$1"
  local url="$2"
  local expected_status="${3:-200}"
  local max_retries="${4:-3}"
  local retry_delay="${5:-5}"
  
  log_info "Testing ${name}: ${url}"
  
  for attempt in $(seq 1 ${max_retries}); do
    if (( attempt > 1 )); then
      log_info "Retry ${attempt}/${max_retries} for ${name}..."
      sleep ${retry_delay}
    fi
    
    # Use curl with appropriate flags
    local curl_flags="-sSL -w %{http_code} -o /dev/null --max-time 10"
    
    # For HTTPS with self-signed certs (local testing)
    if [[ "${url}" == https://* ]]; then
      curl_flags="${curl_flags} -k"
    fi
    
    local http_code
    if http_code=$(curl ${curl_flags} "${url}" 2>/dev/null); then
      if [[ "${http_code}" == "${expected_status}" ]]; then
        log_success "${name}: HTTP ${http_code} OK"
        return 0
      else
        log_warn "${name}: HTTP ${http_code} (expected ${expected_status})"
      fi
    else
      log_warn "${name}: Request failed"
    fi
  done
  
  log_error "${name}: Failed after ${max_retries} attempts"
  return 4
}

# Validate all endpoints
validate_endpoints() {
  if (( SKIP_VALIDATION )); then
    log_info "Skipping endpoint validation (--skip-validation specified)"
    return 0
  fi

  log_step "Validating health endpoints"
  
  local failed=0
  
  # Test frontend root (should return HTML or 200)
  if ! test_endpoint "Frontend /" "${FRONTEND_URL}" "200"; then
    failed=1
  fi
  
  # Test frontend health endpoint
  if ! test_endpoint "Frontend /healthz" "${FRONTEND_HEALTH_URL}" "200"; then
    failed=1
  fi
  
  # Test backend health endpoint (via nginx proxy)
  if ! test_endpoint "Backend /api/v1/health" "${BACKEND_HEALTH_URL}" "200"; then
    failed=1
  fi
  
  # Test API docs endpoint (via nginx proxy)
  if ! test_endpoint "API Docs /api/v1/docs" "${BACKEND_DOCS_URL}" "200"; then
    failed=1
  fi
  
  if (( failed )); then
    log_error "Some endpoint validations failed"
    return 4
  fi
  
  log_success "All endpoint validations passed"
  return 0
}

# Show deployment status
show_status() {
  log_step "Deployment Status Summary"
  
  cd "${PROJECT_ROOT}" || exit 1
  
  echo ""
  echo "Services:"
  ${COMPOSE_CMD} ps 2>/dev/null || true
  
  echo ""
  echo "Endpoints:"
  echo "  Frontend:      ${FRONTEND_URL}"
  echo "  API Health:    ${BACKEND_HEALTH_URL}"
  echo "  API Docs:      ${BACKEND_DOCS_URL}"
  
  echo ""
  echo "Health Checks:"
  echo "  Frontend /healthz:        ${FRONTEND_HEALTH_URL}"
  echo "  Backend /api/v1/health:   ${BACKEND_HEALTH_URL}"
  
  echo ""
}

# Collect logs from all services
collect_logs() {
  log_step "Collecting service logs"
  
  cd "${PROJECT_ROOT}" || exit 1
  
  local services=("db" "backend" "frontend")
  local log_dir="${PROJECT_ROOT}/logs"
  
  mkdir -p "${log_dir}"
  
  for service in "${services[@]}"; do
    log_info "Collecting logs for ${service}..."
    ${COMPOSE_CMD} logs "${service}" > "${log_dir}/${service}.log" 2>&1 || true
  done
  
  log_success "Logs collected to ${log_dir}/"
}

# Main verification workflow
main() {
  log_step "Starting deployment verification (nginx-based stack)"
  log_info "Project root: ${PROJECT_ROOT}"
  log_info "Protocol: ${PROTOCOL}"
  log_info "Frontend URL: ${FRONTEND_URL}"
  echo ""
  
  # Detect docker compose
  detect_docker_compose
  
  # Clean existing deployment if needed
  if ! clean_deployment; then
    log_error "Cleanup failed"
    exit 5
  fi
  
  # Deploy with docker compose
  if ! deploy_with_compose; then
    log_error "Deployment with docker compose failed"
    collect_logs
    exit 2
  fi
  
  # Wait for containers to be healthy
  if ! wait_for_all_containers; then
    log_error "Container health check failed"
    show_status
    collect_logs
    exit 3
  fi
  
  # Validate endpoints
  if ! validate_endpoints; then
    log_error "Endpoint validation failed"
    show_status
    collect_logs
    exit 4
  fi
  
  # Show final status
  show_status
  
  log_success "Deployment verification completed successfully!"
  echo ""
  log_info "Next steps:"
  echo "  1. Open browser: ${FRONTEND_URL}"
  echo "  2. Check API docs: ${BACKEND_DOCS_URL}"
  echo "  3. View logs: docker compose logs -f"
  echo ""
  
  exit 0
}

# Run main function
main "$@"
