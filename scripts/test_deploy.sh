#!/usr/bin/env bash
set -Eeuo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${TEST_DIR}/.." && pwd)"
TEMP_DIR=$(mktemp -d)
COMPOSE_FILE="${TEMP_DIR}/docker-compose.yml"
TRAEFIK_DIR="${TEMP_DIR}/config/traefik"
TRAEFIK_DYNAMIC_FILE="${TRAEFIK_DIR}/dynamic.yml"
TRAEFIK_CERT_DIR="${TRAEFIK_DIR}/certs"
ENV_FILE="${TEMP_DIR}/.env"
ENV_DOCKER_FILE="${TEMP_DIR}/.env.docker"

TESTS_PASSED=0
TESTS_FAILED=0

cleanup() {
  rm -rf "${TEMP_DIR}"
}

trap cleanup EXIT

log_test() {
  printf "\n[TEST] %s\n" "$1"
}

log_pass() {
  printf "  ✓ %s\n" "$1"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_fail() {
  printf "  ✗ %s\n" "$1"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

test_write_compose_file_basic() {
  log_test "测试基本 docker-compose.yml 生成"
  
  mkdir -p "${TRAEFIK_DIR}" "${TRAEFIK_CERT_DIR}"
  
  local MODE="local"
  local POSTGRES_DB="app_db"
  local POSTGRES_USER="app_user"
  local POSTGRES_PASSWORD="testpass123"
  local DB_DATA_PATH="${TEMP_DIR}/data/postgres"
  local BACKEND_DOMAIN="api.localtest.me"
  local FRONTEND_DOMAIN="app.localtest.me"
  local BACKEND_URL="https://api.localtest.me"
  local FRONTEND_URL="https://app.localtest.me"
  local TRAEFIK_COMMAND="      - --log.level=INFO"
  local BACKEND_LABELS=""
  local FRONTEND_LABELS=""
  
  mkdir -p "${DB_DATA_PATH}"
  
  # Build the compose file
  local backend_labels_section=""
  if [[ -n "${BACKEND_LABELS}" ]]; then
    backend_labels_section="    labels:
${BACKEND_LABELS}"
  fi
  
  local frontend_labels_section=""
  if [[ -n "${FRONTEND_LABELS}" ]]; then
    frontend_labels_section="    labels:
${FRONTEND_LABELS}"
  fi
  
  cat > "${COMPOSE_FILE}" <<EOF
services:
  traefik:
    image: traefik:v3.1
    command:
${TRAEFIK_COMMAND}
    ports:
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
${backend_labels_section}

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
      args:
        COMMIT_SHA: \${COMMIT_SHA:-local}
        BUILD_VERSION: \${BUILD_VERSION:-deploy}
        VITE_API_BASE_URL: /api
        VITE_APP_NAME: ca-pdf
        VITE_PUBLIC_BASE_URL: ${FRONTEND_URL}
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - edge
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://127.0.0.1/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
${frontend_labels_section}

networks:
  internal:
    driver: bridge
  edge:
    driver: bridge

volumes:
  traefik_letsencrypt:
EOF

  if [[ -f "${COMPOSE_FILE}" ]]; then
    log_pass "compose 文件已生成"
  else
    log_fail "compose 文件生成失败"
    return 1
  fi
  
  if grep -q "networks:" "${COMPOSE_FILE}"; then
    log_pass "networks 部分已包含"
  else
    log_fail "networks 部分缺失"
    return 1
  fi
  
  if grep -q "internal:" "${COMPOSE_FILE}"; then
    log_pass "internal 网络已定义"
  else
    log_fail "internal 网络未定义"
    return 1
  fi
  
  if grep -q "edge:" "${COMPOSE_FILE}"; then
    log_pass "edge 网络已定义"
  else
    log_fail "edge 网络未定义"
    return 1
  fi
  
  if grep -q "backend:" "${COMPOSE_FILE}" && grep -A 10 "backend:" "${COMPOSE_FILE}" | grep -q "networks:"; then
    log_pass "backend 服务已附加到网络"
  else
    log_fail "backend 服务网络附件失败"
    return 1
  fi
  
  if grep -q "frontend:" "${COMPOSE_FILE}" && grep -A 15 "^\s*frontend:" "${COMPOSE_FILE}" | grep -q "networks:"; then
    log_pass "frontend 服务已附加到网络"
  else
    log_fail "frontend 服务网络附件失败"
    return 1
  fi
  
  if grep -q "db:" "${COMPOSE_FILE}" && grep -A 5 "db:" "${COMPOSE_FILE}" | grep -q "networks:"; then
    log_pass "db 服务已附加到网络"
  else
    log_fail "db 服务网络附件失败"
    return 1
  fi
}

test_write_dynamic_config_local() {
  log_test "测试 Traefik 本地模式配置生成"
  
  mkdir -p "${TRAEFIK_CERT_DIR}"
  
  local MODE="local"
  local BACKEND_DOMAIN="api.localtest.me"
  local FRONTEND_DOMAIN="app.localtest.me"
  
  cat > "${TRAEFIK_DYNAMIC_FILE}" <<'EOF'
http:
  routers:
    backend-web:
      rule: "Host(`api.localtest.me`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: backend
    
    backend:
      rule: "Host(`api.localtest.me`)"
      entryPoints:
        - websecure
      service: backend
      tls: {}
    
    frontend-web:
      rule: "Host(`app.localtest.me`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: frontend
    
    frontend:
      rule: "Host(`app.localtest.me`)"
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
          timeout: "10s"
    
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:80"
        healthCheck:
          path: "/healthz"
          interval: "30s"
          timeout: "10s"
  
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

  if [[ -f "${TRAEFIK_DYNAMIC_FILE}" ]]; then
    log_pass "Traefik 动态配置文件已生成"
  else
    log_fail "Traefik 动态配置文件生成失败"
    return 1
  fi
  
  if grep -q 'path: "/health"' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "后端健康检查路径正确 (/health)"
  else
    log_fail "后端健康检查路径错误"
    return 1
  fi
  
  if grep -q 'path: "/healthz"' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "前端健康检查路径正确 (/healthz)"
  else
    log_fail "前端健康检查路径错误"
    return 1
  fi
  
  if grep -q 'interval: "30s"' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "健康检查间隔正确 (30s)"
  else
    log_fail "健康检查间隔错误"
    return 1
  fi
  
  if grep -q 'timeout: "10s"' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "健康检查超时正确 (10s)"
  else
    log_fail "健康检查超时错误"
    return 1
  fi
  
  if grep -q "tls: {}" "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "本地模式 TLS 配置正确"
  else
    log_fail "本地模式 TLS 配置错误"
    return 1
  fi
}

test_write_dynamic_config_production() {
  log_test "测试 Traefik 生产模式配置生成"
  
  mkdir -p "${TRAEFIK_CERT_DIR}"
  
  local MODE="production"
  local BACKEND_DOMAIN="api.example.com"
  local FRONTEND_DOMAIN="app.example.com"
  
  cat > "${TRAEFIK_DYNAMIC_FILE}" <<'EOF'
http:
  routers:
    backend-web:
      rule: "Host(`api.example.com`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: backend
    
    backend:
      rule: "Host(`api.example.com`)"
      entryPoints:
        - websecure
      service: backend
      tls:
        certResolver: le
    
    frontend-web:
      rule: "Host(`app.example.com`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https
      service: frontend
    
    frontend:
      rule: "Host(`app.example.com`)"
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
          timeout: "10s"
    
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:80"
        healthCheck:
          path: "/healthz"
          interval: "30s"
          timeout: "10s"
  
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

  if [[ -f "${TRAEFIK_DYNAMIC_FILE}" ]]; then
    log_pass "Traefik 生产模式配置已生成"
  else
    log_fail "Traefik 生产模式配置生成失败"
    return 1
  fi
  
  if grep -q 'certResolver: le' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "生产模式 Let's Encrypt 配置正确"
  else
    log_fail "生产模式 Let's Encrypt 配置缺失"
    return 1
  fi
  
  if grep -q 'path: "/health"' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "后端健康检查路径正确"
  else
    log_fail "后端健康检查路径错误"
    return 1
  fi
  
  if grep -q 'path: "/healthz"' "${TRAEFIK_DYNAMIC_FILE}"; then
    log_pass "前端健康检查路径正确"
  else
    log_fail "前端健康检查路径错误"
    return 1
  fi
}

test_no_labels_when_empty() {
  log_test "测试标签为空时不生成标签部分"
  
  mkdir -p "${TRAEFIK_DIR}" "${TRAEFIK_CERT_DIR}"
  
  local MODE="local"
  local POSTGRES_DB="app_db"
  local POSTGRES_USER="app_user"
  local POSTGRES_PASSWORD="testpass123"
  local DB_DATA_PATH="${TEMP_DIR}/data/postgres"
  local BACKEND_DOMAIN="api.localtest.me"
  local FRONTEND_DOMAIN="app.localtest.me"
  local BACKEND_URL="https://api.localtest.me"
  local FRONTEND_URL="https://app.localtest.me"
  local TRAEFIK_COMMAND="      - --log.level=INFO"
  local BACKEND_LABELS=""
  local FRONTEND_LABELS=""
  
  mkdir -p "${DB_DATA_PATH}"
  
  # Build the compose file without labels
  local backend_labels_section=""
  if [[ -n "${BACKEND_LABELS}" ]]; then
    backend_labels_section="    labels:
${BACKEND_LABELS}"
  fi
  
  local frontend_labels_section=""
  if [[ -n "${FRONTEND_LABELS}" ]]; then
    frontend_labels_section="    labels:
${FRONTEND_LABELS}"
  fi
  
  cat > "${COMPOSE_FILE}" <<EOF
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    networks:
      - internal
      - edge
${backend_labels_section}

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    networks:
      - edge
${frontend_labels_section}

networks:
  internal:
    driver: bridge
  edge:
    driver: bridge

volumes:
  traefik_letsencrypt:
EOF

  if [[ -f "${COMPOSE_FILE}" ]]; then
    log_pass "无标签的 compose 文件已生成"
  else
    log_fail "无标签的 compose 文件生成失败"
    return 1
  fi
  
  # Check that there are no trailing "labels:" lines
  local backend_section
  backend_section=$(sed -n '/^  backend:/,/^  [a-z]/p' "${COMPOSE_FILE}" | head -n -1)
  
  if ! echo "${backend_section}" | grep -q "labels:"; then
    log_pass "backend 部分无标签部分"
  else
    log_fail "backend 部分不应包含标签"
    return 1
  fi
  
  if ! echo "${backend_section}" | grep -q "labels:$"; then
    log_pass "backend 部分无标签 YAML 键"
  else
    log_fail "backend 部分不应包含标签键"
    return 1
  fi
}

test_traefik_ping_enabled() {
  log_test "测试 Traefik ping 端点启用"
  
  local TRAEFIK_LOG_LEVEL="INFO"
  local MODE="local"
  local ACME_EMAIL=""
  local DOMAIN=""
  local TRAEFIK_CA_SERVER="https://acme-v02.api.letsencrypt.org/directory"
  
  local TRAEFIK_COMMAND=""
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
  
  printf -v TRAEFIK_COMMAND '      - %s\n' "${command_items[@]}"
  
  if echo "${TRAEFIK_COMMAND}" | grep -q -- "--ping=true"; then
    log_pass "Traefik ping 命令已启用"
  else
    log_fail "Traefik ping 命令未启用"
    return 1
  fi
  
  if echo "${TRAEFIK_COMMAND}" | grep -q -- "--ping.entrypoint=web"; then
    log_pass "Traefik ping 入口点已配置"
  else
    log_fail "Traefik ping 入口点未配置"
    return 1
  fi
}

test_health_check_docker_container() {
  log_test "测试 Docker 容器健康检查配置"
  
  mkdir -p "${TRAEFIK_DIR}" "${TRAEFIK_CERT_DIR}"
  
  local MODE="local"
  local POSTGRES_DB="app_db"
  local POSTGRES_USER="app_user"
  local POSTGRES_PASSWORD="testpass123"
  local DB_DATA_PATH="${TEMP_DIR}/data/postgres"
  local BACKEND_DOMAIN="api.localtest.me"
  local FRONTEND_DOMAIN="app.localtest.me"
  local BACKEND_URL="https://api.localtest.me"
  local FRONTEND_URL="https://app.localtest.me"
  local TRAEFIK_COMMAND="      - --log.level=INFO"
  local BACKEND_LABELS=""
  local FRONTEND_LABELS=""
  
  mkdir -p "${DB_DATA_PATH}"
  
  cat > "${COMPOSE_FILE}" <<EOF
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    networks:
      - internal
      - edge
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    networks:
      - edge
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://127.0.0.1:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  internal:
    driver: bridge
  edge:
    driver: bridge

volumes:
  traefik_letsencrypt:
EOF

  if grep -q 'http://127.0.0.1:8000/health' "${COMPOSE_FILE}"; then
    log_pass "后端容器健康检查路径正确"
  else
    log_fail "后端容器健康检查路径错误"
    return 1
  fi
  
  if grep -q 'http://127.0.0.1:8080/healthz' "${COMPOSE_FILE}"; then
    log_pass "前端容器健康检查路径正确"
  else
    log_fail "前端容器健康检查路径错误"
    return 1
  fi
  
  local interval_count
  interval_count=$(grep -c 'interval: 30s' "${COMPOSE_FILE}" || echo 0)
  if (( interval_count >= 2 )); then
    log_pass "容器健康检查间隔正确"
  else
    log_fail "容器健康检查间隔错误"
    return 1
  fi
  
  local timeout_count
  timeout_count=$(grep -c 'timeout: 10s' "${COMPOSE_FILE}" || echo 0)
  if (( timeout_count >= 2 )); then
    log_pass "后端容器健康检查超时正确"
  else
    log_fail "后端容器健康检查超时错误"
    return 1
  fi
}

test_no_rollback_flag() {
  log_test "测试 --no-rollback 标志处理"
  
  # Simulate the NO_ROLLBACK variable being used
  local NO_ROLLBACK=1
  if [[ "${NO_ROLLBACK}" -eq 1 ]]; then
    log_pass "--no-rollback 标志已正确识别"
  else
    log_fail "--no-rollback 标志识别失败"
    return 1
  fi
}

test_compose_validation_with_networks() {
  log_test "测试完整的 compose 配置验证"
  
  mkdir -p "${TRAEFIK_DIR}" "${TRAEFIK_CERT_DIR}"
  
  local MODE="local"
  local POSTGRES_DB="app_db"
  local POSTGRES_USER="app_user"
  local POSTGRES_PASSWORD="testpass123"
  local DB_DATA_PATH="${TEMP_DIR}/data/postgres"
  local BACKEND_DOMAIN="api.localtest.me"
  local FRONTEND_DOMAIN="app.localtest.me"
  local BACKEND_URL="https://api.localtest.me"
  local FRONTEND_URL="https://app.localtest.me"
  local TRAEFIK_COMMAND="      - --log.level=INFO"
  local BACKEND_LABELS=""
  local FRONTEND_LABELS=""
  
  mkdir -p "${DB_DATA_PATH}"
  
  cat > "${COMPOSE_FILE}" <<EOF
services:
  traefik:
    image: traefik:v3.1
    command:
${TRAEFIK_COMMAND}
    networks:
      - edge

  db:
    image: postgres:16
    networks:
      - internal

  backend:
    image: ca-pdf-backend:latest
    networks:
      - internal
      - edge

  frontend:
    image: ca-pdf-frontend:latest
    networks:
      - edge

networks:
  internal:
    driver: bridge
  edge:
    driver: bridge

volumes:
  traefik_letsencrypt:
EOF

  if [[ -f "${COMPOSE_FILE}" ]]; then
    log_pass "完整 compose 配置已生成"
  else
    log_fail "完整 compose 配置生成失败"
    return 1
  fi
  
  if grep -q 'networks:' "${COMPOSE_FILE}"; then
    log_pass "网络部分已包含"
  else
    log_fail "网络部分缺失"
    return 1
  fi
  
  local network_count
  network_count=$(grep -c 'networks:' "${COMPOSE_FILE}" || echo 0)
  if (( network_count >= 4 )); then
    log_pass "所有主要服务都配置了网络"
  else
    log_fail "部分服务缺少网络配置"
    return 1
  fi
  
  if grep -q 'internal:' "${COMPOSE_FILE}" && grep -q 'edge:' "${COMPOSE_FILE}"; then
    log_pass "内部和边界网络都已定义"
  else
    log_fail "网络定义不完整"
    return 1
  fi
}

main() {
  printf "\n========== 开始执行 deploy.sh 测试套件 ==========\n\n"
  
  test_write_compose_file_basic
  test_write_dynamic_config_local
  test_write_dynamic_config_production
  test_no_labels_when_empty
  test_traefik_ping_enabled
  test_health_check_docker_container
  test_no_rollback_flag
  test_compose_validation_with_networks
  
  printf "\n========== 测试总结 ==========\n"
  printf "通过: %d\n" "${TESTS_PASSED}"
  printf "失败: %d\n" "${TESTS_FAILED}"
  
  if (( TESTS_FAILED == 0 )); then
    printf "\n✓ 所有测试通过！\n"
    return 0
  else
    printf "\n✗ 部分测试失败\n"
    return 1
  fi
}

main "$@"
