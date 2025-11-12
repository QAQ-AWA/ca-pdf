# Development Guide (Preview)

> **Status:** Core topics are summarized here. Detailed code walkthroughs, screenshots, and step-by-step tutorials remain in the Chinese edition.

## Prerequisites

- Python 3.11+
- Node.js 16+
- Docker Engine 23+ with Docker Compose v2
- Poetry (backend dependencies)
- pnpm or npm (frontend dependencies)

## Local Environment Setup

```bash
# Clone repository
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf

# Install backend dependencies
poetry install

# Install frontend dependencies
cd frontend
pnpm install
cd ..
```

## Useful Make Targets

| Command | Description |
|---------|-------------|
| `make install` | Install backend dev dependencies. |
| `make dev-backend` | Run FastAPI with reload at <http://localhost:8000>. |
| `make dev-frontend` | Start Vite dev server at <http://localhost:3000>. |
| `make lint` | Run black, isort, eslint, prettier. |
| `make typecheck` | Run mypy and TypeScript checks. |
| `make test` | Run backend and frontend test suites. |

## Backend Highlights

- **Framework:** FastAPI + SQLAlchemy (async).
- **Database:** PostgreSQL in production, SQLite for tests.
- **Migrations:** Alembic with async support (short revision IDs required).
- **Security:** JWT auth, bcrypt password hashing, encrypted private key storage.

### Running Database Migrations

```bash
poetry run alembic upgrade head
```

Ensure `DATABASE_URL` and `ENCRYPTED_STORAGE_MASTER_KEY` are defined.

## Frontend Highlights

- **Stack:** React, TypeScript, Vite, React Router.
- **Styling:** Tailwind CSS + custom components.
- **API Client:** Located in `frontend/src/lib/api.ts` with Axios instance and interceptors.

### Frontend Dev Server

```bash
make dev-frontend
```

The app proxies API requests to the backend via environment-configured URLs.

## Testing Strategy

- **Backend:** Pytest with async fixtures (`backend/tests`).
- **Frontend:** Vitest + React Testing Library (`frontend/src/**/*.test.tsx`).
- **Coverage:** Target ≥ 80% overall. PRs must pass CI pipelines.

## Contribution Workflow

1. Create a feature branch.
2. Implement changes with accompanying tests and documentation updates.
3. Run `make lint`, `make typecheck`, and `make test` locally.
4. Submit a pull request following Conventional Commit messages.

Refer to the Chinese documentation for extended guidelines, code architecture deep dives, and troubleshooting tips.
