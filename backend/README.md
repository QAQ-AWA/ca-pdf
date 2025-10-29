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
