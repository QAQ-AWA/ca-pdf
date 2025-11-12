#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${BASH_VERSINFO[0]} -lt 4 ]]; then
  echo "This script requires Bash 4.0 or higher." >&2
  exit 1
fi

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

prompt_confirm() {
  local prompt_msg=${1:-"确认继续吗?"}
  local default_choice=${2:-"y"}
  local suffix="[y/N]"
  if [[ "${default_choice}" =~ ^([Yy])$ ]]; then
    suffix="[Y/n]"
  fi
  read -r -p "${prompt_msg} ${suffix} " response || true
  response=${response:-${default_choice}}
  [[ "${response}" =~ ^([Yy])$ ]]
}

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    log_error "缺少依赖：${cmd}"
    exit 1
  fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/deploy-$(date +%Y%m%d).log"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_DOCKER_FILE="${PROJECT_ROOT}/.env.docker"
TRAEFIK_DIR="${PROJECT_ROOT}/config/traefik"
TRAEFIK_CERT_DIR="${TRAEFIK_DIR}/certs"
TRAEFIK_DYNAMIC_FILE="${TRAEFIK_DIR}/dynamic.yml"

COMPOSE_CMD="docker compose"
DEPLOY_STARTED=0
MODE="production"
DOMAIN=""
FRONTEND_DOMAIN=""
BACKEND_DOMAIN=""
FRONTEND_URL=""
BACKEND_URL=""
DOCS_URL=""
DB_DATA_PATH=""
POSTGRES_DB="app_db"
POSTGRES_USER="app_user"
POSTGRES_PASSWORD=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
ACME_EMAIL=""
CORS_ORIGINS=""
JWT_SECRET_KEY=""
SECRET_KEY=""
MASTER_KEY=""
TRAEFIK_CA_SERVER="https://acme-v02.api.letsencrypt.org/directory"
TRAEFIK_LOG_LEVEL="INFO"
TRAEFIK_COMMAND=""
BACKEND_LABELS=""
FRONTEND_LABELS=""
SHOULD_WRITE_COMPOSE="true"

on_error() {
  local exit_code=$?
  local line_no=${1:-unknown}
  log_error "部署失败（第 ${line_no} 行，退出码 ${exit_code}）。"
  if (( DEPLOY_STARTED )); then
    log_warn "正在回滚 Docker 容器..."
    if command -v docker >/dev/null 2>&1; then
      ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true
    fi
  fi
  log_error "请查看日志文件获取详情：${LOG_FILE}"
  exit 1
}

trap 'on_error "$LINENO"' ERR

normalize_path() {
  local input_path="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath -m "${input_path}"
  else
    python3 -c 'import os, sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "${input_path}"
  fi
}

detect_docker_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    log_error "未找到 docker compose，请先安装 Docker Compose V2 或兼容版本。"
    exit 1
  fi
}

check_os() {
  local uname_s
  uname_s=$(uname -s || echo "unknown")
  case "${uname_s}" in
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        log_info "检测到 WSL2，建议优先使用原生 Linux 获得最佳兼容性。"
      else
        log_success "操作系统检查通过：Linux"
      fi
      ;;
    *)
      log_warn "当前系统 (${uname_s}) 未经过完整验证，推荐使用 Linux 或 WSL2。"
      ;;
  esac
}

check_docker() {
  require_command docker
  detect_docker_compose
  local docker_version compose_version
  docker_version=$(docker --version || echo "unknown")
  compose_version=$(${COMPOSE_CMD} version || echo "unknown")
  log_success "Docker 已安装：${docker_version}"
  log_success "Docker Compose：${compose_version}"
}

check_port() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    if ss -ltn "sport = :${port}" 2>/dev/null | grep -q ":${port}"; then
      log_error "端口 ${port} 已被占用，请释放后重试。"
      exit 1
    fi
  elif command -v lsof >/dev/null 2>&1; then
    if lsof -i "TCP:${port}" -sTCP:LISTEN -P -n >/dev/null 2>&1; then
      log_error "端口 ${port} 已被占用，请释放后重试。"
      exit 1
    fi
  else
    log_warn "无法检测端口 ${port} 是否占用（缺少 ss/lsof），请自行确认。"
  fi
}

