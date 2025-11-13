# syntax=docker/dockerfile:1.6

ARG PYTHON_VERSION=3.11.7
ARG POETRY_VERSION=1.8.3

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder-base
ENV DEBIAN_FRONTEND=noninteractive \
    POETRY_HOME=/opt/poetry \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        gcc \
        libffi-dev \
        libjpeg62-turbo-dev \
        libpq-dev \
        libssl-dev \
        pkg-config \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s "${POETRY_HOME}/bin/poetry" /usr/local/bin/poetry \
    && ${POETRY_HOME}/bin/poetry self add "poetry-plugin-export==1.8.0"

WORKDIR /build

FROM builder-base AS deps
COPY backend/pyproject.toml backend/poetry.lock ./
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=secret,id=poetry_token,required=false \
    sh -c 'set -e; \
        if [ -f /run/secrets/poetry_token ]; then \
          poetry config pypi-token.pypi "$(cat /run/secrets/poetry_token)"; \
        fi; \
        poetry export --only main --without-hashes -f requirements.txt -o requirements.txt; \
        python -m pip install --upgrade pip setuptools wheel; \
        python -m pip wheel --no-cache-dir --wheel-dir /wheelhouse -r requirements.txt; \
        if [ -f /run/secrets/poetry_token ]; then \
          poetry config --unset pypi-token.pypi; \
        fi'

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ARG APP_USER=app
ARG APP_GROUP=app
ARG COMMIT_SHA="unknown"
ARG BUILD_VERSION="dev"
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    WEB_CONCURRENCY=2 \
    COMMIT_SHA=${COMMIT_SHA} \
    BUILD_VERSION=${BUILD_VERSION}
LABEL org.opencontainers.image.title="backend" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.revision="${COMMIT_SHA}"
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        file \
        libffi8 \
        libjpeg62-turbo \
        libmagic1 \
        libpq5 \
        libssl3 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system "${APP_GROUP}" \
    && useradd --system --gid "${APP_GROUP}" --create-home --home-dir "${APP_HOME}" "${APP_USER}"

WORKDIR ${APP_HOME}
RUN python -m venv ${VIRTUAL_ENV} \
    && ${VIRTUAL_ENV}/bin/pip install --no-cache-dir --upgrade pip

COPY --from=deps /wheelhouse /tmp/wheels
COPY --from=deps /build/requirements.txt /tmp/requirements.txt
RUN ${VIRTUAL_ENV}/bin/pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r /tmp/requirements.txt \
    && rm -rf /tmp/wheels /tmp/requirements.txt

COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini

RUN chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}
USER ${APP_USER}

EXPOSE 8000
HEALTHCHECK --start-period=40s --interval=30s --timeout=10s --retries=3 CMD curl -f "http://127.0.0.1:${APP_PORT}/health" || exit 1

CMD ["sh", "-c", "gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers ${WEB_CONCURRENCY:-2} --bind ${APP_HOST}:${APP_PORT}"]
