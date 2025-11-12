# Contributing Guide

> **Status**: Contribution guidelines and process
> **Target Audience**: Contributors and developers
> **Last Updated**: 2024

Thank you for your interest in contributing to ca-pdf! This guide explains how to contribute to the project.

## Code of Conduct

We are committed to maintaining a respectful and inclusive community. Please treat everyone with kindness and respect.

## Getting Started

### Prerequisites

- Git 2.0+
- Python 3.11+
- Node.js 18+
- Docker (optional but recommended)
- GitHub account

### Fork and Clone

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/ca-pdf.git
cd ca-pdf

# Add upstream remote
git remote add upstream https://github.com/QAQ-AWA/ca-pdf.git

# Fetch latest changes
git fetch upstream
```

## Development Workflow

### 1. Create a Branch

```bash
# Update local main
git checkout main
git fetch upstream
git rebase upstream/main

# Create feature branch
git checkout -b feat/your-feature-name
```

Branch naming conventions:
- Feature: `feat/description`
- Bug fix: `fix/description`
- Documentation: `docs/description`
- Chore: `chore/description`

### 2. Make Changes

Follow code style guidelines:

**Python (Backend)**
```python
# Use type hints
async def get_user(user_id: int) -> Optional[User]:
    """Get user by ID."""
    return await session.get(User, user_id)
```

**TypeScript (Frontend)**
```typescript
// Use strict types
interface User {
  id: number;
  email: string;
}

const getUser = async (id: number): Promise<User> => {
  // Implementation
};
```

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest --cov=app

# Frontend tests
cd frontend
npm test

# Type checking
mypy app

# Code formatting
black app tests
isort app tests
```

### 4. Commit Changes

Follow Conventional Commits format:

```
feat: add user authentication
fix: resolve PDF signing error
docs: update API documentation
test: add user auth tests
chore: upgrade dependencies

The commit message includes a brief description.
Include more details if the change is complex.

Fixes #123
```

Commit best practices:
- Make atomic commits (one logical change per commit)
- Write clear commit messages
- Reference related issues/PRs
- Don't include unrelated changes

```bash
git add .
git commit -m "feat: add user authentication"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feat/your-feature-name

# Create pull request on GitHub
# - Fill in the PR template
# - Link related issues
# - Describe your changes
```

## Code Quality Requirements

### Python Backend

- **Code Style**: PEP 8 via Black
  ```bash
  poetry run black app tests
  ```

- **Import Sorting**: isort
  ```bash
  poetry run isort app tests
  ```

- **Type Checking**: mypy (strict mode)
  ```bash
  poetry run mypy app
  ```

- **Testing**: pytest with 80%+ coverage
  ```bash
  poetry run pytest --cov=app
  ```

### TypeScript Frontend

- **Linting**: ESLint
  ```bash
  npm run lint
  ```

- **Formatting**: Prettier
  ```bash
  npm run format
  ```

- **Type Checking**: TypeScript compiler
  ```bash
  npm run type-check
  ```

- **Testing**: Jest or Vitest with 80%+ coverage
  ```bash
  npm test -- --coverage
  ```

## Testing

### Backend

Write tests for all functions:

```python
import pytest
from app.services import create_user

@pytest.mark.asyncio
async def test_create_user(session):
    """Test user creation."""
    user = await create_user(
        session=session,
        username="testuser",
        email="test@example.com"
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
```

### Frontend

Test React components:

```typescript
import { render, screen } from '@testing-library/react';
import { LoginForm } from './LoginForm';

test('renders login form', () => {
  render(<LoginForm />);
  expect(screen.getByText('Login')).toBeInTheDocument();
});
```

## Documentation

### Update Relevant Docs

- Update README if behavior changed
- Add API documentation for new endpoints
- Update CHANGELOG.md
- Add examples for new features

### Documentation Format

```markdown
# Section Title

Brief introduction.

## Subsection

Details here.

### Code Example

\`\`\`python
# Code here
\`\`\`

## See Also

- Related doc link
```

## Pull Request Process

### Before Submission

1. ✅ All tests pass locally
2. ✅ Code is formatted and linted
3. ✅ Type checking passes
4. ✅ No console errors/warnings
5. ✅ Documentation is updated
6. ✅ Commit messages are clear

### Submission

