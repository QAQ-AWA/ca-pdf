# Backend

This directory contains the FastAPI backend service for the monorepo.

## Getting started

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Observability & diagnostics

The backend now emits structured JSON logs for every request, including request IDs that are also returned via the `X-Request-ID` response header. Metrics are exposed in Prometheus format via the configurable `/metrics` endpoint using `starlette-exporter`, and liveness/readiness probes are available at `/health`, `/health/live`, and `/health/ready`.

## Security & upload hardening

Inbound requests are protected with tightened CORS defaults, trusted proxy support, optional HTTPS redirects, and security headers managed by Starlette's `SecurityMiddleware`. File uploads are validated centrally to enforce MIME types, size limits, and safe handling of temporary files before they reach the signing services.

## Configuration

Key environment variables include:

- `LOG_LEVEL`, `METRICS_ENDPOINT`
- `ENABLE_CORS`, `CORS_ALLOW_*`, `CORS_EXPOSE_HEADERS`, `CORS_MAX_AGE`
- `TRUSTED_HOSTS`, `ENABLE_PROXY_HEADERS`, `PROXY_TRUSTED_HOSTS`
- `FORCE_HTTPS_REDIRECT`, `ENABLE_SECURITY_HEADERS`, `SECURITY_*`
- `PDF_MAX_BYTES`, `PDF_ALLOWED_CONTENT_TYPES`, `PDF_BATCH_MAX_COUNT`

Refer to [`../.env.example`](../.env.example) and [`../.env.docker.example`](../.env.docker.example) for the full list of configurable settings and suggested defaults.

## Database migrations

```bash
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "description"
```

## Testing

```bash
poetry run pytest
```
