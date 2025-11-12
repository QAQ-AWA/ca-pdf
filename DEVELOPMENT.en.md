# ca-pdf Development Guide

> 📖 **Documentation Navigation**: [README](./README.en.md) · [Documentation Index](./DOCUMENTATION.md) · [API Reference](./API.en.md) · [Architecture](./ARCHITECTURE.en.md)
> 🎯 **Target Audience**: Developers / Contributors
> ⏱️ **Estimated Reading Time**: 50 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This guide helps developers set up local development environment, understand code organization, run tests, and contribute to ca-pdf. For system architecture details, see [ARCHITECTURE.en.md](./ARCHITECTURE.en.md); for REST API reference, see [API.en.md](./API.en.md).

---

## 📋 Development Environment Setup

### Prerequisites

- **Python 3.11+** with Poetry
- **Node.js 16+** with npm
- **PostgreSQL 12+** (or SQLite for development)
- **Docker** and **Docker Compose** (recommended for database)
- **Git** version control

### Quick Setup

```bash
# Clone repository
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf

# Install all dependencies
make install

# Set up environment
cp .env.example .env
# Edit .env and generate keys:
# openssl rand -base64 32 (for SECRET_KEY)
# openssl rand -base64 32 (for ENCRYPTED_STORAGE_MASTER_KEY)

# Initialize database
cd backend && poetry run alembic upgrade head && cd ..

# Start development servers in separate terminals
make dev-backend
make dev-frontend
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/         # Route implementations
│   │   │   ├── auth.py
│   │   │   ├── certificates.py
│   │   │   ├── pdf_signing.py
│   │   │   └── users.py
│   │   └── dependencies.py    # Dependency injection
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── crud/                 # Database CRUD operations
│   ├── services/             # Business logic layer
│   ├── core/                 # Configuration, security, encryption
│   └── main.py              # FastAPI application entry
├── migrations/               # Alembic database migrations
├── tests/                   # Unit and integration tests
└── pyproject.toml          # Poetry dependencies

frontend/
├── src/
│   ├── pages/              # Page components
│   ├── components/         # Reusable UI components
│   ├── lib/                # Utilities, API client, types
│   └── main.tsx            # React entry point
├── Dockerfile              # Container image
└── package.json           # npm dependencies
```

---

## 🔧 Development Commands

### Backend Commands

```bash
# Install dependencies
cd backend && poetry install

# Run tests
poetry run pytest -v

# Type checking
poetry run mypy app

# Code formatting
poetry run black app tests
poetry run isort app tests

# Linting
poetry run ruff check app

# Database migrations
poetry run alembic upgrade head
poetry run alembic revision -m "description"

# Start development server
poetry run uvicorn app.main:app --reload

# Run REPL
poetry run python
```

### Frontend Commands

```bash
# Install dependencies
cd frontend && npm install

# Development server
npm run dev

# Build production
npm run build

# Type checking
npm run typecheck

# Linting
npm run lint

# Formatting
npm run format

# Run tests
npm run test
```

### Makefile Commands

```bash
# Install all
make install

# Development servers
make dev-backend
make dev-frontend

# Code checks
make lint
make format
make typecheck

# Testing
make test
make test-backend
make test-frontend
```

---

## 📝 Code Standards

### Python Standards

**Style & Formatting**
- Format: Black (line length 100)
- Import sorting: isort
- Linting: ruff
- Type checking: mypy strict mode

**Example**:
```python
from typing import Optional
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)
```

**Naming Conventions**
- Classes: PascalCase (e.g., `CertificateService`)
- Functions: snake_case (e.g., `create_certificate`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_PDF_SIZE`)
- Private: prefix with `_` (e.g., `_validate_pdf`)

### TypeScript Standards

**Style & Formatting**
- Format: Prettier
- Linting: ESLint
- Type checking: TypeScript strict mode

**Example**:
```typescript
import { useState, useEffect } from 'react';
import { Certificate, ApiError } from '@/lib/types';
import { api } from '@/lib/api';

export const CertificateList: React.FC = () => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    const loadCertificates = async () => {
      try {
        const data = await api.certificates.list();
        setCertificates(data);
      } catch (err) {
        setError(err as ApiError);
      }
    };

    loadCertificates();
  }, []);

  return (
    <div>
      {certificates.map((cert) => (
        <div key={cert.id}>{cert.subject}</div>
      ))}
    </div>
  );
};
```

---

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_auth.py::test_login -v

# Run with coverage
poetry run pytest --cov=app tests/

# Run integration tests
poetry run pytest tests/integration/ -v
```

