# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS base
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.8.3" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s "${POETRY_HOME}/bin/poetry" /usr/local/bin/poetry

WORKDIR /src

FROM base AS deps
COPY backend/pyproject.toml backend/poetry.lock ./
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=secret,id=poetry_token,required=false \
    sh -c 'set -e; \
        if [ -f /run/secrets/poetry_token ]; then \
          poetry config pypi-token.pypi "$(cat /run/secrets/poetry_token)"; \
        fi; \
        poetry install --only main --no-root; \
        if [ -f /run/secrets/poetry_token ]; then \
          poetry config --unset pypi-token.pypi; \
        fi'

FROM deps AS builder
COPY backend/ ./
RUN --mount=type=cache,target=/root/.cache/pip \
    poetry install --only main

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PATH="/app/.venv/bin:$PATH"
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --home-dir /app app

WORKDIR ${APP_HOME}

COPY --from=builder /src/.venv .venv
COPY --from=builder /src/app ./app
COPY --from=builder /src/alembic.ini ./alembic.ini

RUN chown -R app:app ${APP_HOME}
USER app

EXPOSE 8000

HEALTHCHECK --start-period=30s --interval=30s --timeout=5s --retries=3 CMD curl -f "http://localhost:${UVICORN_PORT:-8000}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${UVICORN_HOST:-0.0.0.0} --port ${UVICORN_PORT:-8000}"]