check_resources() {
  if command -v free >/dev/null 2>&1; then
    local mem_total
    mem_total=$(free -m | awk '/^Mem:/ {print $2}')
    if [[ -n "${mem_total}" && "${mem_total}" -lt 1800 ]]; then
      log_warn "当前可用内存约 ${mem_total}MB，推荐至少 2GB。"
      if ! prompt_confirm "继续部署可能导致性能问题，是否继续?" "n"; then
        exit 1
      fi
    else
      log_success "内存检查通过：${mem_total}MB"
    fi
  else
    log_warn "无法检测内存容量（缺少 free 命令）。"
  fi

  if command -v df >/dev/null 2>&1; then
    local disk_avail
    disk_avail=$(df -Pm "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    if [[ -n "${disk_avail}" && "${disk_avail}" -lt 5120 ]]; then
      log_warn "当前可用磁盘空间约 ${disk_avail}MB，推荐至少 5GB。"
      if ! prompt_confirm "磁盘空间不足，是否继续?" "n"; then
        exit 1
      fi
    else
      log_success "磁盘空间检查通过：${disk_avail}MB"
    fi
  else
    log_warn "无法检测磁盘空间（缺少 df 命令）。"
  fi
}

prompt_domain() {
  printf "\n"
  read -r -p "请输入部署使用的主域名（留空则使用本地模式）: " DOMAIN || true
  DOMAIN=${DOMAIN// /}
  if [[ -z "${DOMAIN}" ]]; then
    MODE="local"
    FRONTEND_DOMAIN="app.localtest.me"
    BACKEND_DOMAIN="api.localtest.me"
    FRONTEND_URL="https://${FRONTEND_DOMAIN}"
    BACKEND_URL="https://${BACKEND_DOMAIN}"
    DOCS_URL="${BACKEND_URL}/docs"
    log_info "已选择本地模式：使用 localtest.me 域名并生成自签名证书。"
  else
    MODE="production"
    read -r -p "前端子域名（默认: app.${DOMAIN}）: " FRONTEND_DOMAIN || true
    FRONTEND_DOMAIN=${FRONTEND_DOMAIN:-app.${DOMAIN}}
    read -r -p "后端子域名（默认: api.${DOMAIN}）: " BACKEND_DOMAIN || true
    BACKEND_DOMAIN=${BACKEND_DOMAIN:-api.${DOMAIN}}
    FRONTEND_URL="https://${FRONTEND_DOMAIN}"
    BACKEND_URL="https://${BACKEND_DOMAIN}"
    DOCS_URL="${BACKEND_URL}/docs"
  fi
}

prompt_email() {
  if [[ "${MODE}" == "production" ]]; then
    read -r -p "请输入用于申请 Let's Encrypt 证书的邮箱（可留空，默认 admin@${DOMAIN}）: " ACME_EMAIL || true
  else
    ACME_EMAIL=""
  fi
}

prompt_admin_email() {
  local default_email
  if [[ "${MODE}" == "production" ]]; then
    default_email="admin@${DOMAIN}"
  else
    default_email="admin@example.com"
  fi
  read -r -p "管理员邮箱（默认: ${default_email}）: " ADMIN_EMAIL || true
  ADMIN_EMAIL=${ADMIN_EMAIL:-${default_email}}
}

prompt_db_path() {
  local default_path="${PROJECT_ROOT}/data/postgres"
  read -r -p "PostgreSQL 数据目录（默认: ${default_path}）: " DB_DATA_PATH || true
  DB_DATA_PATH=${DB_DATA_PATH:-${default_path}}
  DB_DATA_PATH=$(normalize_path "${DB_DATA_PATH}")
  mkdir -p "${DB_DATA_PATH}"
  log_success "PostgreSQL 数据将保存到：${DB_DATA_PATH}"
}

validate_json_list() {
  python3 -c 'import json, sys; data=sys.argv[1]; 
try:
    parsed=json.loads(data)
except Exception:
    sys.exit(1)
sys.exit(0 if isinstance(parsed, list) else 1)' "$1"
}

prompt_cors() {
  local default_cors
  if [[ "${MODE}" == "production" ]]; then
    default_cors='["'"${FRONTEND_URL}"'"]'
  else
    default_cors='["'"${FRONTEND_URL}"'", "http://localhost:5173", "http://127.0.0.1:5173"]'
  fi
  read -r -p "BACKEND_CORS_ORIGINS（JSON 列表，默认: ${default_cors}）: " CORS_ORIGINS || true
  CORS_ORIGINS=${CORS_ORIGINS:-${default_cors}}
  if ! validate_json_list "${CORS_ORIGINS}"; then
    log_error "BACKEND_CORS_ORIGINS 必须是合法的 JSON 列表，如 [\"https://example.com\"]。"
    exit 1
  fi
}

generate_secret_hex() {
  openssl rand -hex 32
}

generate_fernet_from_hex() {
  local hex_value
  hex_value=$(openssl rand -hex 32)
  python3 -c 'import base64, binascii, sys; print(base64.urlsafe_b64encode(binascii.unhexlify(sys.argv[1])).decode())' "${hex_value}"
}

generate_passwords() {
  require_command openssl
  require_command python3
  POSTGRES_PASSWORD=$(openssl rand -hex 16)
  ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '\n=/+[:space:]' | cut -c1-20)
  SECRET_KEY=$(generate_secret_hex)
  JWT_SECRET_KEY=$(generate_secret_hex)
  MASTER_KEY=$(generate_fernet_from_hex)
}

ensure_dirs() {
  mkdir -p "${TRAEFIK_DIR}"
  mkdir -p "${TRAEFIK_CERT_DIR}"
}

build_traefik_assets() {
  local command_items=(
    "--providers.docker=true"
    "--providers.docker.exposedbydefault=false"
    "--providers.file.directory=/etc/traefik/dynamic"
    "--entrypoints.web.address=:80"
    "--entrypoints.websecure.address=:443"
    "--log.level=${TRAEFIK_LOG_LEVEL}"
    "--ping=true"
    "--ping.entrypoint=web"
  )
  if [[ "${MODE}" == "production" ]]; then
    local acme_email="${ACME_EMAIL}"
    if [[ -z "${acme_email}" ]]; then
      acme_email="admin@${DOMAIN}"
    fi
    command_items+=(
      "--certificatesresolvers.le.acme.email=${acme_email}"
      "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
      "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web"
      "--certificatesresolvers.le.acme.caserver=${TRAEFIK_CA_SERVER}"
    )
  else
    command_items+=(
      "--serversTransport.insecureSkipVerify=true"
    )
  fi
  printf -v TRAEFIK_COMMAND '      - %s\n' "${command_items[@]}"

  local backend_labels=(
    "traefik.enable=true"
    "traefik.http.routers.backend-web.rule=Host(\`${BACKEND_DOMAIN}\`)"
    "traefik.http.routers.backend-web.entrypoints=web"
    "traefik.http.routers.backend-web.middlewares=redirect-to-https@file"
    "traefik.http.routers.backend.rule=Host(\`${BACKEND_DOMAIN}\`)"
    "traefik.http.routers.backend.entrypoints=websecure"
    "traefik.http.services.backend.loadbalancer.server.port=8000"
  )
  local frontend_labels=(
    "traefik.enable=true"
    "traefik.http.routers.frontend-web.rule=Host(\`${FRONTEND_DOMAIN}\`)"
    "traefik.http.routers.frontend-web.entrypoints=web"
    "traefik.http.routers.frontend-web.middlewares=redirect-to-https@file"
    "traefik.http.routers.frontend.rule=Host(\`${FRONTEND_DOMAIN}\`)"
    "traefik.http.routers.frontend.entrypoints=websecure"
    "traefik.http.services.frontend.loadbalancer.server.port=8080"
  )
  if [[ "${MODE}" == "production" ]]; then
    backend_labels+=("traefik.http.routers.backend.tls.certresolver=le")
    frontend_labels+=("traefik.http.routers.frontend.tls.certresolver=le")
  else
    backend_labels+=("traefik.http.routers.backend.tls=true")
    frontend_labels+=("traefik.http.routers.frontend.tls=true")
  fi
  printf -v BACKEND_LABELS '      - %s\n' "${backend_labels[@]}"
  printf -v FRONTEND_LABELS '      - %s\n' "${frontend_labels[@]}"
}

write_env_file() {
  cat >"${ENV_FILE}" <<EOF
APP_NAME=ca-pdf
API_V1_PREFIX=/api/v1
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
DATABASE_ECHO=false
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=4320
BACKEND_CORS_ORIGINS=${CORS_ORIGINS}
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
ADMIN_ROLE=admin
ENCRYPTED_STORAGE_ALGORITHM=fernet
ENCRYPTED_STORAGE_MASTER_KEY=${MASTER_KEY}
PRIVATE_KEY_MAX_BYTES=8192
SEAL_IMAGE_MAX_BYTES=1048576
PDF_MAX_BYTES=52428800
PDF_BATCH_MAX_COUNT=10
EOF
}

write_env_docker_file() {
  cat >"${ENV_DOCKER_FILE}" <<EOF
# 由 scripts/deploy.sh 自动生成于 $(date -u +"%Y-%m-%dT%H:%M:%SZ")
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_HOST_PORT=5432
POSTGRES_DATA_PATH=${DB_DATA_PATH}

TRAEFIK_HTTP_PORT=80
TRAEFIK_HTTPS_PORT=443
TRAEFIK_LOG_LEVEL=${TRAEFIK_LOG_LEVEL}
BACKEND_DOMAIN=${BACKEND_DOMAIN}
FRONTEND_DOMAIN=${FRONTEND_DOMAIN}
TRAEFIK_ACME_EMAIL=${ACME_EMAIL}
TRAEFIK_ACME_CA_SERVER=${TRAEFIK_CA_SERVER}

VITE_API_BASE_URL=${BACKEND_URL}
VITE_PUBLIC_BASE_URL=${FRONTEND_URL}
VITE_APP_NAME=ca-pdf
EOF
}

write_dynamic_config() {
  if [[ "${MODE}" == "local" ]]; then
    local cert_file="${TRAEFIK_CERT_DIR}/selfsigned.crt"
    local key_file="${TRAEFIK_CERT_DIR}/selfsigned.key"
    log_step "生成自签名证书"
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -keyout "${key_file}" \
      -out "${cert_file}" \
      -subj "/CN=${FRONTEND_DOMAIN}" \
      -addext "subjectAltName=DNS:${FRONTEND_DOMAIN},DNS:${BACKEND_DOMAIN}" >/dev/null 2>&1
    log_success "已生成自签名证书：${cert_file}"
    cat >"${TRAEFIK_DYNAMIC_FILE}" <<EOF
http:
  middlewares:
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true
tls:
  options:
    default:
      minVersion: VersionTLS12
  certificates:
    - certFile: /etc/traefik/dynamic/certs/selfsigned.crt
      keyFile: /etc/traefik/dynamic/certs/selfsigned.key
EOF
  else
    cat >"${TRAEFIK_DYNAMIC_FILE}" <<'EOF'
http:
  middlewares:
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true
tls:
  options:
    default:
      minVersion: VersionTLS12
EOF
  fi
}

write_compose_file() {
  build_traefik_assets
  cat >"${COMPOSE_FILE}" <<EOF
version: "3.9"

services:
  traefik:
    image: traefik:v3.1
    command:
${TRAEFIK_COMMAND}    ports:
      - "80:80"
      - "443:443"
    volumes:
      - traefik_letsencrypt:/letsencrypt
      - ./config/traefik:/etc/traefik/dynamic:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - edge
    labels:
      - traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https
      - traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true
    healthcheck:
      test: ["CMD", "traefik", "healthcheck", "--ping"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - "${DB_DATA_PATH}:/var/lib/postgresql/data"
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
      args:
        COMMIT_SHA: \${COMMIT_SHA:-local}
        BUILD_VERSION: \${BUILD_VERSION:-deploy}
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env
      - .env.docker
    networks:
      - internal
      - edge
    labels:
${BACKEND_LABELS}

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
      args:
        COMMIT_SHA: \${COMMIT_SHA:-local}
        BUILD_VERSION: \${BUILD_VERSION:-deploy}
        VITE_API_BASE_URL: ${BACKEND_URL}
        VITE_APP_NAME: ca-pdf
        VITE_PUBLIC_BASE_URL: ${FRONTEND_URL}
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - edge
    labels:
${FRONTEND_LABELS}

networks:
  internal:
    driver: bridge
  edge:
    driver: bridge

volumes:
  traefik_letsencrypt:
EOF
}

wait_for_service() {
  local service="$1"
  local timeout="$2"
  local elapsed=0
  while (( elapsed < timeout )); do
    local container_id
    container_id=$(${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps -q "${service}" 2>/dev/null || true)
    if [[ -z "${container_id}" ]]; then
      sleep 5
      elapsed=$((elapsed + 5))
      continue
    fi
    local status
    status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}" 2>/dev/null || echo "starting")
    case "${status}" in
      healthy)
        return 0
        ;;
      unhealthy|exited|dead)
        return 1
        ;;
      *)
        sleep 5
        elapsed=$((elapsed + 5))
        ;;
    esac
  done
  return 1
}

