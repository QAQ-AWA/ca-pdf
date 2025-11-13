# Traefik Routing Fix - Test Plan

## Overview
This document outlines the testing strategy for the Traefik routing configuration fix.

## Pre-Testing Validation

### 1. Syntax Validation
```bash
# Check bash script syntax
bash -n scripts/deploy.sh
# Expected: No output (syntax OK)

# Check YAML syntax
cat config/traefik/dynamic.yml | grep -E "^[a-z]"
# Expected: http, services, middlewares, tls sections visible
```

### 2. Docker Compose Validation
```bash
# Validate compose file (may have env warnings, that's OK)
docker compose config >/dev/null 2>&1
echo $?
# Expected: 0 (success)
```

## Test Scenarios

### Scenario 1: Local Development Mode

#### Prerequisites
- Clean environment (no existing containers)
- Docker and Docker Compose installed
- Ports 80, 443, 5432 available

#### Test Steps
```bash
# 1. Clone/update repository
cd /home/engine/project

# 2. Run deployment script in local mode
./scripts/deploy.sh install \
  --mode local \
  --domain localtest.me \
  --admin-email admin@example.com \
  --admin-password admin123

# 3. Wait for services to start (2-3 minutes)
watch docker compose ps

# 4. Verify Traefik health
docker compose ps traefik
# Expected: Status shows "Up X seconds (healthy)"

# 5. Check dynamic config was generated
cat config/traefik/dynamic.yml
# Expected: File contains routers, services, middlewares, tls sections

# 6. Check self-signed certificate was created
ls -l config/traefik/certs/
# Expected: selfsigned.crt and selfsigned.key exist

# 7. Check Traefik logs for errors
docker compose logs traefik | grep -i error
# Expected: No critical errors

# 8. Test backend health endpoint
curl -k https://api.localtest.me/health
# Expected: {"status":"ok","service":"ca-pdf"}

# 9. Test frontend access
curl -k https://app.localtest.me/ | head -20
# Expected: HTML content (<!DOCTYPE html>...)

# 10. Test HTTPS redirect
curl -I http://api.localtest.me/health
# Expected: HTTP 301 or 302 with Location: https://api.localtest.me/health

# 11. Test HTTPS redirect for frontend
curl -I http://app.localtest.me/
# Expected: HTTP 301 or 302 with Location: https://app.localtest.me/
```

#### Expected Results
✅ Traefik container: healthy
✅ Backend routing: Working (returns JSON)
✅ Frontend routing: Working (returns HTML)
✅ HTTPS redirect: Working (301/302)
✅ Self-signed cert: Created
✅ No critical errors in logs

### Scenario 2: Production Mode (Dry Run)

#### Prerequisites
- Access to a domain with DNS configured
- Let's Encrypt rate limits considered (use staging)

#### Test Steps
```bash
# 1. Run deployment in production mode (staging ACME)
./scripts/deploy.sh install \
  --mode production \
  --domain example.com \
  --acme-email admin@example.com \
  --admin-email admin@example.com \
  --admin-password SecurePassword123

# 2. Verify dynamic config uses certResolver
cat config/traefik/dynamic.yml | grep certResolver
# Expected: certResolver: le

# 3. Check Traefik ACME logs
docker compose logs traefik | grep -i acme
# Expected: ACME certificate requests (may fail if DNS not configured)

# 4. Verify no self-signed certs in production mode
ls config/traefik/certs/ 2>&1
# Expected: Empty directory or doesn't exist

# 5. Check Traefik router configuration
docker compose exec traefik cat /etc/traefik/dynamic/dynamic.yml | head -50
# Expected: Routers with certResolver: le
```

#### Expected Results
✅ Dynamic config uses Let's Encrypt resolver
✅ No self-signed certificates generated
✅ ACME challenge initiated (if DNS configured)
✅ Routers properly configured

### Scenario 3: Configuration Regeneration

#### Test Steps
```bash
# 1. Make a backup of existing dynamic.yml
cp config/traefik/dynamic.yml config/traefik/dynamic.yml.bak

# 2. Modify domains and regenerate
./scripts/deploy.sh install \
  --mode local \
  --domain newdomain.localtest.me \
  --admin-email admin@example.com \
  --admin-password admin123

# 3. Verify configuration was updated
grep "newdomain.localtest.me" config/traefik/dynamic.yml
# Expected: Multiple matches (in router rules)

# 4. Verify old domains are gone
grep "api.localtest.me" config/traefik/dynamic.yml
# Expected: Should show new domain instead
```

#### Expected Results
✅ Configuration regenerated successfully
✅ New domains reflected in dynamic.yml
✅ Services restarted with new configuration

### Scenario 4: Traefik Health Check

#### Test Steps
```bash
# 1. Check Traefik ping endpoint
docker compose exec traefik traefik healthcheck --ping
# Expected: Exit code 0 (healthy)

# 2. Check Traefik dashboard (if enabled)
curl http://localhost:8080/dashboard/
# Expected: HTML or redirect (dashboard may be disabled by default)

# 3. Verify file provider loaded
docker compose logs traefik | grep "file"
# Expected: Lines showing file provider initialized

# 4. Check for configuration errors
docker compose logs traefik | grep -i "error\|fail" | grep -v "level=info"
# Expected: No critical errors
```

#### Expected Results
✅ Ping endpoint working
✅ File provider loaded
✅ No configuration errors
✅ Traefik reports healthy

### Scenario 5: Service Health Checks

#### Test Steps
```bash
# 1. Monitor backend health check
docker compose logs traefik | grep "backend.*health" | tail -5
# Expected: Health check requests to backend

# 2. Monitor frontend health check
docker compose logs traefik | grep "frontend.*health\|frontend.*/" | tail -5
# Expected: Health check requests to frontend

# 3. Verify backend responds to health checks
docker compose exec backend curl http://localhost:8000/health
# Expected: {"status":"ok","service":"ca-pdf"}

# 4. Check service health status
docker compose ps | grep -E "backend|frontend"
# Expected: Both showing healthy status
```

