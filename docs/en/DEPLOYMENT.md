# Deployment Guide (Preview)

> **Translation roadmap:** This page captures the essential deployment workflow. Additional hardening steps and troubleshooting tips remain in the Chinese document for now.

## Deployment Models

- **Local evaluation (Docker Compose)** — spin up PostgreSQL, backend, frontend, and Traefik with `./deploy.sh up`.
- **Production (self-managed)** — provision PostgreSQL 12+, configure Traefik or another reverse proxy, and deploy backend/frontend containers separately.
- **Air-gapped / offline** — mirror container images, manage certificate secrets manually, and disable automatic updates.

## Environment Variables

| Variable | Purpose | Notes |
|----------|---------|-------|
| `ENCRYPTED_STORAGE_MASTER_KEY` | Master key for encrypting seal files and private keys. | Must be a 32-byte Fernet key. Store offline backups. |
| `SECRET_KEY` | JWT signing secret. | Generate with `openssl rand -base64 32`. |
| `DATABASE_URL` | Async SQLAlchemy DSN. | Example: `postgresql+asyncpg://user:pass@host:5432/db`. |
| `BACKEND_CORS_ORIGINS` | JSON array of trusted origins. | Format: `["https://example.com"]`. |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Bootstrap administrator account. | Change after first login. |

## Docker Compose Flow

1. **Prepare environment files** — copy `.env` and `.env.docker`, then edit secrets.
2. **Launch stack** — run `./deploy.sh up` to build images, run migrations, and start services.
3. **Verify services**
   - Backend API: <http://localhost:8000/health>
   - Frontend SPA: <http://localhost:3000>
   - Traefik dashboard (optional): see compose file for port mapping.
4. **Create root CA** — login with admin credentials and generate the root certificate before issuing user certificates.

## Reverse Proxy Checklist

- Terminate TLS at Traefik or Nginx with automatically renewed certificates (Let’s Encrypt or internal CA).
- Forward the `X-Forwarded-*` headers to the backend for correct audit logging.
- Enforce HTTPS and redirect HTTP requests.

## Backup & Recovery

- **Database** — schedule daily dumps plus WAL archiving for PostgreSQL.
- **Secrets** — back up `.env` files, Fernet master key, and root CA private key offline.
- **Seals & uploads** — if configured on persistent volumes, replicate to secure storage.

## Monitoring & Alerting

- Expose FastAPI metrics through Prometheus exporters or sidecars.
- Configure Grafana dashboards for request rate, error rate, and signing latency.
- Enable alerting for failed signing jobs, CA certificate expiration, and disk usage.

## Next Steps

Refer to the Chinese deployment guide for:
- Hardening checklists for each infrastructure component.
- SELinux/AppArmor suggestions and firewall rules.
- High availability topology and disaster recovery drills.
