#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
cd backend

poetry run uvicorn app.main:app --reload --host "${UVICORN_HOST:-0.0.0.0}" --port "${UVICORN_PORT:-8000}"