1. Create PR with detailed description
2. Link related issues (#123)
3. Include before/after screenshots if UI changed
4. Be responsive to feedback

### Code Review

Reviews will check:
- ✓ Code quality and style
- ✓ Functionality and correctness
- ✓ Test coverage
- ✓ Documentation completeness
- ✓ Security implications
- ✓ Performance impact

Be constructive in receiving feedback:
- Respond to all comments
- Request clarification if needed
- Make requested changes
- Push updates to PR branch
- Request re-review when ready

## Common Contribution Scenarios

### Scenario 1: Adding a New API Endpoint

1. **Create migration** (if needed)
   ```bash
   alembic revision --autogenerate -m "add_endpoint_table"
   ```

2. **Add model** in `backend/app/models/`
   ```python
   class NewEntity(Base):
       __tablename__ = "new_entities"
       id = Column(Integer, primary_key=True)
   ```

3. **Add schema** in `backend/app/schemas/`
   ```python
   class NewEntitySchema(BaseModel):
       id: int
   ```

4. **Add endpoint** in `backend/app/api/`
   ```python
   @router.get("/{id}")
   async def get_entity(id: int, session: AsyncSession = Depends(get_session)):
       # Implementation
   ```

5. **Add tests** in `backend/tests/`

6. **Update documentation** in `docs/en/API.md`

### Scenario 2: Fixing a Bug

1. **Identify root cause**
   - Use debugging and logging
   - Review related code
   - Check similar cases

2. **Create minimal reproduction**
   - Isolate the problem
   - Document steps to reproduce

3. **Fix the bug**
   - Address root cause, not symptoms
   - Consider edge cases
   - Check for similar issues

4. **Add regression test**
   - Test should fail before fix
   - Test should pass after fix

5. **Document the fix**
   - Reference issue number
   - Explain what was wrong
   - Explain the fix

### Scenario 3: Improving Performance

1. **Measure baseline**
   - Current response time
   - Resource usage
   - Bottlenecks identified

2. **Implement improvement**
   - Use profiling tools
   - Test thoroughly
   - Ensure no regression

3. **Verify improvement**
   - Measure improvement percentage
   - Document metrics
   - Include benchmarks

## Release Process

Maintainers will handle:

1. **Version bumping** (semantic versioning)
2. **Changelog updates**
3. **Tag creation**
4. **Release notes**
5. **Package publication**

Current version: Check `pyproject.toml` or `package.json`

## Communication

- **Discussions**: GitHub Discussions for ideas
- **Issues**: GitHub Issues for bugs/features
- **Emails**: [7780102@qq.com](mailto:7780102@qq.com)
- **Mentions**: @QAQ-AWA for urgent matters

## Style Guide

### Naming Conventions

**Python**
```python
# Variables and functions: snake_case
user_name = "John"
def get_user_by_id(user_id: int) -> User:
    pass

# Classes: PascalCase
class UserService:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_ATTEMPTS = 3
```

**TypeScript**
```typescript
// Variables and functions: camelCase
const userName = "John";
function getUserById(userId: number): User {
  return ...;
}

// Types and interfaces: PascalCase
interface User {
  id: number;
}

type UserId = number;

// Constants: UPPER_SNAKE_CASE
const MAX_ATTEMPTS = 3;
```

### Comments

Write comments for complex logic:

```python
# Use comments for WHY, not WHAT
# Retry exponential backoff: 1s, 2s, 4s, 8s
delay = 2 ** attempt_count
```

### Error Handling

```python
try:
    result = await database.query(sql)
except DatabaseError as e:
    logger.error("Database query failed: %s", str(e))
    raise ServiceError(f"Failed to query: {e}") from e
```

## Troubleshooting Common Issues

### Pre-commit Hooks Fail

```bash
# Fix formatting
black app tests
isort app tests

# Check types
mypy app

# Run tests
pytest
```

### Test Failures

```bash
# Run failing test with verbose output
pytest tests/test_file.py::test_name -v

# Run with print statements
pytest -s tests/test_file.py
```

### Merge Conflicts

```bash
# Resolve conflicts manually in editor
# Then:
git add .
git commit -m "Resolve merge conflicts"
git push
```

## For More Information

For complete contribution guidelines including:
- Detailed code standards
- Testing best practices
- Review process details
- Release procedures
- Maintainer workflows

Please refer to the [Complete Contributing Guide (Chinese)](../zh/CONTRIBUTING.md).

## Resources

- [Development Guide](./DEVELOPMENT.md) - Setup and development
- [Architecture Guide](./ARCHITECTURE.md) - System design
- [GitHub Issues](https://github.com/QAQ-AWA/ca-pdf/issues) - Reported issues
- [GitHub Discussions](https://github.com/QAQ-AWA/ca-pdf/discussions) - Community

## Thank You!

Your contributions help make ca-pdf better for everyone. We appreciate your time and effort!

---

**Last updated**: 2024
