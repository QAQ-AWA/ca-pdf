# Nginx Reverse Proxy Revision

## Summary

This document outlines the changes made to transform the frontend nginx configuration from a simple static file server to a full reverse proxy that handles API requests, CORS, and includes TLS configuration stubs.

## Changes Made

### 1. frontend/nginx.conf

**Major Changes:**
- **Port Change**: Listen on port 80 (instead of 8080)
- **API Reverse Proxy**: Added `/api/` location block that proxies to `http://backend:8000`
- **Client IP Forwarding**: Added standard proxy headers:
  - `X-Real-IP`
  - `X-Forwarded-For`
  - `X-Forwarded-Proto`
  - `X-Forwarded-Host`
  - `X-Forwarded-Port`
- **CORS Preflight Handling**: Added OPTIONS method handling with `add_header ... always` flags to ensure CORS headers are included in all responses (including errors)
- **TLS Configuration Stubs**: Added commented configuration with detailed instructions for enabling HTTPS:
  - `listen 443 ssl http2;`
  - SSL certificate and key paths
  - TLS protocols and ciphers
  - SSL session configuration
  - Instructions on how to mount certificates via Docker volumes
- **WebSocket Support**: Added WebSocket upgrade headers for future compatibility

**Retained Features:**
- Gzip compression (6 levels, 256-byte minimum)
- Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
- Cache headers for versioned assets (immutable, 1-year max-age)
- `/healthz` endpoint for health checks
- SPA fallback routing with `try_files`

### 2. frontend/Dockerfile

**Changes:**
- **Port Configuration**: Changed `ENV NGINX_PORT` from 8080 to 80
- **Exposed Port**: Changed `EXPOSE` from 8080 to 80
- **Health Check**: Updated healthcheck URL from `http://127.0.0.1:8080/healthz` to `http://127.0.0.1/healthz`
- **npm ci Enhancement**: Added `--include=dev` flag to ensure devDependencies (including vite) are installed even when NODE_ENV is set to production

### 3. docker-compose.yml

**Changes:**
- **API Base URL**: Set `VITE_API_BASE_URL: /api` (relative path) so frontend makes requests through nginx proxy instead of directly to backend
- **Health Check**: Updated frontend healthcheck from port 8080 to port 80

### 4. scripts/deploy.sh

**Changes:**
- **API Base URL**: Changed `VITE_API_BASE_URL` from `${BACKEND_URL}` to `/api` in docker-compose generation
- **Traefik Dynamic Config**: Updated frontend service URL from `http://frontend:8080` to `http://frontend:80` in both local and production modes
- **Health Check**: Updated frontend healthcheck from port 8080 to port 80

### 5. scripts/test_deploy.sh

**Changes:**
- **API Base URL**: Changed `VITE_API_BASE_URL` from `${BACKEND_URL}` to `/api`
- **Traefik Dynamic Config**: Updated frontend service URL from `http://frontend:8080` to `http://frontend:80` in test configurations
- **Health Check**: Updated frontend healthcheck from port 8080 to port 80

### 6. config/traefik/dynamic.yml

**Changes:**
- **Frontend Service URL**: Updated from `http://frontend:8080` to `http://frontend:80`

## Configuration Validation

### Nginx Syntax Check
```bash
docker run --rm -v $(pwd)/frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:1.27.2-alpine nginx -t
```
Result: Configuration syntax is valid ✓

### TLS Configuration Instructions

To enable HTTPS on the frontend container:

1. Uncomment the TLS configuration block in `frontend/nginx.conf`:
```nginx
listen 443 ssl http2;
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

2. Mount certificate files in docker-compose.yml or deploy.sh:
```yaml
frontend:
  volumes:
    - /path/to/cert.pem:/etc/nginx/ssl/cert.pem:ro
    - /path/to/key.pem:/etc/nginx/ssl/key.pem:ro
```

3. Optionally add HTTP to HTTPS redirect (add before location blocks):
```nginx
if ($scheme != "https") {
    return 301 https://$host$request_uri;
}
```

## Request Flow

### Before Changes
```
Browser → Traefik → Frontend (nginx:8080) → Static Assets
Browser → Traefik → Backend (8000) → API (direct connection)
```

### After Changes
```
Browser → Traefik → Frontend (nginx:80) → Static Assets
Browser → Traefik → Frontend (nginx:80) → /api/* → Backend (8000) → API
```

## Benefits

1. **Simplified Frontend Configuration**: Frontend now uses relative API paths (`/api`) instead of absolute URLs, making it environment-agnostic
2. **Single Origin**: All requests (static assets + API) come from the same origin, reducing CORS complexity
3. **Better Security**: Client IP information is properly forwarded to the backend
4. **Future-Proof**: TLS configuration stubs make it easy to enable direct HTTPS on the frontend container if needed
5. **Standard Port**: Using port 80 is more conventional for HTTP services

## Testing

### Local Validation
```bash
# Build the frontend container
docker compose build frontend

# Start the full stack
docker compose up -d

# Test health check
curl http://localhost/healthz  # Should return "ok"

# Test API proxy (requires backend running)
curl http://localhost/api/health  # Should proxy to backend

# Verify CORS preflight
curl -X OPTIONS http://localhost/api/test \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
# Should return 204 with CORS headers
```

### Traefik Integration Test
```bash
# With Traefik running
curl -k https://app.localtest.me/healthz  # Frontend health check
curl -k https://app.localtest.me/api/health  # API proxy through frontend
```

## Migration Notes

- The change from port 8080 to port 80 is transparent when using Traefik, as Traefik routes by service name
- Existing environment variables (VITE_API_BASE_URL) will be overridden in docker-compose.yml and deploy.sh
- No changes required to frontend application code - the relative `/api` path works automatically with the nginx proxy

## Rollback

If issues arise, revert these files to their previous versions:
1. `frontend/nginx.conf` - restore listen 8080 and remove /api/ location
2. `frontend/Dockerfile` - restore NGINX_PORT=8080, EXPOSE 8080, healthcheck port
3. `docker-compose.yml` - restore VITE_API_BASE_URL to full backend URL
4. `scripts/deploy.sh` - restore frontend:8080 and VITE_API_BASE_URL
5. `scripts/test_deploy.sh` - restore test configurations
6. `config/traefik/dynamic.yml` - restore frontend:8080
