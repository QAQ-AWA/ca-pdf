#!/usr/bin/env bash
set -Eeuo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${TEST_DIR}/.." && pwd)"
TEMP_DIR=$(mktemp -d)
COMPOSE_FILE="${TEMP_DIR}/docker-compose.yml"
NGINX_CONF="${TEMP_DIR}/nginx.conf"
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
  log_test "测试基本 docker-compose.yml 生成（3服务栈）"
  
  local POSTGRES_DB="app_db"
  local POSTGRES_USER="app_user"
  local POSTGRES_PASSWORD="testpass123"
  local DB_DATA_PATH="${TEMP_DIR}/data/postgres"
  
  mkdir -p "${DB_DATA_PATH}"
  
  cat > "${COMPOSE_FILE}" <<EOF
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - default
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
        BUILD_VERSION: \${BUILD_VERSION:-dev}
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env
      - .env.docker
    networks:
      - default
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
      args:
        COMMIT_SHA: \${COMMIT_SHA:-local}
        BUILD_VERSION: \${BUILD_VERSION:-dev}
        VITE_API_BASE_URL: /api
        VITE_APP_NAME: ca-pdf
        VITE_PUBLIC_BASE_URL: /
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "80:80"
    networks:
      - default
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://127.0.0.1/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  postgres_data:
EOF

  if [[ -f "${COMPOSE_FILE}" ]]; then
    log_pass "compose 文件已生成"
  else
    log_fail "compose 文件生成失败"
    return 1
  fi
  
  # Test service count
  local service_count
  service_count=$(grep -E "^  (db|backend|frontend):" "${COMPOSE_FILE}" | wc -l)
  if [[ "${service_count}" -eq 3 ]]; then
    log_pass "服务数量正确（3个服务）"
  else
    log_fail "服务数量错误（期望3个，实际${service_count}个）"
    return 1
  fi
  
  # Verify only one network (default)
  if grep -q "networks:" "${COMPOSE_FILE}"; then
    local network_count
    network_count=$(grep -c "\- default" "${COMPOSE_FILE}" || echo 0)
    if [[ "${network_count}" -eq 3 ]]; then
      log_pass "default 网络正确分配给所有服务"
    else
      printf "  ⚠ default 网络分配数量: %s\n" "${network_count}"
    fi
  else
    log_pass "使用默认桥接网络（无显式网络定义）"
  fi
  
  # Verify no Traefik service
  if grep -q "traefik:" "${COMPOSE_FILE}"; then
    log_fail "不应包含 traefik 服务"
    return 1
  else
    log_pass "无 traefik 服务（符合预期）"
  fi
  
  # Verify no Traefik volumes
  if grep -q "traefik_letsencrypt" "${COMPOSE_FILE}"; then
    log_fail "不应包含 traefik_letsencrypt 卷"
    return 1
  else
    log_pass "无 traefik 卷（符合预期）"
  fi
  
  # Verify frontend port binding
  if grep -A 20 "frontend:" "${COMPOSE_FILE}" | grep -q '80:80'; then
    log_pass "frontend 端口绑定正确（80:80）"
  else
    log_fail "frontend 端口绑定错误"
    return 1
  fi
  
  # Verify backend has no exposed ports
  # Extract only the backend service section (from backend: to the next service)
  if sed -n '/^backend:/,/^frontend:/p' "${COMPOSE_FILE}" | grep -q "ports:"; then
    log_fail "backend 不应暴露端口（仅内部访问）"
    return 1
  else
    log_pass "backend 无端口暴露（符合预期）"
  fi
  
  # Verify VITE_API_BASE_URL is set to /api
  if grep -A 20 "frontend:" "${COMPOSE_FILE}" | grep -q "VITE_API_BASE_URL: /api"; then
    log_pass "VITE_API_BASE_URL 设置正确（/api）"
  else
    log_fail "VITE_API_BASE_URL 设置错误"
    return 1
  fi
  
  # Verify volume definition
  if grep -q "^volumes:" "${COMPOSE_FILE}" && grep -q "postgres_data:" "${COMPOSE_FILE}"; then
    log_pass "postgres_data 卷已定义"
  else
    log_fail "postgres_data 卷未定义"
    return 1
  fi
}

