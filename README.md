# Monorepo Scaffold

This repository provides a monorepo layout with a FastAPI backend and a Vite + React + TypeScript frontend. Shared tooling lives under the `config/` directory, while convenience scripts and Make targets help streamline local development.

## Structure

```
.
├── backend/          # FastAPI application packaged with Poetry
├── frontend/         # Vite + React + TypeScript web client
├── config/           # Shared linting/formatting configuration
├── scripts/          # Developer workflow helpers
├── Makefile          # High-level commands for common workflows
└── .env.example      # Sample environment configuration
```

## Getting started

1. Copy the environment template and update values as needed:
   ```bash
   cp .env.example .env
   ```
2. Install backend and frontend dependencies:
   ```bash
   make install
   ```
3. Run the development servers:
   ```bash
   make dev-backend
   make dev-frontend
   ```

## Available commands

| Command                | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `make install`         | Install backend (Poetry) and frontend (npm) deps. |
| `make dev-backend`     | Start the FastAPI backend with auto-reload.       |
| `make dev-frontend`    | Start the Vite development server.                |
| `make lint`            | Run linting for both backend and frontend.        |
| `make format`          | Apply code formatting in both projects.           |
| `make test`            | Execute backend pytest suite and frontend Vitest. |
| `make typecheck`       | Run mypy and TypeScript type checks.              |

## Tooling highlights

- **Backend**: FastAPI, Poetry, pytest, mypy, black, isort.
- **Frontend**: Vite, React, TypeScript, Vitest, Testing Library, ESLint, Prettier.
- **Shared config**: Centralised ESLint and Prettier rules in `config/` for reuse across packages.