run_migrations() {
  log_step "执行数据库迁移"
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T backend alembic upgrade head
  log_success "数据库迁移完成"
}

start_stack() {
  pushd "${PROJECT_ROOT}" >/dev/null
  export COMPOSE_PROJECT_NAME=ca_pdf
  export COMPOSE_DOCKER_CLI_BUILD=1
  export DOCKER_BUILDKIT=1
  DEPLOY_STARTED=1
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" pull --quiet traefik db >/dev/null 2>&1 || true
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d --build
  if ! wait_for_service "db" 180; then
    log_error "PostgreSQL 服务启动失败，请执行 \"${COMPOSE_CMD} -f ${COMPOSE_FILE} logs db\" 排查。"
    exit 1
  fi
  if ! wait_for_service "backend" 300; then
    log_error "后端服务未在预期时间内通过健康检查，请执行 \"${COMPOSE_CMD} -f ${COMPOSE_FILE} logs backend\" 查看详情。"
    exit 1
  fi
  run_migrations
  if ! wait_for_service "backend" 120; then
    log_warn "迁移后后端健康检查仍未恢复，请查看日志确认。"
  fi
  DEPLOY_STARTED=0
  popd >/dev/null
}

print_summary() {
  printf "\n"
  log_success "部署完成！"
  printf "\n"
  printf "%b前端地址%b: %s\n" "${BOLD}" "${RESET}" "${FRONTEND_URL}"
  printf "%b后端健康检查%b: %s/health\n" "${BOLD}" "${RESET}" "${BACKEND_URL}"
  printf "%bAPI 文档%b: %s\n" "${BOLD}" "${RESET}" "${DOCS_URL}"
  printf "%b管理员账号%b: %s\n" "${BOLD}" "${RESET}" "${ADMIN_EMAIL}"
  printf "%b管理员密码%b: %s\n" "${BOLD}" "${RESET}" "${ADMIN_PASSWORD}"
  printf "\n日志文件：%s\n" "${LOG_FILE}"
}

