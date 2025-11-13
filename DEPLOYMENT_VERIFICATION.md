# Deployment Verification Guide

> Comprehensive guide for verifying ca-pdf deployments using automated and manual methods.

## Table of Contents

- [Overview](#overview)
- [Automated Verification](#automated-verification)
- [Manual Verification](#manual-verification)
- [Environment Reset](#environment-reset)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide describes how to verify a ca-pdf deployment to ensure all components are working correctly. The verification process checks:

1. **Container Health**: All Docker containers report `healthy` status
2. **Network Connectivity**: Services can communicate with each other
3. **HTTP Endpoints**: All health check endpoints respond correctly
4. **Database**: PostgreSQL is accessible and migrations applied
5. **Traefik**: Reverse proxy routing and TLS working

---

## Automated Verification

### Quick Start

The fastest way to verify a deployment:

```bash
# Full verification (recommended)
./scripts/verify_deploy.sh

# Using Makefile
make verify-deploy
```

### Installation

The verification script is included in the ca-pdf repository:

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
chmod +x scripts/verify_deploy.sh
./scripts/verify_deploy.sh --help
```

### Command-Line Reference

```
Usage: verify_deploy.sh [OPTIONS]

OPTIONS:
  --force-clean         Automatically clean old data volumes and PostgreSQL data
  --skip-clean          Skip the clean step entirely (test existing deployment)
  --ci-mode             Non-interactive mode, skip prompts, use defaults
  --skip-validation     Skip post-deployment validation (not recommended)
  --timeout SECONDS     Timeout for health checks (default: 600)
  --domain DOMAIN       Domain to use for testing (default: localtest.me)
  --frontend-sub SUB    Frontend subdomain (default: app)
  --backend-sub SUB     Backend subdomain (default: api)
  --no-capdf-install    Use docker compose directly instead of capdf install
  --project-root PATH   Path to ca-pdf project root (default: auto-detect)
  --help                Show this help message
```

### Usage Examples

#### Development Testing

```bash
# Test existing deployment without cleaning
./scripts/verify_deploy.sh --skip-clean

# Full clean deployment test
./scripts/verify_deploy.sh --force-clean

# Quick test with shorter timeout (2 minutes)
./scripts/verify_deploy.sh --skip-clean --timeout 120
```

#### CI/CD Testing

```bash
# Fully automated mode (no prompts)
./scripts/verify_deploy.sh --ci-mode --force-clean

# Using Makefile target
make verify-deploy-ci

# With custom timeout for faster CI
./scripts/verify_deploy.sh --ci-mode --force-clean --timeout 300
```

#### Production Verification

```bash
# Custom domain testing
./scripts/verify_deploy.sh \
  --domain example.com \
  --frontend-sub www \
  --backend-sub api \
  --skip-clean

# Test without redeploying
./scripts/verify_deploy.sh \
  --skip-clean \
  --skip-validation \
  --domain production.example.com
```

### Makefile Targets

Three convenient targets are provided:

```bash
# Standard verification
make verify-deploy

# CI mode (automated, clean environment)
make verify-deploy-ci

# Quick check (skip clean, 2 min timeout)
make verify-deploy-quick
```

### What Gets Verified

#### 1. Container Health Status

The script waits for all containers to report `healthy`:

- **traefik**: Traefik reverse proxy (ping endpoint responding)
- **db**: PostgreSQL database (accepting connections)
- **backend**: FastAPI application (connected to database)
- **frontend**: Nginx web server (serving static files)

#### 2. HTTP Health Endpoints

The script tests these endpoints:

| Service | Endpoint | Expected |
|---------|----------|----------|
| Traefik | `http://localhost:80/ping` | HTTP 200 |
| Backend | `https://api.{domain}/health` | HTTP 200 |
| Frontend | `https://app.{domain}/healthz` | HTTP 200 |

#### 3. Container Dependencies

Verifies proper startup order:

```
db (healthy)
  ↓
backend (healthy, depends on db)
  ↓
frontend (healthy, depends on backend)
  ↓
traefik (routing all services)
```

### Exit Codes

The script exits with specific codes to indicate the failure type:

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success - All checks passed | None |
| 1 | Environment setup failed | Check Docker, files, permissions |
| 2 | Deployment failed | Check logs with `capdf logs` |
| 3 | Container health check failed | Inspect unhealthy containers |
| 4 | Endpoint validation failed | Test endpoints manually |
| 5 | Cleanup failed | Check Docker state |

### Interpreting Output

#### Success Example

```
==> Starting deployment verification
ℹ Project root: /home/user/ca-pdf
ℹ Domain: localtest.me
ℹ Frontend: https://app.localtest.me
ℹ Backend: https://api.localtest.me

==> Cleaning existing deployment
ℹ Stopping Docker containers...
✔ Cleanup completed

==> Deploying with capdf install
ℹ Running: capdf install --force-clean
✔ Deployment completed

==> Waiting for all containers to be healthy
ℹ Waiting for traefik to be healthy (timeout: 600s)...
✔ traefik: Healthy
ℹ Waiting for db to be healthy (timeout: 600s)...
✔ db: Healthy
ℹ Waiting for backend to be healthy (timeout: 600s)...
✔ backend: Healthy
ℹ Waiting for frontend to be healthy (timeout: 600s)...
✔ frontend: Healthy
✔ All containers are healthy

==> Validating health endpoints
ℹ Testing Traefik /ping: http://localhost:80/ping
✔ Traefik /ping: HTTP 200 OK
ℹ Testing Backend /health: https://api.localtest.me/health
✔ Backend /health: HTTP 200 OK
ℹ Testing Frontend /healthz: https://app.localtest.me/healthz
✔ Frontend /healthz: HTTP 200 OK
✔ All endpoint validations passed

==> Deployment Status Summary

Services:
NAME                IMAGE               STATUS       HEALTH
ca_pdf-traefik-1   traefik:v3.1        Up 2 minutes healthy
ca_pdf-db-1        postgres:16         Up 2 minutes healthy
ca_pdf-backend-1   ca_pdf-backend      Up 1 minute  healthy
ca_pdf-frontend-1  ca_pdf-frontend     Up 1 minute  healthy

Endpoints:
  Frontend:  https://app.localtest.me
  Backend:   https://api.localtest.me
  API Docs:  https://api.localtest.me/docs
  Traefik:   http://localhost:80/ping

✔ Deployment verification completed successfully!

ℹ Next steps:
  1. Open browser: https://app.localtest.me
  2. Check API docs: https://api.localtest.me/docs
  3. View logs: capdf logs
```

#### Failure Example

```
==> Waiting for all containers to be healthy
ℹ Waiting for backend to be healthy (timeout: 600s)...
⚠ backend: Container not found yet (5s elapsed)
⚠ backend: Starting... (30s elapsed)
⚠ backend: Starting... (60s elapsed)
✖ backend: Unhealthy
✖ Failed to wait for backend
✖ Container health check failed

Services:
NAME                STATUS      HEALTH
ca_pdf-backend-1   Up 1 minute unhealthy

Exit code: 3

To debug:
  docker compose logs backend
  capdf doctor
  capdf export-logs
```

---

## Manual Verification

If the automated script fails or you need detailed verification, follow these manual steps.

### 1. Check Container Status

```bash
# Using capdf command
capdf status

# Or docker compose directly
cd /path/to/ca-pdf
docker compose ps
```

Expected output: All containers should be `Up` and `healthy`:

```
NAME                IMAGE               STATUS       HEALTH
ca_pdf-traefik-1   traefik:v3.1        Up 5 minutes healthy
ca_pdf-db-1        postgres:16         Up 5 minutes healthy
ca_pdf-backend-1   ca_pdf-backend      Up 4 minutes healthy
ca_pdf-frontend-1  ca_pdf-frontend     Up 4 minutes healthy
```

### 2. Test Health Endpoints

#### Traefik Ping

```bash
curl http://localhost:80/ping
# Expected: "OK"
```

#### Backend Health

```bash
# Local testing (self-signed cert)
curl -k https://api.localtest.me/health

# Production
curl https://api.yourdomain.com/health

# Expected: {"status":"ok","service":"ca-pdf"}
```

#### Frontend Health

```bash
# Local testing
curl -k https://app.localtest.me/healthz

# Production
curl https://app.yourdomain.com/healthz

# Expected: "ok"
```

### 3. Run System Diagnostics

```bash
capdf doctor
```

This comprehensive diagnostic checks:
- Operating system information
- Docker environment
- System resources (CPU, RAM, disk)
- Network connectivity
- Port availability
- Configuration file syntax
- Project structure
- Container health
- Database connection
- Backend API

### 4. Check Container Logs

```bash
# View all logs
capdf logs

# View specific service
capdf logs backend
capdf logs frontend
capdf logs db
capdf logs traefik

# Follow logs in real-time
capdf logs -f backend

# Show last 50 lines
capdf logs backend | tail -50
```

### 5. Verify Database Connection

```bash
# Check database logs
capdf logs db | tail -20

# Should see: "database system is ready to accept connections"

# Test connection from backend
docker compose exec backend python -c "
from app.db.session import engine
with engine.connect() as conn:
    print('Database connection successful')
"
```

### 6. Test API Endpoints

```bash
# API documentation
curl -k https://api.localtest.me/docs
# Should return Swagger UI HTML

# Health check (detailed)
curl -k https://api.localtest.me/health | jq
# Expected:
# {
#   "status": "ok",
#   "service": "ca-pdf"
# }
```

### 7. Browser Testing

Open browser and test:

1. **Frontend**: https://app.localtest.me (or your domain)
   - Login page should display
   - No console errors

2. **API Docs**: https://api.localtest.me/docs
   - Swagger UI should load
   - Can expand and test endpoints

3. **Certificate Warning** (local testing only):
   - Click "Advanced" → "Continue to site"
   - This is expected for self-signed certificates

---

## Environment Reset

### When to Reset

Reset the environment when:
- Testing clean deployment
- Troubleshooting persistent issues
- Switching between configurations
- Database corruption
- Starting fresh after failed deployment

### Method 1: Automated Reset

```bash
# Using verification script
./scripts/verify_deploy.sh --force-clean

# CI mode
./scripts/verify_deploy.sh --ci-mode --force-clean
```

### Method 2: Using capdf Commands

```bash
# Stop all containers and remove volumes
capdf down -v

# Remove PostgreSQL data directory
sudo rm -rf /opt/ca-pdf/data/postgres/

# Reinstall with clean environment
capdf install --force-clean
```

### Method 3: Manual Docker Commands

```bash
cd /path/to/ca-pdf

# Stop and remove everything
docker compose down -v --remove-orphans

# Remove data directories
rm -rf ./data/postgres/
sudo rm -rf /opt/ca-pdf/data/postgres/  # If installed via install.sh

# Clean Docker volumes
docker volume ls | grep 'ca_pdf\|ca-pdf' | awk '{print $2}' | xargs -r docker volume rm

# Remove old images
docker compose down --rmi all

# Clean build cache
docker builder prune -f

# Rebuild and start
docker compose up -d --build --force-recreate
```

### Reset Verification Checklist

After reset, verify:

- [ ] No ca-pdf containers running: `docker compose ps -a`
- [ ] No ca-pdf volumes exist: `docker volume ls | grep ca`
- [ ] PostgreSQL data removed: `ls /opt/ca-pdf/data/postgres/`
- [ ] Ports available: `ss -tlnp | grep -E ':(80|443|5432)'`
- [ ] Clean Docker state: `docker compose config` validates

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deployment Verification

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  verify-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker
        uses: docker/setup-buildx-action@v2
      
      - name: Run deployment verification
        run: |
          chmod +x scripts/verify_deploy.sh
          ./scripts/verify_deploy.sh --ci-mode --force-clean --timeout 300
      
      - name: Export logs on failure
        if: failure()
        run: |
          docker compose logs > deployment-logs.txt
          docker compose ps -a > container-status.txt
      
      - name: Upload logs
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: deployment-logs
          path: |
            deployment-logs.txt
            container-status.txt
```

### GitLab CI Example

```yaml
verify-deploy:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  script:
    - apk add --no-cache bash curl
    - chmod +x scripts/verify_deploy.sh
    - ./scripts/verify_deploy.sh --ci-mode --force-clean --timeout 300
  artifacts:
    when: on_failure
    paths:
      - deployment-logs.txt
    expire_in: 7 days
  timeout: 20 minutes
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Verify Deployment') {
            steps {
                sh '''
                    chmod +x scripts/verify_deploy.sh
                    ./scripts/verify_deploy.sh --ci-mode --force-clean --timeout 300
                '''
            }
        }
    }
    
    post {
        failure {
            sh 'docker compose logs > deployment-logs.txt'
            archiveArtifacts artifacts: 'deployment-logs.txt', fingerprint: true
        }
        cleanup {
            sh 'docker compose down -v || true'
        }
    }
}
```

---

## Troubleshooting

### Container Health Check Failures

#### Symptom: Container stuck in "starting" state

```bash
# Check container logs
docker compose logs [service]

# Inspect health check status
docker inspect [container-id] | jq '.[0].State.Health'

# Common causes:
# - Database not ready (backend)
# - Backend not ready (frontend)
# - Port conflicts
# - Resource constraints
```

#### Symptom: Container immediately unhealthy

```bash
# Check health check command
docker compose config | grep -A 5 healthcheck

# Test health check manually
docker compose exec [service] [health-check-command]

# Examples:
docker compose exec backend curl -f http://127.0.0.1:8000/health
docker compose exec frontend wget --spider -q http://127.0.0.1:8080/healthz
docker compose exec db pg_isready -U app_user -d app_db
```

### Endpoint Validation Failures

#### Symptom: Traefik ping fails

```bash
# Check Traefik status
docker compose ps traefik

# Test ping directly
curl http://localhost:80/ping

# Check Traefik logs
docker compose logs traefik | grep -i error

# Verify Traefik configuration
docker compose exec traefik cat /etc/traefik/dynamic/dynamic.yml
```

#### Symptom: Backend health endpoint fails

```bash
# Test backend directly (bypass Traefik)
curl http://localhost:8000/health

# Check backend logs
docker compose logs backend | tail -50

# Verify database connection
docker compose logs backend | grep -i database

# Check environment variables
docker compose exec backend env | grep -E "DATABASE|SECRET"
```

#### Symptom: Frontend health endpoint fails

```bash
# Test frontend directly
curl http://localhost:8080/healthz

# Check Nginx configuration
docker compose exec frontend cat /etc/nginx/nginx.conf | grep healthz

# Check frontend logs
docker compose logs frontend | tail -50

# Verify backend connectivity from frontend
docker compose exec frontend wget -O- http://backend:8000/health
```

### Timeout Errors

If health checks timeout:

1. **Increase timeout**:
   ```bash
   ./scripts/verify_deploy.sh --timeout 900  # 15 minutes
   ```

2. **Check system resources**:
   ```bash
   free -h  # Memory
   df -h    # Disk space
   top      # CPU usage
   ```

3. **Check Docker performance**:
   ```bash
   docker stats  # Real-time resource usage
   docker system df  # Disk usage
   ```

### Network Issues

#### Local testing (localtest.me)

```bash
# Test DNS resolution
nslookup app.localtest.me
# Should resolve to 127.0.0.1

# Test with different DNS
nslookup app.localtest.me 8.8.8.8

# Add to /etc/hosts if needed
echo "127.0.0.1 app.localtest.me api.localtest.me" | sudo tee -a /etc/hosts
```

#### Production (custom domain)

```bash
# Verify DNS records
nslookup app.yourdomain.com
nslookup api.yourdomain.com

# Test from external network
curl https://app.yourdomain.com/healthz

# Check Let's Encrypt certificates
docker compose logs traefik | grep -i acme
```

### Getting Help

If you're still having issues:

1. **Run diagnostics**:
   ```bash
   capdf doctor
   ```

2. **Export logs**:
   ```bash
   capdf export-logs
   # Creates tarball in backups/ directory
   ```

3. **Open an issue**:
   - Go to: https://github.com/QAQ-AWA/ca-pdf/issues
   - Include:
     - Output from `capdf doctor`
     - Exported logs
     - Error messages
     - Steps to reproduce

4. **Contact support**:
   - Email: 7780102@qq.com
   - Subject: [ca-pdf] Deployment Verification Issue
   - Attach logs and diagnostic output

---

## Best Practices

### Development

- Use `--skip-clean` for faster iteration
- Keep data between tests unless debugging data issues
- Use shorter timeouts (`--timeout 120`) for quick feedback
- Test both clean and dirty deployments

### CI/CD

- Always use `--ci-mode` for non-interactive execution
- Always use `--force-clean` for reproducible tests
- Set appropriate timeouts (300-600s typical)
- Cache Docker layers when possible
- Upload logs on failure

### Production

- Use `--skip-clean` to avoid data loss
- Test with actual production domain
- Verify SSL certificates separately
- Run during maintenance windows
- Have rollback plan ready

### Monitoring

After successful deployment:

```bash
# Set up log monitoring
capdf logs -f | grep -E "ERROR|WARN"

# Monitor container health
watch -n 5 'docker compose ps'

# Monitor resource usage
docker stats

# Set up alerts
# - Container health changes
# - High resource usage
# - Failed requests
# - Database connection issues
```

---

## Related Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Detailed checklist
- [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) - Manual verification steps
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Comprehensive troubleshooting
- [README.md](README.md) - Project overview

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Applicable to**: ca-pdf v0.1.0+
