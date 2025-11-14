# Deploy CLI Refactor Summary

## Overview
Refactored `scripts/deploy.sh` to eliminate all Traefik-specific code and simplify the deployment flow for the new 3-service architecture (db, backend, frontend only).

## Changes Made

### Script Size Reduction
- **Before**: 1931 lines
- **After**: 1553 lines
- **Reduction**: 378 lines (19.6% smaller)

### Removed Components

#### 1. Traefik-Specific Variables
- `TRAEFIK_DIR`, `TRAEFIK_CERT_DIR`, `TRAEFIK_DYNAMIC_FILE`
- `DOMAIN`, `FRONTEND_DOMAIN`, `BACKEND_DOMAIN`
- `FRONTEND_URL`, `BACKEND_URL`, `DOCS_URL`
- `ACME_EMAIL`
- `TRAEFIK_CA_SERVER`, `TRAEFIK_LOG_LEVEL`, `TRAEFIK_COMMAND`
- `BACKEND_LABELS`, `FRONTEND_LABELS`
- `MODE` (local/production distinction based on domains)

#### 2. Removed Functions
- `prompt_domain()` - No longer asking for domain names
- `prompt_email()` - No longer asking for ACME email
- `ensure_dirs()` - No longer creating Traefik directories
- `build_traefik_assets()` - No longer building Traefik command line
- `write_dynamic_config()` - No longer generating Traefik dynamic configuration
- `validate_network_configuration()` - Removed edge/internal network checks

#### 3. Port Checks Updated
- **Removed**: Port 443 (HTTPS handled optionally via nginx)
- **Removed**: Port 8000 external checks (backend is internal only)
- **Kept**: Port 80 (frontend nginx), Port 5432 (PostgreSQL)

### New/Updated Components

#### 1. Optional HTTPS Support
- Added `HTTPS_ENABLED` flag and TLS cert/key path variables
- New `prompt_https()` function for optional HTTPS configuration
- If enabled, mounts TLS cert/key files to frontend nginx container
- No automatic ACME/Let's Encrypt - users provide their own certificates

#### 2. Simplified Environment Files

**`.env.docker`** now contains only:
```bash
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
POSTGRES_HOST_PORT, POSTGRES_DATA_PATH
VITE_API_BASE_URL=/api
VITE_PUBLIC_BASE_URL=/
VITE_APP_NAME=ca-pdf
HTTPS_ENABLED (0 or 1)
```

**Removed from `.env.docker`**:
- All `TRAEFIK_*` variables
- `BACKEND_DOMAIN`, `FRONTEND_DOMAIN`
- `BACKEND_URL`, `FRONTEND_URL` (replaced with localhost defaults)

#### 3. Docker Compose Generation

**New compose file structure** (3 services only):
```yaml
services:
  db:
    image: postgres:16
    ports: ["5432:5432"]
    # ... healthcheck
  
  backend:
    build: ...
    depends_on: db
    # No port exposure (internal only)
    # No networks section (uses default)
    
  frontend:
    build: ...
    depends_on: backend
    ports: ["80:80"]
    volumes: # Optional, only if HTTPS enabled
      - /path/to/tls.crt:/etc/nginx/ssl/server.crt:ro
      - /path/to/tls.key:/etc/nginx/ssl/server.key:ro

volumes:
  postgres_data:  # No traefik_letsencrypt volume
```

#### 4. Updated Operational Commands

**`command_install()`**:
- Removed domain/ACME prompts
- Added optional HTTPS cert/key prompt
- Port checks: 80, 5432 only
- Removed Traefik dynamic config generation

**`command_doctor()`**:
- Port checks: 80, 5432 (removed 443, 8000)
- Health check: `http://localhost/api/health` (not domain-based URLs)
- Expected services: `["db", "backend", "frontend"]` (removed "traefik")

**`command_export_logs()`**:
- Service list: `db, backend, frontend` (removed "traefik")

**`command_uninstall()`**:
- Removed `TRAEFIK_DIR` cleanup

**`validate_deployment()`**:
- Expected services: 3 (db, backend, frontend)
- API check: `http://localhost/api/health`

**`start_stack()`**:
- Removed Traefik image pull
- Removed network validation (uses default network only)

#### 5. Default URLs and Access

All deployments now use localhost-based URLs:
- **Frontend**: `http://localhost`
- **API**: `http://localhost/api`
- **Health Check**: `http://localhost/api/health`
- **API Docs**: `http://localhost/api/docs`

**CORS Default**: `["http://localhost"]`

### Interactive Installer Flow

**New prompt sequence**:
1. Admin email (defaults to `admin@example.com`)
2. PostgreSQL data directory path
3. CORS origins (JSON list format)
4. **Optional HTTPS** (yes/no)
   - If yes: prompt for TLS cert and key paths
   - Validates files exist before proceeding
5. Auto-generate passwords and secrets

**Removed prompts**:
- Domain name input
- Frontend/backend subdomain input
- ACME email for Let's Encrypt
- Local vs Production mode selection

### Help Text Updates

Updated `install` command help:
```
--force-stop        自动停止占用端口 (80/5432) 的 Docker 容器
```
(Previously listed 80/443/5432/8000)

Updated deployment flow description:
```
2. ✓ 端口占用检查（80/5432）
3. ✓ 交互式配置（管理员邮箱、数据库路径、CORS、可选 HTTPS）
5. ✓ 生成配置文件（.env、.env.docker、docker-compose.yml）
```
(Removed Traefik configuration step)

## Testing Recommendations

Before merging, manually test these key flows:

### 1. Fresh Install (HTTP Only)
```bash
./scripts/deploy.sh install
# Accept defaults, select "no" for HTTPS
# Verify: 3 services start, http://localhost accessible
```

### 2. Fresh Install (with HTTPS)
```bash
./scripts/deploy.sh install
# Accept defaults, select "yes" for HTTPS
# Provide paths to test cert/key files
# Verify: frontend container has TLS volumes mounted
```

### 3. Operational Commands
```bash
./scripts/deploy.sh doctor
# Verify: checks ports 80, 5432 only
# Verify: expects 3 services

./scripts/deploy.sh export-logs
# Verify: collects logs from db, backend, frontend only

./scripts/deploy.sh backup
./scripts/deploy.sh restore <backup-file>
# Verify: no Traefik references in backup/restore flow
```

### 4. Syntax Validation
```bash
bash -n scripts/deploy.sh  # Should output nothing (success)
```

## Breaking Changes

⚠️ **Existing deployments with Traefik will need migration**:

1. Stop the old stack: `capdf down`
2. Remove old config: `rm -rf config/traefik`
3. Run new installer: `capdf install`
4. Provide optional HTTPS certs if needed

The new installer will prompt to overwrite existing files.

## Benefits

1. **Simpler Architecture**: 3 services instead of 4
2. **Easier HTTPS**: Optional, user-provided certs (no ACME complexity)
3. **Fewer Variables**: Reduced configuration surface area
4. **Better Defaults**: Localhost-based URLs work out of the box
5. **Cleaner Code**: 378 fewer lines, better maintainability
6. **Single Network**: No internal/edge network complexity

## Files Changed

- `scripts/deploy.sh` - Major refactor (1931 → 1553 lines)

## Files NOT Changed

- `frontend/nginx.conf` - Already configured for reverse proxy
- `frontend/Dockerfile` - Already correct for port 80
- `docker-compose.yml` - Will be regenerated by new script
- `.env.example`, `.env.docker.example` - Should be updated separately to match new format
