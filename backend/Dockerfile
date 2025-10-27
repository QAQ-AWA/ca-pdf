# syntax=docker/dockerfile:1.5

FROM python:3.11-slim as builder

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" && \
    mkdir -p /app

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry export --only main --without-hashes --format=requirements.txt \
    --output /tmp/requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/requirements.txt

COPY app app
COPY alembic.ini alembic.ini

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