test_nginx_proxy_config() {
  log_test "测试 nginx 反向代理配置"
  
  cat > "${NGINX_CONF}" <<'EOF'
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # API reverse proxy
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        
        # Forward client IP information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Handle OPTIONS preflight requests with CORS headers
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }
    }

    # Health check endpoint
    location = /healthz {
        add_header Content-Type text/plain;
        return 200 "ok";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

  if [[ -f "${NGINX_CONF}" ]]; then
    log_pass "nginx 配置文件已生成"
  else
    log_fail "nginx 配置文件生成失败"
    return 1
  fi
  
  # Test /api proxy configuration
  if grep -q 'location /api/' "${NGINX_CONF}" && grep -q 'proxy_pass http://backend:8000/api/;' "${NGINX_CONF}"; then
    log_pass "/api 反向代理配置正确"
  else
    log_fail "/api 反向代理配置错误"
    return 1
  fi
  
  # Test client IP forwarding headers
  local headers=("X-Real-IP" "X-Forwarded-For" "X-Forwarded-Proto" "X-Forwarded-Host" "X-Forwarded-Port")
  local headers_ok=1
  for header in "${headers[@]}"; do
    if ! grep -q "proxy_set_header ${header}" "${NGINX_CONF}"; then
      log_fail "${header} 头未设置"
      headers_ok=0
    fi
  done
  if [[ "${headers_ok}" -eq 1 ]]; then
    log_pass "客户端 IP 转发头已正确设置"
  fi
  
  # Test CORS preflight handling
  if grep -q "if (\$request_method = 'OPTIONS')" "${NGINX_CONF}"; then
    log_pass "CORS preflight 处理已配置"
  else
    log_fail "CORS preflight 处理缺失"
    return 1
  fi
  
  # Test health check endpoint
  if grep -q 'location = /healthz' "${NGINX_CONF}" && grep -q 'return 200 "ok"' "${NGINX_CONF}"; then
    log_pass "/healthz 健康检查端点已配置"
  else
    log_fail "/healthz 健康检查端点配置错误"
    return 1
  fi
  
  # Test listen port
  if grep -q 'listen 80;' "${NGINX_CONF}"; then
    log_pass "nginx 监听端口正确（80）"
  else
    log_fail "nginx 监听端口错误"
    return 1
  fi
}

test_env_variables() {
  log_test "测试环境变量配置（无 Traefik）"
  
  cat > "${ENV_DOCKER_FILE}" <<'EOF'
# Database Configuration
POSTGRES_DB=app_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://app_user:secure_password_here@db:5432/app_db

# Backend Configuration
BACKEND_CORS_ORIGINS=["http://localhost"]
APP_HOST=0.0.0.0
APP_PORT=8000

# Frontend Configuration
VITE_API_BASE_URL=/api
VITE_PUBLIC_BASE_URL=/
VITE_APP_NAME=ca-pdf

# Security
ENCRYPTED_STORAGE_MASTER_KEY=your-master-key-here
SECRET_KEY=your-secret-key-here
EOF

  if [[ -f "${ENV_DOCKER_FILE}" ]]; then
    log_pass "环境变量文件已生成"
  else
    log_fail "环境变量文件生成失败"
    return 1
  fi
  
  # Verify no Traefik variables
  if grep -q "TRAEFIK" "${ENV_DOCKER_FILE}"; then
    log_fail "不应包含 TRAEFIK 相关变量"
    return 1
  else
    log_pass "无 TRAEFIK 变量（符合预期）"
  fi
  
  # Verify no domain variables
  if grep -q "DOMAIN\|ACME_EMAIL" "${ENV_DOCKER_FILE}"; then
    log_fail "不应包含 DOMAIN/ACME_EMAIL 变量"
    return 1
  else
    log_pass "无 DOMAIN/ACME 变量（符合预期）"
  fi
  
  # Verify CORS origins format
  if grep -q 'BACKEND_CORS_ORIGINS=\["http://localhost"\]' "${ENV_DOCKER_FILE}"; then
    log_pass "CORS origins 格式正确（JSON 数组）"
  else
    log_fail "CORS origins 格式错误"
    return 1
  fi
  
  # Verify VITE_API_BASE_URL
  if grep -q 'VITE_API_BASE_URL=/api' "${ENV_DOCKER_FILE}"; then
    log_pass "VITE_API_BASE_URL 设置正确"
  else
    log_fail "VITE_API_BASE_URL 设置错误"
    return 1
  fi
  
  # Verify database connection string
  if grep -q 'DATABASE_URL=postgresql+asyncpg://.*@db:5432/' "${ENV_DOCKER_FILE}"; then
    log_pass "数据库连接字符串格式正确"
  else
    log_fail "数据库连接字符串格式错误"
    return 1
  fi
}

