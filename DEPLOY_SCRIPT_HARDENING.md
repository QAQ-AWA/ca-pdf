# Deploy Script Hardening - Feature Documentation

This document describes the hardening improvements made to `scripts/deploy.sh` to ensure valid asset generation and robust deployment validation.

## Overview

The deployment script has been enhanced with:
1. **Network Configuration Validation** - Ensures proper network definitions and attachments
2. **Health Check Configuration** - Comprehensive health checks for all services
3. **No-Rollback Mode** - Optional debugging mode that preserves failed deployments
4. **Improved Configuration Generation** - Smart YAML generation that handles empty configurations

## Features

### 1. Network Configuration Validation

**Function**: `validate_network_configuration()`

Before deployment starts, the script validates that the generated `docker-compose.yml` file has proper network configuration:

#### What is validated:
- **Network Definitions**: Both `edge` and `internal` networks are defined with bridge drivers
- **Service Attachments**: Critical services (backend, frontend, db, traefik) are properly attached to networks
- **Docker Compose Syntax**: File passes `docker compose config` validation

#### Example Output:
```
==> 验证生成的配置文件
ℹ 验证网络配置...
ℹ 检查网络定义...
✔ 找到 'edge' 网络
✔ 找到 'internal' 网络
ℹ 检查服务网络附件...
✔ 服务网络配置正确（4/4）
```

#### Error Handling:
If validation fails, the deployment aborts with detailed error messages:
```
✖ docker-compose.yml 语法验证失败
✖ 未找到 'edge' 网络定义
```

### 2. Health Check Configuration

The deployment script ensures comprehensive health checks at both container and load balancer levels:

#### Docker Container Health Checks (in docker-compose.yml):
- **Backend**: HTTP health endpoint at `/health` (30s interval, 10s timeout)
- **Frontend**: HTTP health endpoint at `/healthz` (30s interval, 10s timeout)
- **Database**: PostgreSQL readiness probe (10s interval, 5s timeout)
- **Traefik**: Built-in traefik healthcheck command (30s interval, 5s timeout)

#### Traefik Load Balancer Health Checks (in dynamic.yml):
- **Backend service**: `/health` endpoint (30s interval, 10s timeout)
- **Frontend service**: `/healthz` endpoint (30s interval, 10s timeout)

#### Traefik Ping Endpoint:
The Traefik `/ping` endpoint is automatically enabled for health monitoring:
```bash
--ping=true
--ping.entrypoint=web
```

### 3. Smart Label Generation

**What changed**: Backend and frontend Docker labels are only included in `docker-compose.yml` when they are non-empty.

#### Before:
```yaml
backend:
  # ... other config ...
  labels:      # Empty labels section - causes validation issues
```

#### After:
```yaml
backend:
  # ... other config ...
  # labels section omitted when empty - cleaner, valid YAML
```

**Benefit**: Generated YAML files always pass `docker compose config` validation, even when labels are not used.

### 4. No-Rollback Flag for Debugging

**Flag**: `--no-rollback`

Allows operators to disable automatic rollback on deployment failure, preserving the failed state for debugging.

#### When to use:
- Debugging deployment issues
- Investigating service startup problems
- Analyzing failed migrations
- Examining partially built containers

#### Usage:
```bash
capdf install --no-rollback
```

#### Behavior with --no-rollback:
- If deployment fails, containers remain running
- Logs are preserved for analysis
- Manual cleanup required: `capdf down --clean`

#### Behavior without --no-rollback (default):
- Automatic `docker compose down --remove-orphans` on failure
- Dangling images cleaned up automatically
- Clean slate for retry

#### Example Output:
```
✖ 部署失败（第 1060 行，退出码 1）。
⚠ 检测到 --no-rollback 标志，已禁用自动回滚（便于调试）。
⚠ 可手动运行 'capdf down --clean' 清理资源。
✖ 请查看日志文件获取详情：...
```

## Configuration Files Generated

### 1. docker-compose.yml
- Defines all services (traefik, db, backend, frontend)
- Configures networks (edge for public, internal for private)
- Health check configuration per service
- Volume definitions
- Optional labels (only when non-empty)