### Frontend Testing

```bash
# Run tests
npm run test

# Run specific test file
npm run test -- components/CertificateList.test.tsx

# Run with coverage
npm run test -- --coverage
```

### Test Organization

```
backend/tests/
├── conftest.py              # Pytest configuration
├── test_auth.py             # Authentication tests
├── test_certificates.py     # Certificate tests
├── integration/             # Integration tests
└── fixtures/                # Test data

frontend/__tests__/
├── components/              # Component tests
├── lib/                     # Utility tests
└── fixtures/                # Mock data
```

---

## 🔌 API Development

### Creating New Endpoints

1. **Define Schema** (`schemas/your_feature.py`):
```python
from pydantic import BaseModel

class YourFeatureRequest(BaseModel):
    field: str

class YourFeatureResponse(BaseModel):
    id: int
    field: str
```

2. **Create Service** (`services/your_service.py`):
```python
from app.models import YourModel

class YourService:
    async def create_item(self, request: YourFeatureRequest) -> YourModel:
        # Business logic here
        pass
```

3. **Add Route** (`api/endpoints/your_feature.py`):
```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/", response_model=YourFeatureResponse)
async def create(
    request: YourFeatureRequest,
    service: YourService = Depends(get_service),
):
    return await service.create_item(request)
```

4. **Register in Main App** (`main.py`):
```python
from app.api.endpoints import your_feature

app.include_router(
    your_feature.router,
    prefix="/api/v1/your-feature",
    tags=["Your Feature"]
)
```

---

## 🗄️ Database Changes

### Creating Migrations

```bash
cd backend

# Generate migration
poetry run alembic revision -m "describe_change"

# Edit the generated file in migrations/versions/

# Apply migration
poetry run alembic upgrade head

# Verify
poetry run alembic current
```

### Migration Template

```python
# migrations/versions/001_initial.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'])

def downgrade():
    op.drop_table('users')
```

---

## 🐛 Debugging

### Backend Debugging

```bash
# Debug with print statements
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")

# Interactive debugger (with pdb)
import pdb; pdb.set_trace()

# IDE debugging (VS Code)
# Add to .vscode/launch.json:
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

```bash
# Browser DevTools (F12)
# Component debugging in React DevTools

# Console logging
console.log('Debug:', data);

# Debugger statement
debugger;

# IDE debugging (VS Code)
# Add to .vscode/launch.json:
{
  "type": "chrome",
  "request": "launch",
  "name": "Launch Chrome",
  "url": "http://localhost:5173",
  "webRoot": "${workspaceFolder}/frontend"
}
```

---

## 📦 Dependency Management

### Backend Dependencies

```bash
cd backend

# Add dependency
poetry add package_name

# Add dev dependency
poetry add --group dev package_name

# Update dependencies
poetry update

# Show dependencies
poetry show
poetry show --tree
```

### Frontend Dependencies

```bash
cd frontend

# Add dependency
npm install package_name

# Add dev dependency
npm install --save-dev package_name

# Update dependencies
npm update

# Show outdated packages
npm outdated
```

---

## 🚀 Contributing Guidelines

### Workflow

1. **Create branch**: `git checkout -b feature/feature-name`
2. **Make changes**: Implement your feature
3. **Test**: `make test`
4. **Format**: `make format`
5. **Type check**: `make typecheck`
6. **Lint**: `make lint`
7. **Commit**: `git commit -m "feat: description"`
8. **Push**: `git push origin feature/feature-name`
9. **Create PR**: Open pull request on GitHub

### Commit Message Format

Follow Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, perf, test, chore

**Example**:
```
feat(auth): add JWT token rotation

- Implement automatic token refresh
- Add token blacklist management
- Update tests

Closes #123
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change

## Testing
- [ ] Tests added/updated
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added
- [ ] Documentation updated
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

**Last Updated**: 2024
**Version**: 1.0
