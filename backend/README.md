# Backend

This directory contains the FastAPI backend service for the monorepo.

## Getting started

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Database migrations

```bash
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "description"
```

## Testing

```bash
poetry run pytest
```
