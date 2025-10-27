# Monorepo Scaffold

This repository provides a monorepo layout with a FastAPI backend and a Vite + React + TypeScript frontend. Shared tooling lives under the `config/` directory, while convenience scripts and Make targets help streamline local development.

## Structure

```
.
├── backend/          # FastAPI application packaged with Poetry
├── frontend/         # Vite + React + TypeScript web client
├── config/           # Shared linting/formatting configuration
├── scripts/          # Developer workflow helpers
├── Makefile          # High-level commands for common workflows
└── .env.example      # Sample environment configuration
```

## Getting started

1. Copy the environment template and update values as needed:
   ```bash
   cp .env.example .env
   ```
2. Install backend and frontend dependencies:
   ```bash
   make install
   ```
3. Run the development servers:
   ```bash
   make dev-backend
   make dev-frontend
   ```

## Available commands

| Command                | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `make install`         | Install backend (Poetry) and frontend (npm) deps. |
| `make dev-backend`     | Start the FastAPI backend with auto-reload.       |
| `make dev-frontend`    | Start the Vite development server.                |
| `make lint`            | Run linting for both backend and frontend.        |
| `make format`          | Apply code formatting in both projects.           |
| `make test`            | Execute backend pytest suite and frontend Vitest. |
| `make typecheck`       | Run mypy and TypeScript type checks.              |

## Tooling highlights

- **Backend**: FastAPI, Poetry, pytest, mypy, black, isort.
- **Frontend**: Vite, React, TypeScript, Vitest, Testing Library, ESLint, Prettier.
- **Shared config**: Centralised ESLint and Prettier rules in `config/` for reuse across packages.

## Containerised local environment

The repository includes production-ready Docker images and a local stack powered by Docker Compose, Traefik, and PostgreSQL. This flow mirrors a TLS-enabled deployment while keeping databases and certificates persistent across restarts.

### Prerequisites

- Docker Engine 23.x or newer (Docker Desktop works as well).
- Docker Compose V2 (bundled with the Docker CLI).
- Hostnames that resolve to your workstation. The defaults use the `*.localtest.me` wildcard, which already maps to `127.0.0.1` and does not require editing `/etc/hosts`.

### Environment configuration

1. Copy the base application settings:
   ```bash
   cp .env.example .env
   ```
2. Copy the Compose-specific overrides:
   ```bash
   cp .env.docker.example .env.docker
   ```
3. Update both files with secure values (e.g. `SECRET_KEY`, database password) and adjust the front-end/back-end domains if you are not using the defaults.

The Compose file loads both `.env` and `.env.docker`, so anything defined in `.env.docker` overrides the base configuration. Ensure `DATABASE_URL` in `.env.docker` points at the `db` service (`postgresql+asyncpg://…@db:5432/...`).

### Building and running the stack

Build the images and start all services:

```bash
docker compose up -d --build
```

The backend container listens on port 8000 and the frontend container exposes port 8080. Traefik continues to front the services and terminate TLS on 443 for external access.

Once Traefik has obtained certificates you can access:

- API: `https://${BACKEND_DOMAIN}/docs`
- Frontend: `https://${FRONTEND_DOMAIN}`
- PostgreSQL: exposed on `${POSTGRES_HOST_PORT}` for local tooling.

To stop and remove the containers (but keep data and certificates):

```bash
docker compose down
```

Add `--volumes` if you want to reset persisted data: `docker compose down --volumes`.

### Multi-architecture builds

Both Dockerfiles are ready for Docker Buildx multi-platform builds. Ensure BuildKit is enabled and select a builder that supports `linux/amd64` and `linux/arm64`:

```bash
docker buildx create --name multiarch --use --bootstrap
```

Build and optionally push the backend image:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  --build-arg BUILD_VERSION=$(git describe --tags --always) \
  -f backend/Dockerfile \
  -t registry.example.com/backend:$(git rev-parse --short HEAD) \
  .
```

Build the frontend image, passing along any Vite build arguments that your deployment requires:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  --build-arg BUILD_VERSION=$(git describe --tags --always) \
  --build-arg VITE_API_BASE_URL=${VITE_API_BASE_URL:-https://api.example.com} \
  --build-arg VITE_APP_NAME="${VITE_APP_NAME:-Monorepo UI}" \
  --build-arg VITE_PUBLIC_BASE_URL=${VITE_PUBLIC_BASE_URL:-https://app.example.com} \
  -f frontend/Dockerfile \
  -t registry.example.com/frontend:$(git rev-parse --short HEAD) \
  .
```

Use `--push` with either command to publish directly to your registry. When building locally without pushing, omit the flag to load the images into your Docker daemon.

### Data persistence

The stack defines named volumes so that database state and ACME certificates survive container restarts:

| Volume              | Purpose                                |
| ------------------- | --------------------------------------- |
| `postgres_data`     | PostgreSQL data directory               |
| `traefik_letsencrypt` | ACME account and issued certificates |

### TLS and Traefik settings

Traefik terminates HTTPS and requests certificates from Let’s Encrypt using the HTTP challenge on port 80. For real certificates, ensure your chosen domains resolve publicly to your machine and adjust the following variables in `.env.docker`:

- `TRAEFIK_ACME_EMAIL`: Email used for ACME registration.
- `TRAEFIK_ACME_CA_SERVER`: Defaults to the Let’s Encrypt staging endpoint for safe testing. Switch to `https://acme-v02.api.letsencrypt.org/directory` for production certificates.
- `BACKEND_DOMAIN` / `FRONTEND_DOMAIN`: Hostnames routed to the API and the SPA.

When certificates are issued they are stored in the `traefik_letsencrypt` volume. Remove the volume to force renewal from scratch.

Let’s Encrypt must be able to reach your machine over ports 80 and 443 for certificate issuance. For purely local-only scenarios consider pointing the domains at a tunnel (e.g. Cloudflare Tunnel, ngrok) or swap in self-signed certificates mounted into Traefik.

### Build secrets

Both Dockerfiles support BuildKit secrets for private registries. Pass secrets when building to avoid storing credentials in image layers:

```bash
docker compose build \
  --secret id=poetry_token,src=/path/to/pypi-token.txt \
  --secret id=npm_token,src=/path/to/npm-token.txt
```

Each secret is optional; omit the corresponding flag if you do not rely on private dependencies.

### Health checks

- Backend exposes `GET /health` on port 8000 and is polled by Docker for readiness.
- Frontend serves `GET /healthz` from Nginx on port 8080 inside the container.
- PostgreSQL and Traefik include native health checks.

These checks allow Compose to coordinate startup ordering for dependable local development.
