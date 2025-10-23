.PHONY: install install-backend install-frontend \
	dev-backend dev-frontend \
	lint lint-backend lint-frontend \
	format format-backend format-frontend \
	test test-backend test-frontend \
	typecheck typecheck-backend typecheck-frontend

install: install-backend install-frontend

install-backend:
	cd backend && poetry install

install-frontend:
	cd frontend && npm install

dev-backend:
	./scripts/dev_backend.sh

dev-frontend:
	./scripts/dev_frontend.sh

lint: lint-backend lint-frontend

lint-backend:
	cd backend && poetry run black --check app tests
	cd backend && poetry run isort --check-only app tests

lint-frontend:
	cd frontend && npm run lint

format: format-backend format-frontend

format-backend:
	cd backend && poetry run black app tests
	cd backend && poetry run isort app tests

format-frontend:
	cd frontend && npm run format

test: test-backend test-frontend

test-backend:
	cd backend && poetry run pytest

test-frontend:
	cd frontend && npm run test

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	cd backend && poetry run mypy app

typecheck-frontend:
	cd frontend && npm run typecheck