### 2. config/traefik/dynamic.yml
- File-based routing configuration (not Docker labels)
- Traefik routers for HTTP and HTTPS
- Load balancer health checks
- Service definitions
- TLS configuration (self-signed for local, Let's Encrypt for production)
- HTTPS redirect middleware

### 3. .env
- Application-specific environment variables
- Database configuration
- Security keys and tokens
- CORS origins

### 4. .env.docker
- Docker Compose environment variables
- Domain configuration
- Traefik settings

## Validation Flow

```
capdf install [--no-rollback] [other options]
  ├─ Environment Pre-checks (OS, Docker, Ports, Resources)
  ├─ Interactive Configuration (Domain, Email, Database)
  ├─ Data Cleanup (if requested)
  ├─ Generate Configuration Files
  │  ├─ .env
  │  ├─ .env.docker
  │  ├─ docker-compose.yml
  │  └─ config/traefik/dynamic.yml
  ├─ Network Configuration Validation ← NEW
  │  ├─ Verify edge network exists
  │  ├─ Verify internal network exists
  │  ├─ Check service network attachments
  │  └─ Validate docker-compose syntax
  ├─ Docker Compose Up
  ├─ Wait for Services
  ├─ Database Migrations
  ├─ Deployment Validation
  └─ On Failure:
     ├─ If --no-rollback: Preserve containers for debugging
     └─ Otherwise: Automatic rollback and cleanup
```

## Testing

Unit tests are included in `scripts/test_deploy.sh`:

```bash
# Run tests
bash scripts/test_deploy.sh

# Test coverage:
# - Basic docker-compose.yml generation
# - Network definition and service attachments
# - Traefik configuration (local and production modes)
# - Empty labels handling
# - Traefik ping endpoint enablement
# - Docker container health checks
```

### Running Tests
```bash
cd /home/engine/project
scripts/test_deploy.sh
```

### Test Output Example
```
========== 开始执行 deploy.sh 测试套件 ==========

[TEST] 测试基本 docker-compose.yml 生成
✓ compose 文件已生成
✓ networks 部分已包含
✓ edge 网络已定义
✓ backend 服务已附加到网络

[TEST] 测试 Traefik 本地模式配置生成
✓ 后端健康检查路径正确 (/health)
✓ 健康检查间隔正确 (30s)
✓ 本地模式 TLS 配置正确

========== 测试总结 ==========
通过: 26
失败: 0
✓ 所有测试通过！
```

## Usage Examples

### Standard Installation with Validation
```bash
capdf install
```
- Validates network configuration before startup
- Automatic rollback on failure

### Debug Mode Installation
```bash
capdf install --no-rollback
```
- Failed deployment preserves containers for debugging
- Manual cleanup: `capdf down --clean`

### Complete Reinstallation
```bash
capdf install --force-clean --no-cache
```
- Removes old data volumes and PostgreSQL data
- Rebuilds images without cache
- Standard validation and rollback

### Forced Deployment (bypass rollback)
```bash
capdf install --force-clean --no-rollback
```
- Clean slate
- No automatic rollback on failure
- Useful for CI/CD debugging

## Troubleshooting

### Network Validation Failures

**Error**: "docker-compose.yml 语法验证失败"
- **Cause**: Generated YAML has syntax errors
- **Solution**: Check `.env` and `.env.docker` files for invalid characters or unclosed quotes

**Error**: "未找到 'edge' 网络定义"
- **Cause**: Network definition missing in compose file
- **Solution**: Regenerate compose file: `rm docker-compose.yml && capdf install`

### Health Check Issues

**Container keeps restarting**:
- Check health check configuration in `docker-compose.yml`
- Verify service is actually running: `capdf logs backend`
- Increase `start_period` if startup is slow

**Load balancer cannot reach service**:
- Verify network attachments: `docker network inspect ca_pdf_internal`
- Check service logs: `capdf logs frontend`
- Verify health check endpoint is responding

### Debugging Failed Deployments

With `--no-rollback`:
```bash
# Check container logs
capdf logs backend
capdf logs frontend
capdf logs db

# Inspect running containers
docker ps

# Check network configuration
docker network ls
docker network inspect ca_pdf_edge
docker network inspect ca_pdf_internal

# Clean up manually
capdf down --clean
```

## File Structure After Installation

```
/opt/ca-pdf (or custom path)
├── docker-compose.yml          (generated)
├── .env                        (generated, contains secrets)
├── .env.docker                 (generated)
├── .env.example                (reference)
├── .env.docker.example         (reference)
├── config/
│   └── traefik/
│       ├── dynamic.yml         (generated, routing config)
│       ├── certs/
│       │   ├── selfsigned.crt  (local mode only)
│       │   └── selfsigned.key  (local mode only)
├── backend/                    (project source)
├── frontend/                   (project source)
├── scripts/
│   ├── deploy.sh               (deployment script)
│   └── install.sh              (installation script)
└── data/
    └── postgres/               (database data, created at first run)
```

## Environment Variables

### New Variables (for debugging)
- `NO_ROLLBACK=1` - Can be set instead of flag, but flag takes precedence

### Important Existing Variables
- `COMPOSE_PROJECT_NAME=ca_pdf` - Project name for Docker Compose
- `DOCKER_BUILDKIT=1` - Enable Docker buildkit for faster builds
- `COMPOSE_DOCKER_CLI_BUILD=1` - Use Docker CLI for building

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete deployment guide
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Development environment setup
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Troubleshooting guide

## Implementation Details

### Code Changes Summary

1. **New Global Variable**:
   - `NO_ROLLBACK=0` - Controls rollback behavior

2. **Enhanced `on_error()` Function**:
   - Checks `NO_ROLLBACK` flag
   - Preserves containers when flag is set
   - Provides helpful guidance for manual cleanup

3. **New Function `validate_network_configuration()`**:
   - Uses `docker compose config` for validation
   - Verifies network definitions
   - Checks service network attachments
   - Returns meaningful error messages

4. **Updated `start_stack()` Function**:
   - Calls network validation before deployment
   - Aborts on validation failure

5. **Enhanced Help Text**:
   - Documents --no-rollback flag
   - Includes new deployment flow step

6. **Test Suite `scripts/test_deploy.sh`**:
   - Comprehensive fixture tests
   - Validates generated YAML
   - Tests all health check configurations
   - Tests network attachment logic

## Backward Compatibility

All changes are backward compatible:
- Existing installations continue to work
- Default behavior (with rollback) unchanged
- New flag is optional
- Generated configs produce valid YAML

## Performance Impact

Minimal performance impact:
- Network validation adds ~100-200ms
- Uses `docker compose config` (efficient YAML parsing)
- Only runs before Docker Compose up
- Does not affect runtime performance

## Security Considerations

- Generated compose files never expose secrets
- Health check endpoints are internal only
- Network isolation maintained (edge/internal)
- TLS configuration varies by environment (self-signed/Let's Encrypt)
- --no-rollback does not disable other security measures
