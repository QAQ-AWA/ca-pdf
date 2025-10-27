# ca-pdf

A self-hosted PDF signing platform with a built-in certificate authority, FastAPI backend, and React/Vite frontend. The project ships with Docker Compose manifests and helper scripts for running the complete stack behind Traefik.

> 📘 **Looking for the full deployment and usage guide?**
>
> All detailed instructions (installation, operations, security hardening, and FAQs) are maintained in **[README.zh-CN.md](./README.zh-CN.md)**.

## Quick start (TL;DR)

```bash
cp .env.example .env
cp .env.docker.example .env.docker
./deploy.sh up
```

- `deploy.sh` detects the host architecture (amd64 / arm64) and wraps the Docker Compose workflow.
- Configure `SECRET_KEY`, `ENCRYPTED_STORAGE_MASTER_KEY`, database credentials, and public domains in the `.env` files before deploying.
- The frontend is served at `https://<FRONTEND_DOMAIN>` and the FastAPI docs live at `https://<BACKEND_DOMAIN>/docs`.

## Repository layout

```
.
├── backend/          # FastAPI service (Poetry, SQLAlchemy, pyHanko)
├── frontend/         # Vite + React + TypeScript client
├── config/           # Shared lint/format rules
├── scripts/          # Local development helpers
├── docker-compose.yml
├── deploy.sh         # One-stop deployment wrapper
└── README.zh-CN.md   # Comprehensive Chinese documentation
```

## Local development

```bash
make install        # Install backend (Poetry) & frontend (npm) dependencies
make dev-backend    # Run the FastAPI server with reload
make dev-frontend   # Run the Vite dev server
make test           # Backend pytest + frontend Vitest
```

Automation is handled via GitHub Actions (`backend-ci`, `frontend-ci`, and `docker-build`). Refer to the Chinese documentation for production guidance, backup strategies, and troubleshooting tips.
