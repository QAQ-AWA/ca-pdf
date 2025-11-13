# Backend

This directory contains the FastAPI backend service for the monorepo.

## Getting started

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Database migrations

Database migrations are automated in production via the `scripts/prestart.sh` entrypoint script, which runs before the Gunicorn server starts.

### Automated migrations (Docker/Production)

When the backend container starts:
1. The prestart script waits for PostgreSQL to be ready (with exponential backoff)
2. Runs `alembic upgrade head` automatically (with retry logic)
3. Only then starts the Gunicorn application server

This ensures the database schema is always up-to-date without manual intervention.

### Manual migrations (Development)

For local development outside Docker:

```bash
# Apply migrations
poetry run alembic upgrade head

# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Downgrade migrations
poetry run alembic downgrade -1
```

### Migration script details

- **Location**: `backend/scripts/prestart.sh`
- **Database wait**: Up to 30 attempts with exponential backoff (1s, 2s, 4s, ..., 30s)
- **Migration retries**: Up to 3 attempts with 2s, 4s delays
- **Failure handling**: Container exits with error code if migrations fail
- **Logs**: All steps are logged with timestamps for debugging

## Testing

```bash
poetry run pytest
```

## Code Formatting

This project uses [black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort) for code formatting.

### Manual formatting
```bash
poetry run black app tests
poetry run isort app tests
```

### Pre-commit hooks (recommended)

To ensure code is formatted before each commit, install the pre-commit hooks:

```bash
poetry run pre-commit install
```

The hooks will automatically run black and isort on staged files before each commit.