handle_cleanup_command() {
  log_step "清理 Docker 资源"
  detect_docker_compose
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    log_warn "未找到 ${COMPOSE_FILE}，无需清理。"
    exit 0
  fi
  if prompt_confirm "确定要停止并删除所有容器、网络和数据卷吗？" "n"; then
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down --volumes --remove-orphans
    log_success "已清理 Docker 资源。"
  else
    log_info "已取消清理操作。"
  fi
  exit 0
}

verify_env_files() {
  if [[ -f "${ENV_FILE}" ]]; then
    if prompt_confirm ".env 已存在，是否覆盖？" "n"; then
      log_info "将覆盖现有 .env 文件。"
    else
      log_info "保留现有 .env 文件。"
      return 1
    fi
  fi
  return 0
}

verify_env_docker_file() {
  if [[ -f "${ENV_DOCKER_FILE}" ]]; then
    if prompt_confirm ".env.docker 已存在，是否覆盖？" "n"; then
      log_info "将覆盖现有 .env.docker 文件。"
    else
      log_info "保留现有 .env.docker 文件。"
      return 1
    fi
  fi
  return 0
}

prepare_compose_file() {
  SHOULD_WRITE_COMPOSE="true"
  if [[ -f "${COMPOSE_FILE}" ]]; then
    if prompt_confirm "检测到现有 docker-compose.yml，是否覆盖为自动生成的模板？" "y"; then
      log_info "将覆盖 docker-compose.yml。"
    else
      log_info "保留现有 docker-compose.yml。"
      SHOULD_WRITE_COMPOSE="false"
    fi
  fi
}

main() {
  if [[ "${1:-}" == "down" ]]; then
    handle_cleanup_command
  fi

  log_step "环境预检查"
  check_os
  check_docker
  check_port 80
  check_port 443
  check_resources

  log_step "交互式配置"
  prompt_domain
  prompt_email
  prompt_admin_email
  prompt_db_path
  prompt_cors
  generate_passwords

  ensure_dirs
  prepare_compose_file

  if verify_env_files; then
    write_env_file
    log_success "已生成 .env"
  fi
  if verify_env_docker_file; then
    write_env_docker_file
    log_success "已生成 .env.docker"
  fi

  write_dynamic_config
  log_success "已生成 Traefik 配置"

  if [[ "${SHOULD_WRITE_COMPOSE}" == "true" ]]; then
    write_compose_file
    log_success "已生成 docker-compose.yml"
  fi

  log_step "启动 Docker Compose 集群"
  start_stack
  print_summary
}

main "$@"
