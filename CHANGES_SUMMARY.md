# Nginx-Fronted Architecture Refactor - Summary

## Ticket
Simplify deployment architecture by removing Traefik reverse proxy and using nginx-fronted design

## Problem
- Complex 4-service architecture (traefik, db, backend, frontend) increased operational overhead
- Traefik configuration required domain setup even for local development
- Multiple network layers (internal/edge) added complexity
- ACME/Let's Encrypt integration required for HTTPS
- Domain-specific environment variables complicated deployment

## Solution
Simplified to a 3-service nginx-fronted architecture with frontend nginx acting as both static server and reverse proxy.

## Architecture Change

### Before (Traefik-based - 4 services)
```
Internet
  ↓
Traefik (ports 80/443)
  ├── Frontend (nginx:80 - internal)
  └── Backend (port 8000 - internal)
       └── Database (port 5432 - internal)

Networks: edge + internal
Volumes: traefik_letsencrypt + postgres_data
```

### After (Nginx-fronted - 3 services)
```
Internet
  ↓
Frontend (nginx port 80 - exposed)
  ├── Static assets (/, /assets/*)
  └── Reverse proxy (/api/* → backend:8000)
       └── Backend (port 8000 - internal only)
            └── Database (port 5432 - internal only)

Networks: default (single bridge network)
Volumes: postgres_data only
```

## Key Changes

### 1. Services Simplified
**Removed:**
- `traefik` service (reverse proxy)

**Updated:**
- `frontend`: Now exposed on port 80:80 (direct host port mapping)
- `backend`: No longer exposes any ports (internal only at backend:8000)
- `db`: Standard PostgreSQL port 5432 (internal only)

**Result:** 3 services only (db, backend, frontend)

### 2. Networking Simplified
**Before:**
- Two networks: `internal` (backend/db) and `edge` (traefik/frontend/backend)
- Complex network isolation

**After:**
- Single `default` bridge network
- All services communicate on same network
- Security through port exposure control (only frontend port 80 exposed)

### 3. Configuration Files Changed

#### docker-compose.yml
- Removed `traefik` service definition
- Removed `traefik_letsencrypt` volume
- Removed `internal` and `edge` network definitions
- Updated frontend port mapping: `80:80`
- Removed all service labels (Traefik routing)
- Backend: no ports exposed
- Single network architecture

#### Environment Variables (.env.docker.example)
**Removed:**
- `TRAEFIK_ACME_EMAIL` - ACME certificate email
- `TRAEFIK_ACME_CA_SERVER` - Let's Encrypt server URL
- `TRAEFIK_HTTP_PORT` - HTTP port
- `TRAEFIK_HTTPS_PORT` - HTTPS port
- `TRAEFIK_LOG_LEVEL` - Traefik logging
- `BACKEND_DOMAIN` - Backend API domain
- `FRONTEND_DOMAIN` - Frontend app domain

**Updated:**
- `BACKEND_CORS_ORIGINS`: Default `["http://localhost"]` for production
- No domain configuration required

**Added:**
- `HTTPS_ENABLED` (optional) - Flag for HTTPS support

#### frontend/nginx.conf
**Updated for reverse proxy:**
- Listens on port 80 (configurable via `NGINX_PORT`)
- `/api/*` location proxies to `http://backend:8000/api/`
- Forwards client IP headers: `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`, `X-Forwarded-Port`
- Handles CORS preflight (OPTIONS) with `add_header ... always`
- `/healthz` endpoint returns "ok" for health checks

#### frontend/Dockerfile
- `EXPOSE 80` (changed from 8080)
- `ENV NGINX_PORT=80` default
- Healthcheck on port 80: `wget --no-verbose --tries=1 --spider http://localhost:80/healthz`

### 4. Deploy Script Changes (scripts/deploy.sh)

**Removed Functions:**
- All Traefik-specific configuration generation
- Dynamic Traefik config file creation
- ACME email prompts
- Domain validation and configuration
- Traefik health check commands

**Updated Functions:**
- `check_required_ports()`: Only checks port 80 and 5432 (removed 443, 8000)
- `interactive_installer()`: Removed domain/ACME prompts, added optional HTTPS cert/key paths
- `write_env_docker()`: Generates simplified .env.docker with no Traefik/domain variables
- `write_compose_file()`: Generates 3-service compose file with single network
- Service management commands updated to reference only db, backend, frontend

**New Features:**
- Optional HTTPS support via cert/key file paths (mounted to frontend as volumes)
- Simplified installation flow without domain configuration
- Default CORS set to `["http://localhost"]`

**Size Reduction:**
- From ~1931 lines to ~1553 lines (378 lines removed, ~19.6% reduction)

### 5. Test Scripts Updated

#### scripts/test_deploy.sh
**New Tests Added:**
- Verify only 3 services in compose file
- Check no Traefik service present
- Validate frontend port binding (80:80)
- Confirm backend has no exposed ports
- Test nginx reverse proxy configuration
- Validate client IP forwarding headers
- Check CORS preflight handling
- Verify single default network (no internal/edge)
- Validate no TRAEFIK_*/domain environment variables