#### Expected Results
✅ Traefik performs health checks
✅ Backend health endpoint responds
✅ Frontend health endpoint responds
✅ Services report healthy

## Negative Test Cases

### Test 1: Missing Configuration File
```bash
# 1. Remove dynamic.yml
mv config/traefik/dynamic.yml config/traefik/dynamic.yml.tmp

# 2. Restart Traefik
docker compose restart traefik

# 3. Check Traefik status
docker compose ps traefik
# Expected: Should start but log warnings about missing config

# 4. Restore configuration
mv config/traefik/dynamic.yml.tmp config/traefik/dynamic.yml
docker compose restart traefik
```

### Test 2: Invalid YAML Syntax
```bash
# 1. Backup valid config
cp config/traefik/dynamic.yml config/traefik/dynamic.yml.bak

# 2. Add invalid YAML
echo "invalid: : : syntax" >> config/traefik/dynamic.yml

# 3. Restart Traefik
docker compose restart traefik

# 4. Check logs for errors
docker compose logs traefik | grep -i "error\|fail" | tail -10
# Expected: YAML parsing errors

# 5. Restore valid config
mv config/traefik/dynamic.yml.bak config/traefik/dynamic.yml
docker compose restart traefik
```

### Test 3: Wrong Service URLs
```bash
# 1. Modify service URL to invalid port
sed -i 's/backend:8000/backend:9999/g' config/traefik/dynamic.yml

# 2. Restart Traefik
docker compose restart traefik

# 3. Test backend access
curl -k https://api.localtest.me/health
# Expected: 502 Bad Gateway or timeout

# 4. Restore correct config
./scripts/deploy.sh install --mode local --domain localtest.me
```

## Performance Tests

### Test 1: Response Time
```bash
# Measure backend response time
time curl -k https://api.localtest.me/health
# Expected: < 1 second

# Measure frontend response time
time curl -k https://app.localtest.me/
# Expected: < 2 seconds
```

### Test 2: Concurrent Requests
```bash
# Test with multiple concurrent requests
seq 10 | xargs -P 10 -I {} curl -s -k https://api.localtest.me/health
# Expected: All requests succeed
```

## Rollback Test

### Test Steps
```bash
# 1. Note current working state
docker compose ps > current_state.txt

# 2. Simulate rollback
git checkout HEAD~1 docker-compose.yml scripts/deploy.sh
rm -rf config/traefik

# 3. Deploy with old configuration
docker compose down
docker compose up -d

# 4. Verify services still work (with old configuration)
# Expected: Services work but may use Docker labels for routing

# 5. Roll forward to new configuration
git checkout - docker-compose.yml scripts/deploy.sh
git restore config/traefik

# 6. Redeploy
./scripts/deploy.sh install --mode local --domain localtest.me
```

## Acceptance Criteria Checklist

- [ ] ✅ Traefik container status is "healthy"
- [ ] ✅ Backend API accessible via HTTPS (https://api.domain.com/health)
- [ ] ✅ Frontend accessible via HTTPS (https://app.domain.com/)
- [ ] ✅ HTTP to HTTPS redirect works (301/302 response)
- [ ] ✅ Configuration generated correctly on each install
- [ ] ✅ Routers defined in dynamic.yml (backend-web, backend, frontend-web, frontend)
- [ ] ✅ Services defined in dynamic.yml (backend, frontend)
- [ ] ✅ Health checks configured (backend: /health, frontend: /)
- [ ] ✅ No errors in Traefik logs
- [ ] ✅ TLS configuration works (Let's Encrypt for prod, self-signed for local)

## Success Metrics

1. **Traefik Health**: Container should be "healthy" status
2. **Response Time**: < 1s for backend, < 2s for frontend
3. **Uptime**: No container restarts during testing
4. **Error Rate**: 0 configuration errors in logs
5. **Redirect Rate**: 100% of HTTP requests redirect to HTTPS

## Test Environment

### Required
- Docker: 20.10+
- Docker Compose: 2.0+
- OS: Ubuntu 22.04 / Debian 11 / similar
- RAM: 2GB minimum
- Disk: 5GB free space

### Optional
- curl: For API testing
- jq: For JSON parsing
- watch: For monitoring

## Troubleshooting Guide

### Issue: Traefik unhealthy
**Solution**: Check logs `docker compose logs traefik | tail -50`

### Issue: 404 Not Found
**Solution**: Verify dynamic.yml routers and restart Traefik

### Issue: 502 Bad Gateway
**Solution**: Check backend/frontend service health and URLs

### Issue: Certificate errors
**Solution**: Accept self-signed cert with `-k` flag in curl, or configure Let's Encrypt for production

### Issue: HTTPS redirect not working
**Solution**: Verify middleware in dynamic.yml and router configuration

## Test Report Template

```
Date: YYYY-MM-DD
Tester: [Name]
Environment: [Local/Production]
Docker Version: [version]
Docker Compose Version: [version]

Test Results:
- Scenario 1 (Local Mode): PASS/FAIL
- Scenario 2 (Production Mode): PASS/FAIL
- Scenario 3 (Regeneration): PASS/FAIL
- Scenario 4 (Health Check): PASS/FAIL
- Scenario 5 (Service Health): PASS/FAIL

Acceptance Criteria: [X/10 passed]

Issues Found:
1. [Issue description]
2. [Issue description]

Notes:
[Additional observations]
```

---

**Last Updated**: 2024-11-13
**Version**: 1.0
**Status**: Ready for Testing
