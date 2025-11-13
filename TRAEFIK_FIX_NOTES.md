# Traefik Configuration Fix - Implementation Notes

## Problem Description

Traefik dynamic configuration was missing routers and services definitions, causing:
- Traefik container to be unhealthy
- Reverse proxy unable to route requests to backend and frontend

## Root Cause

The installation script (`scripts/deploy.sh`) was generating a `dynamic.yml` file with only:
- Middleware definitions (redirect-to-https)
- TLS settings

But missing:
- HTTP routers (for both web and websecure entrypoints)
- Service definitions (pointing to backend and frontend containers)
- Health check configurations

## Changes Made

### 1. Updated `scripts/deploy.sh`

#### Function: `write_dynamic_config()` (lines 642-794)

Added complete Traefik routing configuration:

**Routers:**
- `backend-web`: HTTP router (port 80) that redirects to HTTPS
- `backend`: HTTPS router (port 443) for backend API
- `frontend-web`: HTTP router (port 80) that redirects to HTTPS
- `frontend`: HTTPS router (port 443) for frontend

**Services:**
- `backend`: Points to `http://backend:8000` with health check at `/health`
- `frontend`: Points to `http://frontend:8080` with health check at `/`

**Key differences between modes:**
- **Local mode**: Uses self-signed certificates from `certs/selfsigned.crt`
- **Production mode**: Uses Let's Encrypt certificate resolver (`certResolver: le`)

#### Function: `build_traefik_assets()` (lines 565-568)

Removed Docker label generation since routing is now handled by file-based configuration:
- Set `BACKEND_LABELS=""` and `FRONTEND_LABELS=""`
- Added comment explaining that routers are defined in dynamic.yml

### 2. Updated `docker-compose.yml`

#### Traefik service (lines 2-34)
- Added `--providers.file.directory=/etc/traefik/dynamic` to command
- Added volume mount: `./config/traefik:/etc/traefik/dynamic:ro`

#### Backend and Frontend services (lines 55-86)
- Removed all Traefik labels since routing is now file-based
- Kept all other configurations intact

### 3. Created Static Configuration Files

#### `/config/traefik/dynamic.yml`
Default configuration for local development with:
- Default domains: `api.localtest.me` and `app.localtest.me`
- Complete router and service definitions
- HTTPS redirect middleware
- Health check configurations

#### `/config/traefik/README.md`
Documentation explaining:
- Configuration structure
- Router and service details
- Usage for local development and production

#### `/config/traefik/certs/.gitignore`
Prevents accidental commit of certificate files while tracking the directory.

## Configuration Architecture

### File-Based Routing (New)

```
Traefik Container
├── File Provider: /etc/traefik/dynamic/
│   └── dynamic.yml (defines routers, services, middlewares)
└── Docker Provider: docker.sock
(used only for service discovery, not routing)
```

**Advantages:**
- Centralized configuration
- Easier to validate and version control
- Consistent across all deployment modes
- Better separation of concerns

### Previous Docker Labels Approach (Removed)

Previously used Docker labels on backend/frontend services for routing, which:
- Was scattered across multiple services
- Harder to maintain and validate
- Could conflict with file-based config

## Validation Steps

### 1. Check Deploy Script Syntax
```bash
bash -n scripts/deploy.sh
```

### 2. Verify Docker Compose Configuration
```bash
docker compose config
```

### 3. Test Deployment (Local Mode)
```bash
# Install fresh deployment
./scripts/deploy.sh install \
  --mode local \
  --domain localtest.me

# Check Traefik health
docker compose ps traefik
# Should show: healthy

# Check dynamic config was generated
cat config/traefik/dynamic.yml
# Should contain routers, services, middlewares, tls sections

# Check certificates (local mode)
ls -l config/traefik/certs/
# Should contain selfsigned.crt and selfsigned.key

# Test backend routing
curl -k https://api.localtest.me/health
# Should return: {"status":"healthy"}

# Test frontend routing
curl -k https://app.localtest.me/
# Should return frontend HTML

# Test HTTPS redirect
curl -I http://api.localtest.me/health
# Should return: 301/302 redirect to https://
```

### 4. Test Deployment (Production Mode)
```bash
# Install with production settings
./scripts/deploy.sh install \
  --mode production \
  --domain example.com \
  --acme-email admin@example.com

# Check Traefik logs for certificate acquisition
docker compose logs traefik | grep -i acme

# Verify routers are active
docker compose exec traefik traefik healthcheck --ping
```

## Dynamic Configuration Structure

### Generated for Local Mode
```yaml
http:
routers:
backend-web:
rule: "Host(`api.example.com`)"
entryPoints: [web]
middlewares: [redirect-to-https]
service: backend

backend:
rule: "Host(`api.example.com`)"
entryPoints: [websecure]
service: backend
tls: {}  # Uses self-signed cert

# ... frontend routers ...

services:
backend:
loadBalancer:
servers:
- url: "http://backend:8000"
healthCheck:
path: "/health"
interval: "30s"
timeout: "5s"

# ... frontend service ...

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
```

### Generated for Production Mode
Same structure but:
- `tls.certResolver: le` instead of `tls: {}`
- No `tls.certificates` section (uses Let's Encrypt)

## Acceptance Criteria Status

✅ **Traefik routers defined in dynamic.yml**
- backend-web, backend, frontend-web, frontend routers created

✅ **Traefik services defined in dynamic.yml**
- backend and frontend services point to correct containers

✅ **Routes match configured domains**
- Uses BACKEND_DOMAIN and FRONTEND_DOMAIN variables
- Default domains: api.localtest.me, app.localtest.me

✅ **Health checks configured**
- Backend: `/health` endpoint every 30s
- Frontend: `/` endpoint every 30s

✅ **HTTPS redirect implemented**
- `redirect-to-https` middleware on all HTTP routers
- Permanent redirect (301) configured

✅ **Configuration generated on each install**
- `write_dynamic_config()` called during deployment
- File recreated with current domain settings

## Testing Results Expected

### Traefik Container Health
```bash
docker compose ps traefik
```
Expected: `Status: Up (healthy)`

### Backend API Access
```bash
curl -k https://api.localtest.me/health
```
Expected: `{"status":"healthy"}`

### Frontend Access
```bash
curl -k https://app.localtest.me/
```
Expected: Frontend HTML content

### HTTPS Redirect
```bash
curl -I http://api.localtest.me/health
```
Expected: `Location: https://api.localtest.me/health`

## Rollback Plan

If issues occur, rollback changes:

1. Restore Docker labels in docker-compose.yml:
```bash
git checkout HEAD~1 docker-compose.yml
```

2. Restore previous deploy.sh:
```bash
git checkout HEAD~1 scripts/deploy.sh
```

3. Remove file provider configuration:
```bash
# Remove from Traefik command:
# - --providers.file.directory=/etc/traefik/dynamic
```

## Future Improvements

1. **Dynamic router reloading**: Implement hot-reload without container restart
2. **Multiple domains**: Support multiple domains per service
3. **Path-based routing**: Add API path prefixes (e.g., `/api/v1/`, `/api/v2/`)
4. **Rate limiting**: Add rate limit middleware per service
5. **IP whitelisting**: Add IP-based access control for admin endpoints

## References

- Traefik v3.1 Documentation: https://doc.traefik.io/traefik/
- File Provider: https://doc.traefik.io/traefik/providers/file/
- Routers: https://doc.traefik.io/traefik/routing/routers/
- Services: https://doc.traefik.io/traefik/routing/services/
