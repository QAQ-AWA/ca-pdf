# Development Guide

> **Status**: Local development and contributing guide
> **Target Audience**: Developers and contributors
> **Last Updated**: 2024

This guide covers setting up a local development environment for ca-pdf and contributing code changes.

## Environment Setup

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Docker**: 20.10+ (optional, but recommended)
- **Git**: 2.0+
- **PostgreSQL**: 14+ (or use SQLite for testing)

### Quick Start with Docker

The fastest way to set up a development environment:

```bash
# Clone the repository
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf

# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# The application will be available at:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

If you prefer not to use Docker:

#### Backend Setup

```bash
# Install Python dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Setup database
export DATABASE_URL="postgresql://user:password@localhost/ca_pdf_dev"
alembic upgrade head

# Run backend
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
# Install Node dependencies
cd frontend
npm install

# Start development server
npm run dev

# Open browser to http://localhost:5173
```

## Project Structure

```
ca-pdf/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Core utilities (security, config)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── api/            # API endpoints
│   │   ├── db/             # Database utilities
│   │   └── main.py         # Application entry point
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   └── pyproject.toml      # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── store/          # Redux store
│   │   ├── api/            # API client
│   │   └── App.tsx         # Main app component
│   ├── public/             # Static assets
│   └── package.json        # Node dependencies
├── docs/                   # Documentation
│   ├── zh/                 # Chinese documentation
│   └── en/                 # English documentation
└── docker-compose.yml      # Docker Compose configuration
```

## Backend Development

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

```bash
# Type checking
mypy app

# Code formatting check
black --check app tests

# Import sorting check
isort --check-only app tests

# Linting
pylint app
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Review migration file and edit if needed
vim alembic/versions/*.py

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### API Development

Add new endpoints in `backend/app/api/`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/{item_id}")
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Get item by ID"""
    # Implementation
    pass
```

### Working with Database

```python
from app.db import AsyncSessionLocal
from app.models import User

# Query example
async with AsyncSessionLocal() as session:
    user = await session.get(User, 1)
    # Use user object
```

## Frontend Development

### Running Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test AuthPage.test.tsx
```

### Building Components

React components should:

1. Use functional components with hooks
2. Have proper TypeScript types
3. Include error boundary support
4. Follow accessibility standards (WCAG 2.1)

Example component:

```tsx
import React from 'react';
import { Box, Button, TextField } from '@mui/material';

interface Props {
  onSubmit: (value: string) => void;
  loading?: boolean;
}

export const InputForm: React.FC<Props> = ({ onSubmit, loading }) => {
  const [value, setValue] = React.useState('');

  return (
    <Box component="form" onSubmit={() => onSubmit(value)}>
      <TextField
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={loading}
      />
      <Button type="submit" loading={loading}>
        Submit
      </Button>
    </Box>
  );
};
```

### Styling

Use Material-UI theming:

```tsx
import { useTheme } from '@mui/material/styles';

const MyComponent = () => {
  const theme = useTheme();
  
  return (
    <Box sx={{ color: theme.palette.primary.main }}>
      Content
    </Box>
  );
};
```

## Code Style and Standards

### Python Standards

- Follow PEP 8
- Use type hints for all functions
- Format with Black
- Sort imports with isort

Example:

```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(user_id: int, session: AsyncSession) -> Optional[User]:
    """Get user by ID."""
    return await session.get(User, user_id)
```

### TypeScript Standards

- Use strict TypeScript mode
- No `any` types without justification
- Use interfaces for object types
- Use enums for constants

Example:

```typescript
interface User {
  id: number;
  email: string;
  roles: Role[];
}

enum Role {
  Admin = 'admin',
  User = 'user',
  Auditor = 'auditor',
}
```

## Debugging

### Backend Debugging

Use VS Code with Python extension:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
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

1. Open Developer Tools (F12)
2. Set breakpoints in source files
3. Use Redux DevTools extension

## Git Workflow

### Branch Naming

- Feature: `feat/description`
- Bug fix: `fix/description`
- Documentation: `docs/description`
- Chore: `chore/description`

### Commit Messages

Follow Conventional Commits format:

```
feat: add user authentication
fix: resolve PDF signing error
docs: update API documentation
test: add tests for certificate validation
chore: update dependencies
```

### Creating Pull Request

1. Push to your branch
2. Create pull request on GitHub
3. Ensure CI checks pass
4. Request review from team members
5. Address review comments
6. Merge when approved

## Testing Guidelines

- Aim for 80%+ code coverage
- Test both happy path and error cases
- Use fixtures for common test data
- Test async code with pytest-asyncio

Example test:

```python
import pytest
from app.models import User
from app.api import get_user

@pytest.mark.asyncio
async def test_get_user(session):
    """Test retrieving a user."""
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    await session.commit()
    
    result = await get_user(user.id, session)
    assert result.username == "testuser"
```

## Performance Optimization

### Database Optimization

- Use async database calls
- Implement pagination for large datasets
- Add database indexes on frequently queried columns
- Use query optimization techniques

### Frontend Optimization

- Use React.memo for expensive components
- Implement code splitting with React.lazy
- Optimize images (use modern formats)
- Minimize bundle size

## Documentation

Add docstrings to functions:

```python
async def sign_pdf(document_id: int, cert_id: int) -> bytes:
    """
    Sign a PDF document with the specified certificate.
    
    Args:
        document_id: ID of the document to sign
        cert_id: ID of the certificate to use
    
    Returns:
        Signed PDF as bytes
    
    Raises:
        DocumentNotFound: If document doesn't exist
        CertificateNotValid: If certificate is not valid
    """
    # Implementation
```

## Dependency Management

### Backend

```bash
# Add dependency
pip install new-package
pip install new-package -e .

# Update requirements
pip freeze > requirements.txt
```

### Frontend

```bash
# Add dependency
npm install new-package

# Add dev dependency
npm install --save-dev new-package-dev
```

## Troubleshooting Development

### Port Already in Use

```bash
# Find and kill process using port
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
psql postgresql://user:password@localhost/ca_pdf_dev

# Review DATABASE_URL
echo $DATABASE_URL
```

### Module Import Errors

```bash
# Reinstall in dev mode
pip install -e ".[dev]"

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

## For More Details

For complete development documentation including:
- Architecture overview
- Database schema documentation
- API development guidelines
- Testing best practices
- Performance optimization techniques
- Debugging strategies

Please refer to the [Complete Development Guide (Chinese)](../zh/DEVELOPMENT.md).

## Additional Resources

- [Architecture Guide](./ARCHITECTURE.md) - System design and components
- [Contributing Guide](./CONTRIBUTING.md) - Contribution process
- [API Documentation](./API.md) - API reference
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment

---

**Last updated**: 2024
