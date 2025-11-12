# Contributing Guide (Preview)

> **Quick summary:** This guide outlines the contribution process. The Chinese version includes detailed role expectations, review templates, and case studies.

## Workflow Overview

1. **Fork** the repository and create a feature branch (`feat/...`).
2. **Implement** code changes with tests and documentation updates.
3. **Run quality checks** before submitting:
   ```bash
   make lint
   make typecheck
   make test
   ```
4. **Open a pull request** following the Conventional Commit format (e.g., `feat: add pdf seal auditing`).
5. **Respond to reviews** and keep documentation synchronized with code changes.

## Coding Standards

- **Python**: black, isort, mypy (strict mode), pytest.
- **Frontend**: ESLint, Prettier, TypeScript strict mode, Vitest.
- **Commits**: Conventional Commits with clear scope and descriptive summary.
- **Tests**: Maintain ≥ 80% coverage and include regression tests for bugs.

## Documentation Expectations

- Update relevant sections in the documentation site (Chinese and English stubs if applicable).
- Record major documentation maintenance in `./MAINTENANCE_LOG.md`.
- Provide API contract updates in both `/docs/zh/API.md` and `/docs/en/API.md`.

## Code Review Checklist

- Does the change include appropriate tests?
- Are secrets, credentials, and config validations handled safely?
- Are migrations using short revision identifiers (< 32 characters)?
- Are user-facing errors localized and consistent?

## Communication

- GitHub Issues: bug reports and feature requests.
- GitHub Discussions: design proposals, community Q&A.
- Email: [7780102@qq.com](mailto:7780102@qq.com) for security-sensitive topics.

Refer to the Chinese document for detailed onboarding scenarios, contributor roles, and escalation policies.