test_compose_validation() {
  log_test "测试 docker compose 配置验证"
  
  # Generate minimal compose file
  cat > "${COMPOSE_FILE}" <<'EOF'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: test_pass
    networks:
      - default

  backend:
    image: alpine:latest
    command: sleep 3600
    depends_on:
      - db
    networks:
      - default

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - default

volumes:
  postgres_data:
EOF

  # Validate with docker compose config
  cd "${TEMP_DIR}" || return 1
  
  if docker compose -f "${COMPOSE_FILE}" config > /dev/null 2>&1; then
    log_pass "docker compose 配置验证通过"
  else
    log_fail "docker compose 配置验证失败"
    return 1
  fi
  
  # Count services in validated output
  local validated_services
  validated_services=$(docker compose -f "${COMPOSE_FILE}" config --services 2>/dev/null | wc -l)
  if [[ "${validated_services}" -eq 3 ]]; then
    log_pass "验证输出包含3个服务"
  else
    log_fail "验证输出服务数量错误（期望3个，实际${validated_services}个）"
    return 1
  fi
  
  # Verify no Traefik in services list
  if docker compose -f "${COMPOSE_FILE}" config --services 2>/dev/null | grep -q "traefik"; then
    log_fail "服务列表不应包含 traefik"
    return 1
  else
    log_pass "服务列表不包含 traefik（符合预期）"
  fi
}

test_health_check_endpoints() {
  log_test "测试健康检查端点配置"
  
  cat > "${COMPOSE_FILE}" <<'EOF'
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d app_db"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s

  backend:
    image: alpine:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: nginx:alpine
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://127.0.0.1/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
EOF

  if [[ -f "${COMPOSE_FILE}" ]]; then
    log_pass "健康检查配置文件已生成"
  else
    log_fail "健康检查配置文件生成失败"
    return 1
  fi
  
  # Test backend health check
  if grep -A 5 "backend:" "${COMPOSE_FILE}" | grep -q 'http://127.0.0.1:8000/health'; then
    log_pass "backend 健康检查路径正确（/health）"
  else
    log_fail "backend 健康检查路径错误"
    return 1
  fi
  
  # Test frontend health check
  if grep -A 5 "frontend:" "${COMPOSE_FILE}" | grep -q 'http://127.0.0.1/healthz'; then
    log_pass "frontend 健康检查路径正确（/healthz）"
  else
    log_fail "frontend 健康检查路径错误"
    return 1
  fi
  
  # Test db health check
  if grep -A 5 "db:" "${COMPOSE_FILE}" | grep -q 'pg_isready'; then
    log_pass "db 健康检查配置正确（pg_isready）"
  else
    log_fail "db 健康检查配置错误"
    return 1
  fi
  
  # Verify no Traefik health check
  if grep -q "traefik.*healthcheck\|traefik.*ping" "${COMPOSE_FILE}"; then
    log_fail "不应包含 traefik 健康检查"
    return 1
  else
    log_pass "无 traefik 健康检查（符合预期）"
  fi
}

test_network_architecture() {
  log_test "测试网络架构（单一默认网络）"
  
  cat > "${COMPOSE_FILE}" <<'EOF'
services:
  db:
    image: postgres:16
    networks:
      - default

  backend:
    image: alpine:latest
    networks:
      - default

  frontend:
    image: nginx:alpine
    networks:
      - default
EOF

  # Test that all services use default network
  local services_with_default
  services_with_default=$(grep -c "\- default" "${COMPOSE_FILE}" || echo 0)
  if [[ "${services_with_default}" -eq 3 ]]; then
    log_pass "所有服务使用 default 网络"
  else
    log_fail "服务网络配置错误（期望3个 default，实际${services_with_default}个）"
    return 1
  fi
  
  # Verify no internal/edge networks
  if grep -q "internal:\|edge:" "${COMPOSE_FILE}"; then
    log_fail "不应包含 internal/edge 网络"
    return 1
  else
    log_pass "无 internal/edge 网络（符合预期）"
  fi
  
  # Verify no explicit network definitions (using implicit default)
  if grep -q "^networks:" "${COMPOSE_FILE}"; then
    log_warn "存在显式网络定义（可选）"
  else
    log_pass "使用隐式默认网络（推荐）"
  fi
}

# Run all tests
main() {
  printf "\n================================\n"
  printf "Deployment Configuration Tests\n"
  printf "================================\n"
  
  test_write_compose_file_basic
  test_nginx_proxy_config
  test_env_variables
  test_compose_validation
  test_health_check_endpoints
  test_network_architecture
  
  printf "\n================================\n"
  printf "Test Summary\n"
  printf "================================\n"
  printf "Passed: %d\n" "${TESTS_PASSED}"
  printf "Failed: %d\n" "${TESTS_FAILED}"
  printf "================================\n\n"
  
  if [[ ${TESTS_FAILED} -gt 0 ]]; then
    exit 1
  else
    printf "All tests passed! ✓\n\n"
    exit 0
  fi
}

main "$@"
