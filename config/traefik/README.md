# Traefik Configuration

This directory contains Traefik dynamic configuration files.

## Files

- `dynamic.yml` - Dynamic routing configuration for Traefik
  - Defines HTTP routers for backend and frontend services
  - Configures HTTPS redirect middleware
  - Sets up service load balancers with health checks
  - Configures TLS settings

- `certs/` - Directory for SSL/TLS certificates (for local development with self-signed certs)

## Configuration Details

### Routers

- **backend-web**: HTTP router for backend API that redirects to HTTPS
- **backend**: HTTPS router for backend API
- **frontend-web**: HTTP router for frontend that redirects to HTTPS  
- **frontend**: HTTPS router for frontend

### Services

- **backend**: Points to `backend:8000` with health check at `/health`
- **frontend**: Points to `frontend:8080` with health check at `/`

### Middlewares

- **redirect-to-https**: Redirects all HTTP traffic to HTTPS

## Usage

### Local Development

For local development, the default `dynamic.yml` uses:
- Backend: `api.localtest.me`
- Frontend: `app.localtest.me`

These domains resolve to 127.0.0.1 by default, so no hosts file modification is needed.

### Production Deployment

When using `scripts/deploy.sh`, the dynamic.yml file is automatically generated with your custom domains based on the deployment configuration.

## Note

This configuration uses file-based routing (instead of Docker labels) for better centralization and easier management. The deploy.sh script will regenerate this file with your specific domain configuration during deployment.
