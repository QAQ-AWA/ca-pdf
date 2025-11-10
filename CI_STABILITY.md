# CI Stability Guide

This document provides comprehensive guidance on maintaining CI stability for the ca-pdf project after the complete stabilization refactor.

## Overview

The ca-pdf project has undergone a comprehensive CI stabilization refactor to address systemic issues that caused over 30 failing PRs. This refactor focused on creating a **stable, reliable, and maintainable** CI system.

## CI Architecture

### Workflows

1. **Backend CI** (`.github/workflows/backend-ci.yml`)
   - Purpose: Lint, type check, test, and migration validation for FastAPI backend
   - Timeout: 15 minutes total with individual step timeouts
   - Database: PostgreSQL 15 with proper health checks

2. **Frontend CI** (`.github/workflows/frontend-ci.yml`)
   - Purpose: Lint and test React frontend with Vitest
   - Timeout: 10 minutes total with individual step timeouts
   - Testing: Vitest with jsdom environment and optimized threading

3. **Docker Build** (`.github/workflows/docker-build.yml`)
   - Purpose: Build and publish multi-architecture Docker images
   - Timeout: 30 minutes
   - Platforms: linux/amd64, linux/arm64

## Key Optimizations

### 1. Timeout Management
- **Backend CI**: 15 minutes total, with specific timeouts per step
- **Frontend CI**: 10 minutes total, with specific timeouts per step  
- **Docker Build**: 30 minutes total
- **Individual steps**: Appropriate timeouts to prevent hanging

### 2. Dependency Management
- **Backend**: Poetry with optimized caching strategy
- **Frontend**: npm ci with lock file caching
- **Python**: Locked to 3.12 in CI, ^3.11 in development
- **Node.js**: Locked to 20.x LTS

### 3. Performance Optimizations
- **Backend Tests**: Pytest with timeout support, short traceback, fail-fast
- **Frontend Tests**: Vitest with threading, isolated tests, 10s timeout
- **Type Checking**: MyPy with optimized configuration
- **Database**: PostgreSQL health checks and ready state validation

### 4. Caching Strategy
- **Poetry**: Virtualenv and cache piped to GitHub Actions cache
- **npm**: Dependency caching with lock file as key
- **Docker**: Multi-stage build caching with GitHub Container Registry

## Environment Configuration

### Backend Environment Variables
All required environment variables are explicitly defined in CI with proper formats:

```yaml
BACKEND_CORS_ORIGINS: '["http://testclient"]'  # JSON array format
DATABASE_URL: "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/backend"
ENCRYPTED_STORAGE_MASTER_KEY: "L9oZbBY7bRHt9aCJloPAV9ooa-QKdfYU0uf5KIKGJ28="
```

### Frontend Configuration
- Node.js 20.x LTS
- npm with ci for clean installs
- Vitest with optimized threading and timeouts

## Testing Strategy

### Backend Testing
- **Framework**: pytest with asyncio support
- **Database**: SQLite for unit tests, PostgreSQL for integration
- **Coverage**: XML and terminal reporting
- **Timeout**: 300 seconds per test with pytest-timeout
- **Markers**: slow, integration, unit for categorization

### Frontend Testing
- **Framework**: Vitest with jsdom environment
- **Threading**: 1-4 threads for optimal performance
- **Timeout**: 10 seconds per test, 10 seconds for hooks
- **Coverage**: V8 provider with LCOV and text summary

## Common Issues and Solutions

### 1. Backend Test Timeouts
**Problem**: Tests hanging indefinitely
**Solution**: 
- Added pytest-timeout dependency
- Individual test timeout of 300 seconds
- Fail-fast with `-x` flag
- Short traceback format for faster debugging

### 2. Database Connection Issues
**Problem**: PostgreSQL not ready when tests start
**Solution**:
- Added health check with retry logic
- 20 attempts with 3-second intervals
- Explicit timeout for database waiting step

### 3. Frontend Test Memory Issues
**Problem**: Vitest running out of memory
**Solution**:
- Limited thread pool to 1-4 threads
- Isolated test execution
- 10-second timeout per test
- Verbose reporting for better debugging

### 4. Dependency Cache Invalidation
**Problem**: Outdated caches causing inconsistent builds
**Solution**:
- Hash-based cache keys for Poetry and npm
- Separate cache scopes for Docker builds
- Proper fallback cache keys

## Maintenance Guidelines

### 1. Adding New Dependencies
- **Backend**: Add to `pyproject.toml`, run `poetry lock`, update Poetry cache key
- **Frontend**: Add to `package.json`, update `package-lock.json`, npm cache auto-updates

### 2. Modifying Tests
- **Backend**: Respect timeout configurations, use appropriate markers
- **Frontend**: Keep tests under 10 seconds, use threading for parallel execution

### 3. Updating CI Workflows
- Maintain timeout configurations
- Update cache keys when dependencies change
- Test changes in a feature branch first

### 4. Performance Monitoring
- Monitor CI execution times
- Adjust timeouts if needed (but document reasons)
- Review cache hit rates regularly

## Troubleshooting Checklist

### When CI Fails:

1. **Check Timeouts**: Is it a timeout issue or actual failure?
2. **Review Logs**: Look for specific error messages
3. **Check Dependencies**: Are lock files up to date?
4. **Verify Environment**: Are all required variables set?
5. **Database Status**: Is PostgreSQL healthy and ready?
6. **Cache Issues**: Try clearing caches if behavior is inconsistent

### Performance Issues:

1. **Execution Time**: Is CI taking longer than expected?
2. **Resource Usage**: Are we hitting memory or CPU limits?
3. **Parallel Execution**: Are we maximizing parallelization?
4. **Cache Effectiveness**: Are caches being properly utilized?

## Future Improvements

### Planned Enhancements:
1. **Parallel Workflows**: Run backend and frontend CI in parallel
2. **Smart Caching**: Implement more granular cache strategies
3. **Test Parallelization**: Further optimize test execution parallelism
4. **Monitoring**: Add CI performance monitoring and alerting

### Monitoring Metrics:
- CI execution time trends
- Cache hit rates
- Test failure patterns
- Resource utilization

## Emergency Procedures

### CI System Down:
1. Check GitHub Actions status
2. Verify workflow syntax with YAML linter
3. Review recent changes to workflows
4. Fall back to manual testing if needed

### Persistent Failures:
1. Create emergency branch with known-good CI
2. Revert problematic changes
3. Fix issues in separate branch
4. Merge fixes after validation

## Contact and Support

For CI-related issues:
1. Check this documentation first
2. Review recent changes to workflows
3. Consult the troubleshooting checklist
4. Create an issue with detailed logs and reproduction steps

---

**Last Updated**: 2024-11-10  
**Version**: 1.0  
**Maintainer**: ca-pdf Development Team