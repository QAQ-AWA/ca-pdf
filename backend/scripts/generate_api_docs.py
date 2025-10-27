#!/usr/bin/env python3
"""Generate offline API documentation artefacts for the FastAPI service."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Provision the minimum configuration required for settings validation before we
# import the application factory. The backend enforces the presence of the
# encrypted storage master key and expects a database URL.
DEFAULT_FERNET_KEY = "k6ER8Q1ZIHH2wUuD9eYANxE0JaROtDi2D1eMd7zXJ6E="

os.environ.setdefault("ENCRYPTED_STORAGE_MASTER_KEY", DEFAULT_FERNET_KEY)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///tmp/openapi-docs.db")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "[\"http://localhost:3000\"]")

from app.main import create_application  # noqa: E402


def main() -> None:
    app = create_application()
    openapi_schema = app.openapi()

    docs_dir = Path(__file__).resolve().parents[2] / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)

    openapi_path = docs_dir / "openapi.json"
    openapi_path.write_text(
        json.dumps(openapi_schema, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    swagger_html = get_swagger_ui_html(
        openapi_url="openapi.json",
        title=f"{app.title} – Swagger UI",
    )
    (docs_dir / "swagger.html").write_text(
        swagger_html.body.decode("utf-8"),
        encoding="utf-8",
    )

    redoc_html = get_redoc_html(
        openapi_url="openapi.json",
        title=f"{app.title} – ReDoc",
    )
    (docs_dir / "redoc.html").write_text(
        redoc_html.body.decode("utf-8"),
        encoding="utf-8",
    )

    print(f"Generated API documentation in {docs_dir}")


if __name__ == "__main__":
    main()