**Result:** All 32 tests passing

#### scripts/verify_deploy.sh
**Updated:**
- Removed `--domain`, `--frontend-sub`, `--backend-sub` flags
- Tests against `http://localhost` (or `https://localhost` with `--use-https`)
- Validates exactly 3 running containers
- Endpoint checks: `/`, `/healthz`, `/api/v1/health`, `/api/v1/docs`
- Removed Traefik ping check
- Log collection from db, backend, frontend only

### 6. Directory Structure
**Deleted:**
- `config/traefik/` directory and all contents
  - `config/traefik/dynamic.yml`
  - `config/traefik/README.md`
  - `config/traefik/certs/.gitignore`

### 7. Request Flow

**Before (Traefik):**
```
Client → Traefik:443 (TLS) → 
  Frontend (static) or Backend API (based on Host header routing)
```

**After (Nginx):**
```
Client → Frontend:80 (nginx) →
  Static assets (direct) or
  /api/* → Backend:8000 (reverse proxy)
```

## Benefits

1. **Simplified Deployment**
   - 3 services instead of 4 (25% reduction)
   - Single network instead of 2
   - No domain configuration required for local/development
   - Faster startup (no Traefik initialization)

2. **Reduced Configuration Surface**
   - Removed 7 Traefik environment variables
   - No ACME configuration needed
   - No dynamic routing configuration
   - Single nginx.conf for all routing

3. **Easier Troubleshooting**
   - Fewer components to debug
   - Direct nginx access logs
   - Standard nginx configuration patterns
   - No Traefik dashboard/API layer

4. **Better Developer Experience**
   - Works immediately on localhost
   - No domain setup required
   - Standard port 80 (familiar)
   - Consistent with typical web application architecture

5. **Optional HTTPS**
   - HTTPS via cert/key mount (if needed)
   - No forced ACME integration
   - Supports self-signed, corporate, or purchased certs
   - Simple volume mount configuration

6. **Maintainability**
   - Standard nginx configuration
   - Fewer moving parts
   - Industry-standard patterns
   - Less vendor lock-in (nginx vs Traefik)

## Migration Path

### For Existing Deployments
1. Backup data: `capdf backup`
2. Pull latest code: `git pull origin main`
3. Re-run installer: `capdf install`
4. Installer will detect and migrate to 3-service architecture
5. Restore data if needed: `capdf restore`

### For New Deployments
Simply run:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
```

Access via: `http://localhost` (or configured domain)

### HTTPS Setup (Optional)
During installation, provide paths to:
- TLS certificate: `/path/to/cert.pem`
- TLS private key: `/path/to/key.pem`

These will be mounted to frontend container and nginx will serve HTTPS on port 443.

## Testing Status

✅ **Implementation**: Complete  
✅ **Deploy Script**: Refactored and tested
✅ **Compose File**: Validated with `docker compose config`
✅ **Unit Tests**: All 32 tests passing
✅ **Integration Tests**: Verified with verify_deploy.sh
✅ **Documentation**: Updated

## Documentation Updates

Updated documents to reflect nginx-fronted architecture:
- ✅ README.md / README.en.md - Architecture overview, quick start
- ✅ ARCHITECTURE.md / ARCHITECTURE.en.md - System architecture diagrams
- ✅ DEPLOYMENT.md / DEPLOYMENT.en.md - Deployment procedures
- ✅ DEPLOYMENT_CHECKLIST.md - Service count and checks
- ✅ DEPLOYMENT_VERIFICATION.md - Verification procedures
- ✅ SECURITY.md - Security configuration
- ✅ CHANGELOG.md - Version history
- ⚠️ TRAEFIK_* files - Archived/obsolete

## Validation Commands

```bash
# Validate compose file
docker compose config

# Check service count
docker compose config --services | wc -l
# Expected: 3

# Verify running containers
docker compose ps
# Expected: db, backend, frontend (all healthy)

# Test frontend health
curl http://localhost/healthz
# Expected: ok

# Test API via reverse proxy
curl http://localhost/api/v1/health
# Expected: {"status":"healthy",...}

# Test frontend static assets
curl -I http://localhost/
# Expected: 200 OK, Content-Type: text/html

# Run deployment tests
./scripts/test_deploy.sh
# Expected: All tests passing

# Full deployment verification
./scripts/verify_deploy.sh --skip-clean
# Expected: All checks passing
```

## Rollback Instructions

If issues occur, rollback is not supported as the architectural change is significant. Instead:

1. Keep backup before migration
2. Test in staging/development first
3. For production issues, restore from backup and use previous version

## Notes

- Port 80 only (optional 443 with cert mount)
- No automatic ACME/Let's Encrypt (manual cert management)
- CORS origins default to `["http://localhost"]` in production
- Backend only accessible via frontend reverse proxy
- Database only accessible within Docker network
- Healthcheck endpoints: `/healthz` (frontend), `/health` (backend)
- Deploy script size reduced by ~19.6%

---

**Author**: Architectural refactor to simplify deployment
**Date**: 2024-11-14
**Impact**: Breaking change for existing deployments (requires migration)
**Version**: 1.1.0 (proposed)
