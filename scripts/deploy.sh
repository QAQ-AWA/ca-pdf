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

on_error() {
  local exit_code=$?
  local line_no=${1:-unknown}
  log_error "脚本执行失败（第 ${line_no} 行，退出码 ${exit_code}）。"
  log_error "请查看日志文件获取详情：${LOG_FILE:-未生成}"
  exit ${exit_code}
}

trap 'on_error "$LINENO"' ERR

SCRIPT_SOURCE="${BASH_SOURCE[0]}"
while [[ -h "${SCRIPT_SOURCE}" ]]; do
  SCRIPT_DIR_TEMP="$(cd -P "$(dirname "${SCRIPT_SOURCE}")" && pwd)"
  SCRIPT_SOURCE="$(readlink "${SCRIPT_SOURCE}")"
  [[ ${SCRIPT_SOURCE} != /* ]] && SCRIPT_SOURCE="${SCRIPT_DIR_TEMP}/${SCRIPT_SOURCE}"
done
DEFAULT_SCRIPT_DIR="$(cd -P "$(dirname "${SCRIPT_SOURCE}")" && pwd)"
DEFAULT_PROJECT_ROOT="$(cd "${DEFAULT_SCRIPT_DIR}/.." && pwd)"

if [[ -n "${CAPDF_HOME:-}" ]]; then
  PROJECT_ROOT="$(cd "${CAPDF_HOME}" && pwd)"
else
  PROJECT_ROOT="${DEFAULT_PROJECT_ROOT}"
fi
SCRIPT_DIR="${PROJECT_ROOT}/scripts"

LOG_DIR="${PROJECT_ROOT}/logs"
BACKUP_DIR="${PROJECT_ROOT}/backups"
mkdir -p "${LOG_DIR}" "${BACKUP_DIR}"
LOG_FILE="${LOG_DIR}/installer-$(date +%Y%m%d).log"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

CAPDF_REMOTE_REPO="${CAPDF_REMOTE_REPO:-QAQ-AWA/ca-pdf}"
CAPDF_CHANNEL_FILE="${PROJECT_ROOT}/.capdf-channel"
if [[ -z "${CAPDF_CHANNEL:-}" && -f "${CAPDF_CHANNEL_FILE}" ]]; then
  CAPDF_CHANNEL="$(<"${CAPDF_CHANNEL_FILE}")"
fi
CAPDF_CHANNEL="${CAPDF_CHANNEL:-main}"
CAPDF_CHANNEL="$(printf "%s" "${CAPDF_CHANNEL}" | tr -d ' \n\r')"
CAPDF_RAW_BASE_URL="https://raw.githubusercontent.com/${CAPDF_REMOTE_REPO}/${CAPDF_CHANNEL}"

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
FORCE_CLEAN=0
FORCE_REBUILD=0
NO_CACHE=0
FORCE_STOP=0
SKIP_VALIDATION=0

on_error() {
  local exit_code=$?
  local line_no=${1:-unknown}
  log_error "部署失败（第 ${line_no} 行，退出码 ${exit_code}）。"
  if (( DEPLOY_STARTED )); then
    log_warn "正在回滚 Docker 容器..."
    if command -v docker >/dev/null 2>&1; then
      ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true
      log_info "清理部分构建的镜像..."
      docker image prune -f --filter "dangling=true" >/dev/null 2>&1 || true
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

compose() {
  detect_docker_compose
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    log_error "未找到 ${COMPOSE_FILE}，请先运行 capdf install 生成配置。"
    exit 1
  fi
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" "$@"
}

is_stack_running() {
  detect_docker_compose
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    return 1
  fi
  local status
  status=$(${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps 2>/dev/null || true)
  if echo "${status}" | grep -qE "Up|running"; then
    return 0
  fi
  return 1
}

ensure_env_ready() {
  if [[ ! -f "${ENV_FILE}" || ! -f "${ENV_DOCKER_FILE}" ]]; then
    log_error "缺少必要的环境文件，请先运行 capdf install 完成初始化。"
    exit 1
  fi
}

print_runtime_summary() {
  local frontend_url backend_url docs_url
  frontend_url=$(get_env_var "VITE_PUBLIC_BASE_URL")
  backend_url=$(get_env_var "VITE_API_BASE_URL")
  if [[ -z "${frontend_url}" ]]; then
    frontend_url=$(get_env_var "FRONTEND_URL" "https://app.localtest.me")
  fi
  if [[ -z "${backend_url}" ]]; then
    backend_url=$(get_env_var "BACKEND_URL" "https://api.localtest.me")
  fi
  docs_url="${backend_url%/}/docs"
  printf "\n"
  log_info "访问入口："
  printf "  %b前端%b: %s\n" "${BOLD}" "${RESET}" "${frontend_url}"
  printf "  %b后端健康检查%b: %s/health\n" "${BOLD}" "${RESET}" "${backend_url}"
  printf "  %bAPI 文档%b: %s\n" "${BOLD}" "${RESET}" "${docs_url}"
}

doctor_check_port() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    if ss -ltn "sport = :${port}" 2>/dev/null | grep -q ":${port}"; then
      log_warn "端口 ${port} 已被占用。"
    else
      log_success "端口 ${port} 可用。"
    fi
  elif command -v lsof >/dev/null 2>&1; then
    if lsof -i "TCP:${port}" -sTCP:LISTEN -P -n >/dev/null 2>&1; then
      log_warn "端口 ${port} 已被占用。"
    else
      log_success "端口 ${port} 可用。"
    fi
  else
    log_warn "无法检测端口 ${port} 是否占用（缺少 ss/lsof）。"
  fi
}

download_from_repo() {
  local channel="$1"
  local remote_path="$2"
  local target_path="$3"
  local base="https://raw.githubusercontent.com/${CAPDF_REMOTE_REPO}/${channel}"
  curl -fsSL --retry 3 --retry-delay 1 --retry-connrefused "${base}/${remote_path}" -o "${target_path}.tmp"
  mv "${target_path}.tmp" "${target_path}"
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
  local force_stop="${2:-0}"
  local port_in_use=0
  local process_info=""
  
  if command -v ss >/dev/null 2>&1; then
    if ss -ltn "sport = :${port}" 2>/dev/null | grep -q ":${port}"; then
      port_in_use=1
      process_info=$(ss -ltnp "sport = :${port}" 2>/dev/null | grep ":${port}" | head -n1 || echo "未知进程")
    fi
  elif command -v lsof >/dev/null 2>&1; then
    if lsof -i "TCP:${port}" -sTCP:LISTEN -P -n >/dev/null 2>&1; then
      port_in_use=1
      process_info=$(lsof -i "TCP:${port}" -sTCP:LISTEN -P -n 2>/dev/null | tail -n1 || echo "未知进程")
    fi
  else
    log_warn "无法检测端口 ${port} 是否占用（缺少 ss/lsof），请自行确认。"
    return 0
  fi
  
  if (( port_in_use )); then
    log_warn "端口 ${port} 已被占用"
    log_info "占用信息: ${process_info}"
    
    if (( force_stop )); then
      log_info "尝试停止占用端口 ${port} 的 Docker 容器..."
      local containers
      containers=$(docker ps --format '{{.Names}}' --filter "publish=${port}" 2>/dev/null || true)
      if [[ -n "${containers}" ]]; then
        echo "${containers}" | while read -r container; do
          log_info "停止容器: ${container}"
          docker stop "${container}" >/dev/null 2>&1 || true
        done
        sleep 2
        if command -v ss >/dev/null 2>&1; then
          if ss -ltn "sport = :${port}" 2>/dev/null | grep -q ":${port}"; then
            log_error "端口 ${port} 仍被占用，请手动释放后重试。"
            exit 1
          fi
        fi
        log_success "已停止占用端口 ${port} 的容器"
      else
        log_error "端口 ${port} 未被 Docker 容器占用，无法自动停止。请手动释放。"
        log_info "提示: lsof -i :${port} 查看占用进程"
        exit 1
      fi
    else
      log_error "端口 ${port} 已被占用，请释放后重试。"
      log_info "提示: 使用 --force-stop 参数可自动停止占用端口的容器"
      exit 1
    fi
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

clean_old_data() {
  local force="${1:-0}"
  local should_clean=0
  
  detect_docker_compose
  
  local has_existing=0
  if [[ -f "${COMPOSE_FILE}" ]] && is_stack_running; then
    has_existing=1
  fi
  
  local data_path="${DB_DATA_PATH:-${PROJECT_ROOT}/data/postgres}"
  if [[ -d "${data_path}" && -n "$(ls -A "${data_path}" 2>/dev/null)" ]]; then
    has_existing=1
  fi
  
  if (( !has_existing )); then
    return 0
  fi
  
  if (( force )); then
    should_clean=1
    log_info "检测到 --force-clean 参数，将清理旧数据"
  else
    log_warn "检测到已存在的数据"
    if [[ -f "${COMPOSE_FILE}" ]]; then
      log_info "  - Docker Compose 配置和容器"
    fi
    if [[ -d "${data_path}" ]]; then
      log_info "  - PostgreSQL 数据目录: ${data_path}"
    fi
    if prompt_confirm "是否清理旧数据并重新开始？" "n"; then
      should_clean=1
    fi
  fi
  
  if (( should_clean )); then
    log_step "清理旧数据"
    
    if [[ -f "${COMPOSE_FILE}" ]]; then
      log_info "停止并删除容器和数据卷..."
      ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down -v --remove-orphans >/dev/null 2>&1 || true
    fi
    
    if [[ -d "${data_path}" ]]; then
      log_info "删除 PostgreSQL 数据目录..."
      rm -rf "${data_path}"
    fi
    
    local volumes
    volumes=$(docker volume ls -q 2>/dev/null | grep -E "ca_pdf|ca-pdf" || true)
    if [[ -n "${volumes}" ]]; then
      log_info "删除相关 Docker 数据卷..."
      echo "${volumes}" | xargs -r docker volume rm >/dev/null 2>&1 || true
    fi
    
    log_success "旧数据清理完成"
  else
    log_info "保留现有数据"
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

  # Note: Routers are now defined in dynamic.yml (file provider)
  # Docker labels are not needed for routing as file-based config takes precedence
  BACKEND_LABELS=""
  FRONTEND_LABELS=""
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
  routers:
    # Backend HTTP router (redirect to HTTPS)
    backend-web:
      rule: "Host(\`${BACKEND_DOMAIN}\`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: backend
    
    # Backend HTTPS router
    backend:
      rule: "Host(\`${BACKEND_DOMAIN}\`)"
      entryPoints:
        - websecure
      service: backend
      tls: {}
    
    # Frontend HTTP router (redirect to HTTPS)
    frontend-web:
      rule: "Host(\`${FRONTEND_DOMAIN}\`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: frontend
    
    # Frontend HTTPS router
    frontend:
      rule: "Host(\`${FRONTEND_DOMAIN}\`)"
      entryPoints:
        - websecure
      service: frontend
      tls: {}
  
  services:
    backend:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
        healthCheck:
          path: "/health"
          interval: "30s"
          timeout: "5s"
    
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:8080"
        healthCheck:
          path: "/"
          interval: "30s"
          timeout: "5s"
  
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
    cat >"${TRAEFIK_DYNAMIC_FILE}" <<EOF
http:
  routers:
    # Backend HTTP router (redirect to HTTPS)
    backend-web:
      rule: "Host(\`${BACKEND_DOMAIN}\`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: backend
    
    # Backend HTTPS router
    backend:
      rule: "Host(\`${BACKEND_DOMAIN}\`)"
      entryPoints:
        - websecure
      service: backend
      tls:
        certResolver: le
    
    # Frontend HTTP router (redirect to HTTPS)
    frontend-web:
      rule: "Host(\`${FRONTEND_DOMAIN}\`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: frontend
    
    # Frontend HTTPS router
    frontend:
      rule: "Host(\`${FRONTEND_DOMAIN}\`)"
      entryPoints:
        - websecure
      service: frontend
      tls:
        certResolver: le
  
  services:
    backend:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
        healthCheck:
          path: "/health"
          interval: "30s"
          timeout: "5s"
    
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:8080"
        healthCheck:
          path: "/"
          interval: "30s"
          timeout: "5s"
  
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
  if ! ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T backend alembic upgrade head; then
    log_error "数据库迁移失败"
    log_info "提示: 查看日志 capdf logs backend"
    exit 1
  fi
  log_success "数据库迁移完成"
}

validate_deployment() {
  log_step "验证部署状态"
  
  local backend_url
  backend_url=$(get_env_var "VITE_API_BASE_URL" "https://api.localtest.me")
  
  log_info "检查服务运行状态..."
  local services_running=0
  local expected_services=("traefik" "db" "backend" "frontend")
  local running_services
  running_services=$(${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps --services --filter "status=running" 2>/dev/null || true)
  
  for service in "${expected_services[@]}"; do
    if echo "${running_services}" | grep -q "^${service}$"; then
      log_success "服务 ${service} 运行中"
      services_running=$((services_running + 1))
    else
      log_warn "服务 ${service} 未运行"
    fi
  done
  
  if (( services_running < ${#expected_services[@]} )); then
    log_warn "部分服务未启动（${services_running}/${#expected_services[@]}）"
  else
    log_success "所有服务运行正常（${services_running}/${#expected_services[@]}）"
  fi
  
  log_info "验证后端 API..."
  if command -v curl >/dev/null 2>&1; then
    if curl -fsSL -k --max-time 10 "${backend_url}/health" >/dev/null 2>&1; then
      log_success "后端 API 健康检查通过: ${backend_url}/health"
    else
      log_warn "无法访问后端 API: ${backend_url}/health"
      log_info "这可能需要几分钟时间，请稍后使用 'capdf doctor' 检查"
    fi
  fi
  
  log_success "部署验证完成"
}

start_stack() {
  detect_docker_compose
  pushd "${PROJECT_ROOT}" >/dev/null
  export COMPOSE_PROJECT_NAME=ca_pdf
  export COMPOSE_DOCKER_CLI_BUILD=1
  export DOCKER_BUILDKIT=1
  DEPLOY_STARTED=1
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" pull --quiet traefik db >/dev/null 2>&1 || true
  
  local build_args=""
  if (( NO_CACHE )) || (( FORCE_REBUILD )); then
    log_info "使用 --no-cache 构建镜像（忽略缓存）"
    build_args="--no-cache"
  fi
  
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d --build ${build_args}
  
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
  
  if (( !SKIP_VALIDATION )); then
    validate_deployment
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

stop_stack() {
  detect_docker_compose
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    log_warn "未找到 ${COMPOSE_FILE}，跳过停止操作。"
    return
  fi
  log_step "停止 Docker Compose 集群"
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans
  log_success "服务已停止。"
}

restart_stack() {
  stop_stack
  log_step "重新启动 Docker Compose 集群"
  start_stack
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

get_env_var() {
  local key="$1"
  local default_value="${2:-}"
  local file line value
  for file in "${ENV_FILE}" "${ENV_DOCKER_FILE}"; do
    if [[ -f "${file}" ]]; then
      line=$(grep -E "^${key}=" "${file}" | tail -n1 || true)
      if [[ -n "${line}" ]]; then
        value="${line#*=}"
        value="${value%%#*}"
        value="$(printf '%s' "${value}" | sed -e 's/\\r$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        printf '%s' "${value}"
        return 0
      fi
    fi
  done
  if [[ -n "${default_value}" ]]; then
    printf '%s' "${default_value}"
    return 0
  fi
  return 1
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

command_install() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force-clean)
        FORCE_CLEAN=1
        shift
        ;;
      --no-cache)
        NO_CACHE=1
        shift
        ;;
      --force-stop)
        FORCE_STOP=1
        shift
        ;;
      --skip-validation)
        SKIP_VALIDATION=1
        shift
        ;;
      *)
        log_warn "未知参数: $1"
        shift
        ;;
    esac
  done

  log_step "环境预检查"
  check_os
  check_docker
  check_port 80 "${FORCE_STOP}"
  check_port 443 "${FORCE_STOP}"
  check_port 5432 "${FORCE_STOP}"
  check_port 8000 "${FORCE_STOP}"
  check_resources

  log_step "交互式配置"
  prompt_domain
  prompt_email
  prompt_admin_email
  prompt_db_path
  prompt_cors
  generate_passwords

  clean_old_data "${FORCE_CLEAN}"

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

command_up() {
  ensure_env_ready
  log_step "启动 ca-pdf 服务"
  start_stack
  print_runtime_summary
}

command_down() {
  if [[ "${1:-}" == "--clean" ]]; then
    handle_cleanup_command
  else
    stop_stack
  fi
}

command_restart() {
  ensure_env_ready
  restart_stack
  print_runtime_summary
}

command_logs() {
  ensure_env_ready
  if [[ $# -eq 0 ]]; then
    compose logs --tail 200 -f
  else
    compose logs "$@"
  fi
}

command_status() {
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    log_warn "未找到 ${COMPOSE_FILE}，请先运行 capdf install。"
    return
  fi
  compose ps
}

command_migrate() {
  ensure_env_ready
  detect_docker_compose
  local started_temp=0
  if ! is_stack_running; then
    log_warn "服务未运行，将临时启动数据库和后端用于迁移。"
    compose up -d db backend
    started_temp=1
    if ! wait_for_service "db" 180; then
      log_error "数据库启动失败，无法执行迁移。"
      exit 1
    fi
    if ! wait_for_service "backend" 300; then
      log_error "后端启动失败，无法执行迁移。"
      exit 1
    fi
  fi
  run_migrations
  if [[ ${started_temp} -eq 1 ]]; then
    compose stop backend
    compose stop db
    log_info "已停止临时启动的容器。"
  fi
}

command_backup() {
  ensure_env_ready
  detect_docker_compose
  local timestamp backup_path tmp_dir db_name db_user data_path
  timestamp=$(date +%Y%m%d%H%M%S)
  backup_path="${BACKUP_DIR}/capdf-backup-${timestamp}.tar.gz"
  tmp_dir=$(mktemp -d)
  db_name=$(get_env_var "POSTGRES_DB" "app_db")
  db_user=$(get_env_var "POSTGRES_USER" "app_user")
  data_path=$(get_env_var "POSTGRES_DATA_PATH")

  local started_temp=0
  if ! is_stack_running; then
    log_warn "服务未运行，将临时启动数据库用于备份。"
    compose up -d db
    started_temp=1
    if ! wait_for_service "db" 180; then
      log_error "数据库启动失败，无法执行备份。"
      rm -rf "${tmp_dir}"
      exit 1
    fi
  fi

  log_step "导出数据库 ${db_name}"
  if ! ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T db pg_dump -U "${db_user}" "${db_name}" > "${tmp_dir}/postgres.sql"; then
    rm -rf "${tmp_dir}"
    log_error "数据库导出失败。"
    exit 1
  fi

  mkdir -p "${tmp_dir}/env"
  cp -f "${ENV_FILE}" "${tmp_dir}/env/.env"
  cp -f "${ENV_DOCKER_FILE}" "${tmp_dir}/env/.env.docker"
  if [[ -d "${PROJECT_ROOT}/config" ]]; then
    cp -a "${PROJECT_ROOT}/config" "${tmp_dir}/config"
  fi
  if [[ -n "${data_path}" && -d "${data_path}" ]]; then
    cp -a "${data_path}" "${tmp_dir}/postgres_data"
  fi

  tar -czf "${backup_path}" -C "${tmp_dir}" .
  rm -rf "${tmp_dir}"

  if [[ ${started_temp} -eq 1 ]]; then
    compose stop db
  fi

  log_success "备份完成：${backup_path}"
}

command_restore() {
  ensure_env_ready
  local backup_file="${1:-}"
  if [[ -z "${backup_file}" ]]; then
    read -r -p "请输入备份文件路径: " backup_file || true
  fi
  backup_file=$(echo "${backup_file}" | xargs)
  if [[ -z "${backup_file}" ]]; then
    log_error "未提供备份文件。"
    exit 1
  fi
  if [[ ! -f "${backup_file}" ]]; then
    log_error "备份文件不存在：${backup_file}"
    exit 1
  fi
  if ! prompt_confirm "恢复将覆盖当前配置与数据，确认继续？" "n"; then
    log_info "已取消恢复操作。"
    return
  fi

  stop_stack

  local tmp_dir
  tmp_dir=$(mktemp -d)
  tar -xzf "${backup_file}" -C "${tmp_dir}"
  if [[ -f "${tmp_dir}/env/.env" ]]; then
    cp -f "${tmp_dir}/env/.env" "${ENV_FILE}"
  fi
  if [[ -f "${tmp_dir}/env/.env.docker" ]]; then
    cp -f "${tmp_dir}/env/.env.docker" "${ENV_DOCKER_FILE}"
  fi
  if [[ -d "${tmp_dir}/config" ]]; then
    rm -rf "${PROJECT_ROOT}/config"
    cp -a "${tmp_dir}/config" "${PROJECT_ROOT}/config"
  fi

  local data_path
  data_path=$(get_env_var "POSTGRES_DATA_PATH")
  if [[ -n "${data_path}" && -d "${tmp_dir}/postgres_data" ]]; then
    rm -rf "${data_path}"
    cp -a "${tmp_dir}/postgres_data" "${data_path}"
  fi

  detect_docker_compose
  compose up -d db
  if ! wait_for_service "db" 180; then
    rm -rf "${tmp_dir}"
    log_error "数据库启动失败，无法恢复。"
    exit 1
  fi

  local db_name db_user
  db_name=$(get_env_var "POSTGRES_DB" "app_db")
  db_user=$(get_env_var "POSTGRES_USER" "app_user")
  log_step "恢复数据库 ${db_name}"
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T db bash -c "psql -U ${db_user} -d postgres -c \"DROP DATABASE IF EXISTS \\\"${db_name}\\\";\""
  ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T db bash -c "psql -U ${db_user} -d postgres -c \"CREATE DATABASE \\\"${db_name}\\\";\""
  if ! ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T db psql -U "${db_user}" -d "${db_name}" < "${tmp_dir}/postgres.sql"; then
    rm -rf "${tmp_dir}"
    log_error "数据库恢复失败。"
    exit 1
  fi

  rm -rf "${tmp_dir}"
  compose stop db

  log_success "备份恢复完成，可执行 capdf up 重新启动服务。"
}

command_config() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    log_warn "尚未初始化配置，请运行 capdf install。"
    if prompt_confirm "是否现在运行安装向导？" "y"; then
      command_install
    fi
    return
  fi
  log_step "当前配置信息"
  log_info "管理员邮箱: $(get_env_var "ADMIN_EMAIL")"
  log_info "CORS 配置: $(get_env_var "BACKEND_CORS_ORIGINS")"
  log_info "数据库名称: $(get_env_var "POSTGRES_DB")"
  if prompt_confirm "是否重新运行配置向导以更新以上信息？" "n"; then
    command_install
  fi
}

command_doctor() {
  log_step "======== ca-pdf 系统诊断 ========" 
  
  log_step "1. 操作系统检查"
  check_os
  if [[ -f /etc/os-release ]]; then
    local os_name os_version
    os_name=$(grep "^NAME=" /etc/os-release | cut -d'"' -f2)
    os_version=$(grep "^VERSION=" /etc/os-release | cut -d'"' -f2 || echo "未知")
    log_info "发行版: ${os_name} ${os_version}"
  fi
  
  log_step "2. Docker 环境检查"
  check_docker
  if command -v docker >/dev/null 2>&1; then
    local docker_root
    docker_root=$(docker info 2>/dev/null | grep "Docker Root Dir" | cut -d: -f2 | xargs || echo "未知")
    log_info "Docker 数据目录: ${docker_root}"
    
    if docker ps >/dev/null 2>&1; then
      log_success "Docker 守护进程运行正常"
    else
      log_error "无法连接到 Docker 守护进程"
      log_info "请执行: sudo systemctl status docker"
    fi
  fi
  
  log_step "3. 系统资源检查"
  check_resources
  
  log_step "4. 网络检查"
  if command -v ping >/dev/null 2>&1; then
    if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
      log_success "外网连接正常"
    else
      log_warn "无法连接到外网"
    fi
  fi
  
  if command -v host >/dev/null 2>&1 || command -v nslookup >/dev/null 2>&1; then
    if host github.com >/dev/null 2>&1 || nslookup github.com >/dev/null 2>&1; then
      log_success "DNS 解析正常"
    else
      log_warn "DNS 解析可能存在问题"
    fi
  fi
  
  log_step "5. 端口检查"
  doctor_check_port 80
  doctor_check_port 443
  doctor_check_port 8000
  doctor_check_port 3000
  doctor_check_port 5432

  log_step "6. 配置文件检查"
  if [[ -f "${ENV_FILE}" ]]; then
    log_success "环境配置文件存在: .env"
    local cors
    cors=$(get_env_var "BACKEND_CORS_ORIGINS")
    if [[ -n "${cors}" ]]; then
      if validate_json_list "${cors}"; then
        log_success "BACKEND_CORS_ORIGINS 格式正确"
      else
        log_warn "BACKEND_CORS_ORIGINS 不是合法 JSON 列表：${cors}"
      fi
    fi
    
    local master_key
    master_key=$(get_env_var "ENCRYPTED_STORAGE_MASTER_KEY")
    if [[ -n "${master_key}" ]]; then
      log_success "加密主密钥已配置"
    else
      log_warn "未找到加密主密钥配置"
    fi
  else
    log_error "环境配置文件不存在，请先运行 capdf install"
  fi
  
  if [[ -f "${ENV_DOCKER_FILE}" ]]; then
    log_success "Docker 配置文件存在: .env.docker"
  else
    log_warn "Docker 配置文件不存在: .env.docker"
  fi
  
  if [[ -f "${COMPOSE_FILE}" ]]; then
    log_success "Compose 配置文件存在: docker-compose.yml"
    if command -v docker >/dev/null 2>&1; then
      if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" config >/dev/null 2>&1; then
        log_success "docker-compose.yml 语法正确"
      else
        log_error "docker-compose.yml 语法错误，请检查"
      fi
    fi
  else
    log_warn "Compose 配置文件不存在，请先运行 capdf install"
  fi
  
  log_step "7. 项目文件检查"
  local required_dirs=("backend" "frontend" "scripts")
  local missing_dirs=0
  for dir in "${required_dirs[@]}"; do
    if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
      log_success "目录存在: ${dir}/"
    else
      log_error "目录缺失: ${dir}/"
      missing_dirs=$((missing_dirs + 1))
    fi
  done

  log_step "8. 容器状态检查"
  if is_stack_running; then
    log_info "容器状态："
    compose ps
    
    local db_user db_name
    db_user=$(get_env_var "POSTGRES_USER" "app_user")
    db_name=$(get_env_var "POSTGRES_DB" "app_db")
    
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T db pg_isready -U "${db_user}" -d "${db_name}" >/dev/null 2>&1; then
      log_success "数据库连接正常"
    else
      log_warn "数据库连接检查失败"
      log_info "请执行: capdf logs db"
    fi
    
    local backend_url
    backend_url=$(get_env_var "VITE_API_BASE_URL" "https://api.localtest.me")
    if command -v curl >/dev/null 2>&1; then
      if curl -fsSL -k "${backend_url}/health" >/dev/null 2>&1; then
        log_success "后端 API 健康检查通过"
      else
        log_warn "无法访问后端 API: ${backend_url}/health"
        log_info "请执行: capdf logs backend"
      fi
    fi
  else
    log_warn "容器当前未运行"
    log_info "启动服务: capdf up"
  fi
  
  log_step "======== 诊断完成 ========" 
  log_info "如有问题，请查看日志: ${LOG_FILE}"
  log_info "导出诊断信息: capdf export-logs"
}

command_self_update() {
  local channel="${1:-${CAPDF_CHANNEL}}"
  if [[ -z "${channel}" ]]; then
    channel="main"
  fi
  log_step "从 ${CAPDF_REMOTE_REPO}@${channel} 拉取最新脚本"
  download_from_repo "${channel}" "scripts/deploy.sh" "${SCRIPT_DIR}/deploy.sh"
  chmod +x "${SCRIPT_DIR}/deploy.sh"
  download_from_repo "${channel}" "scripts/install.sh" "${SCRIPT_DIR}/install.sh"
  chmod +x "${SCRIPT_DIR}/install.sh"
  download_from_repo "${channel}" ".env.example" "${PROJECT_ROOT}/.env.example"
  download_from_repo "${channel}" ".env.docker.example" "${PROJECT_ROOT}/.env.docker.example"
  download_from_repo "${channel}" "docker-compose.yml" "${PROJECT_ROOT}/docker-compose.example.yml"
  echo "${channel}" > "${CAPDF_CHANNEL_FILE}"
  log_success "自更新完成（频道：${channel}）。"
  log_info "如需立即应用新脚本，请重新运行 capdf。"
}

command_export_logs() {
  local timestamp export_file tmp_dir
  timestamp=$(date +%Y%m%d%H%M%S)
  export_file="${BACKUP_DIR}/capdf-logs-${timestamp}.tar.gz"
  tmp_dir=$(mktemp -d)
  
  log_step "收集诊断日志"
  
  mkdir -p "${tmp_dir}/logs"
  mkdir -p "${tmp_dir}/config"
  mkdir -p "${tmp_dir}/system"
  
  if [[ -d "${LOG_DIR}" ]]; then
    cp -r "${LOG_DIR}"/* "${tmp_dir}/logs/" 2>/dev/null || true
    log_info "已收集安装日志"
  fi
  
  if is_stack_running; then
    detect_docker_compose
    log_info "导出容器日志..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs --no-color > "${tmp_dir}/logs/docker-compose.log" 2>&1 || true
    for service in traefik db backend frontend; do
      ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs --no-color "${service}" > "${tmp_dir}/logs/${service}.log" 2>&1 || true
    done
    log_info "已收集容器日志"
  fi
  
  if [[ -f "${ENV_FILE}" ]]; then
    grep -v -E "PASSWORD|SECRET|KEY" "${ENV_FILE}" > "${tmp_dir}/config/env.sanitized" 2>/dev/null || true
    log_info "已收集环境配置（已脱敏）"
  fi
  
  if [[ -f "${COMPOSE_FILE}" ]]; then
    cp "${COMPOSE_FILE}" "${tmp_dir}/config/docker-compose.yml" 2>/dev/null || true
    log_info "已收集 Compose 配置"
  fi
  
  {
    echo "=== 系统信息 ==="
    uname -a
    echo ""
    echo "=== 发行版信息 ==="
    cat /etc/os-release 2>/dev/null || echo "未知"
    echo ""
    echo "=== Docker 版本 ==="
    docker --version 2>&1 || echo "Docker 未安装"
    echo ""
    echo "=== Docker Compose 版本 ==="
    docker compose version 2>&1 || docker-compose --version 2>&1 || echo "Docker Compose 未安装"
    echo ""
    echo "=== 内存信息 ==="
    free -h 2>/dev/null || echo "无法获取"
    echo ""
    echo "=== 磁盘信息 ==="
    df -h 2>/dev/null || echo "无法获取"
    echo ""
    echo "=== 网络信息 ==="
    ip addr show 2>/dev/null || ifconfig 2>/dev/null || echo "无法获取"
  } > "${tmp_dir}/system/system-info.txt"
  log_info "已收集系统信息"
  
  if is_stack_running; then
    docker ps -a > "${tmp_dir}/system/docker-ps.txt" 2>&1 || true
    docker images > "${tmp_dir}/system/docker-images.txt" 2>&1 || true
    docker network ls > "${tmp_dir}/system/docker-networks.txt" 2>&1 || true
    log_info "已收集 Docker 状态"
  fi
  
  tar -czf "${export_file}" -C "${tmp_dir}" . 2>/dev/null || {
    log_error "打包日志失败"
    rm -rf "${tmp_dir}"
    return 1
  }
  
  rm -rf "${tmp_dir}"
  
  log_success "诊断日志已导出到: ${export_file}"
  log_info "请将此文件发送给技术支持以获取帮助"
  log_info "GitHub Issues: https://github.com/${CAPDF_REMOTE_REPO}/issues"
}

command_uninstall() {
  if ! prompt_confirm "确认卸载 ca-pdf 并停止所有容器？" "n"; then
    log_info "已取消卸载操作。"
    return
  fi
  stop_stack
  if prompt_confirm "是否删除当前配置和数据文件？" "n"; then
    rm -f "${ENV_FILE}" "${ENV_DOCKER_FILE}" "${COMPOSE_FILE}"
    rm -rf "${TRAEFIK_DIR}"
    local data_path
    data_path=$(get_env_var "POSTGRES_DATA_PATH")
    if [[ -n "${data_path}" ]]; then
      rm -rf "${data_path}"
    fi
    log_success "已删除配置与数据。"
  else
    log_info "保留配置与数据文件。"
  fi
  log_warn "如需彻底移除脚本，可删除目录：${PROJECT_ROOT}"
}

show_menu() {
  while true; do
    printf "\n%bca-pdf 运维菜单%b\n" "${BOLD}" "${RESET}"
    cat <<'MENU'
[1] 安装 / 初始化
[2] 启动服务
[3] 停止服务
[4] 重启服务
[5] 查看日志
[6] 查看状态
[7] 执行数据库迁移
[8] 创建备份
[9] 恢复备份
[10] 配置管理
[11] 健康检查
[12] 导出诊断日志
[13] 自更新
[14] 卸载
[0] 退出
MENU
    read -r -p "请选择操作: " choice || true
    case "${choice}" in
      1)
        command_install
        ;;
      2)
        command_up
        ;;
      3)
        command_down
        ;;
      4)
        command_restart
        ;;
      5)
        read -r -p "输入服务名称（留空为全部）: " svc || true
        if [[ -n "${svc}" ]]; then
          command_logs "${svc}"
        else
          command_logs
        fi
        ;;
      6)
        command_status
        ;;
      7)
        command_migrate
        ;;
      8)
        command_backup
        ;;
      9)
        read -r -p "备份文件路径: " backup_path || true
        command_restore "${backup_path}"
        ;;
      10)
        command_config
        ;;
      11)
        command_doctor
        ;;
      12)
        command_export_logs
        ;;
      13)
        read -r -p "更新频道（默认: ${CAPDF_CHANNEL}）: " new_channel || true
        command_self_update "${new_channel}"
        ;;
      14)
        command_uninstall
        ;;
      0)
        log_info "已退出。"
        break
        ;;
      *)
        log_warn "无效选择，请重新输入。"
        ;;
    esac
  done
}

print_help() {
  cat <<'USAGE'
用法: capdf <命令> [参数]

可用命令：
  install [选项]    运行安装向导
  up                启动服务
  down [--clean]    停止服务（--clean 同时清理数据卷）
  restart           重启服务
  logs [args]       查看日志（参数将传递给 docker compose logs）
  status            查看容器状态
  migrate           执行数据库迁移
  backup            创建备份归档
  restore [file]    还原备份
  config            查看或重新配置环境
  doctor            运行完整系统诊断
  export-logs       导出诊断日志供技术支持使用
  self-update [ch]  从指定分支/频道更新脚本
  uninstall         卸载并停止服务
  menu              打开交互式菜单
  help              显示帮助信息

install 命令选项：
  --force-clean       强制清理旧数据卷和 PostgreSQL 数据目录
  --no-cache          Docker 镜像构建时不使用缓存（强制重新构建）
  --force-stop        自动停止占用端口 (80/443/5432/8000) 的 Docker 容器
  --skip-validation   跳过部署后的验证步骤（不推荐）

示例：
  capdf install                            # 首次安装
  capdf install --force-clean              # 清理旧数据后重新安装
  capdf install --no-cache                 # 强制重新构建镜像
  capdf install --force-stop               # 自动停止冲突容器
  capdf install --force-clean --no-cache   # 完全清理并重建
  capdf up                                 # 启动服务
  capdf doctor                             # 健康检查
  capdf logs backend                       # 查看后端日志
  capdf backup                             # 创建备份
  capdf export-logs                        # 导出诊断日志

部署流程（install 命令执行步骤）：
  1. ✓ 环境预检查（操作系统、Docker、端口、资源）
  2. ✓ 端口占用检查（80/443/5432/8000）
  3. ✓ 交互式配置（域名、邮箱、数据库路径、CORS）
  4. ✓ 旧数据清理提示（可选）
  5. ✓ 生成配置文件（.env、docker-compose.yml）
  6. ✓ Docker Compose 启动（支持缓存控制）
  7. ✓ Alembic 数据库迁移验证
  8. ✓ 服务健康检查验证
  9. ✓ 部署失败自动回滚清理

更多帮助：https://github.com/QAQ-AWA/ca-pdf
USAGE
}

main() {
  local command="${1:-menu}";
  shift || true
  case "${command}" in
    install)
      command_install "$@"
      ;;
    up)
      command_up "$@"
      ;;
    down)
      command_down "$@"
      ;;
    restart)
      command_restart "$@"
      ;;
    logs)
      command_logs "$@"
      ;;
    status)
      command_status "$@"
      ;;
    migrate)
      command_migrate "$@"
      ;;
    backup)
      command_backup "$@"
      ;;
    restore)
      command_restore "$@"
      ;;
    config)
      command_config "$@"
      ;;
    doctor)
      command_doctor "$@"
      ;;
    export-logs)
      command_export_logs "$@"
      ;;
    self-update)
      command_self_update "$@"
      ;;
    uninstall)
      command_uninstall "$@"
      ;;
    menu|interactive)
      show_menu
      ;;
    help|-h|--help)
      print_help
      ;;
    *)
      log_error "未知命令: ${command}"
      print_help
      exit 1
      ;;
  esac
}

main "$@"

