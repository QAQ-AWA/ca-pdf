# Troubleshooting Guide

> **Status**: Common issues and solutions
> **Target Audience**: All users
> **Last Updated**: 2024

This guide provides solutions to common problems and frequently asked questions about ca-pdf.

## Getting Help

Before troubleshooting, consider these resources:

1. **Check Logs**: Review application logs for error messages
2. **Search Documentation**: Look for similar issues in relevant guides
3. **Check GitHub Issues**: Search existing issue reports
4. **Contact Support**: Email [7780102@qq.com](mailto:7780102@qq.com)

## Authentication Issues

### Cannot Log In

**Symptoms**: Login page appears to hang or shows "Invalid credentials"

**Solutions**:

1. **Verify credentials**
   - Check username is correct (case-sensitive)
   - Verify CAPS LOCK is off
   - Check password for typos

2. **Reset password**
   - Click "Forgot Password" link
   - Enter your email address
   - Follow instructions in reset email

3. **Check server**
   - Verify backend is running: `docker-compose ps`
   - Check backend logs: `docker-compose logs backend`

4. **Clear browser cache**
   - Chrome: Ctrl+Shift+Delete → Clear browsing data
   - Firefox: Ctrl+Shift+Delete → Everything
   - Safari: Cmd+Shift+Delete (or use settings)

### Session Expires Too Quickly

**Symptoms**: You're logged out unexpectedly

**Causes**:
- JWT token expiration timeout
- Browser cache issues
- Session fixation

**Solutions**:

1. **Check JWT expiration**
   - See `JWT_EXPIRE_MINUTES` in deployment guide
   - Adjust if needed via environment variable

2. **Clear browser cache**
   - Log out completely
   - Close browser
   - Clear all browser data
   - Log in again

3. **Check browser settings**
   - Ensure cookies are enabled
   - Check LocalStorage is enabled
   - Disable any privacy extensions

### API Token Errors

**Symptoms**: API calls return "Unauthorized" (401)

**Solutions**:

1. **Verify token in header**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/v1/ca/certificates
   ```

2. **Refresh token**
   - Log out and log back in
   - Request a new token

3. **Check token expiration**
   - Decode JWT token on [jwt.io](https://jwt.io)
   - Verify `exp` claim

## Certificate Issues

### Cannot Create Certificate

**Symptoms**: Certificate creation fails with error

**Common Causes**:
- Invalid certificate parameters
- Insufficient permissions
- Storage space issues

**Solutions**:

1. **Verify parameters**
   - Common Name (CN) should be a valid identifier
   - Email should be in valid format
   - Organization name should not be empty if required

2. **Check permissions**
   - Log in as administrator or appropriate user
   - Verify user role has certificate creation rights

3. **Check storage**
   - Ensure database has space: `df -h`
   - Check for disk space errors in logs

### Certificate Expired or Invalid

**Symptoms**: Signatures fail, certificate shows as invalid

**Solutions**:

1. **Check certificate validity**
   - Log in to dashboard
   - Go to Certificates
   - Check "Valid To" date
   - Request new certificate if expired

2. **Verify certificate chain**
   - Ensure root CA certificate is trusted
   - Check intermediate certificates are included
   - Verify all certificates in chain are valid

3. **Re-request certificate**
   - If business certificate expired, request new one
   - Wait for administrator approval
   - Use new certificate for signing

## PDF Signing Issues

### Document Upload Fails

**Symptoms**: Upload shows error or progress bar gets stuck

**Solutions**:

1. **Check file format**
   ```bash
   # Verify it's a valid PDF
   file document.pdf
   ```

2. **Check file size**
   - Default limit is 50 MB
   - Split large files or increase limit in config

3. **Check network connection**
   - Ensure stable internet connection
   - Try uploading smaller file first
   - Check firewall isn't blocking uploads

4. **Clear browser cache**
   - If upload preview fails
   - Reload page and try again

### Signature Application Fails

**Symptoms**: Cannot sign document or signing hangs

**Solutions**:

1. **Check certificate status**
   - Verify selected certificate is active
   - Check certificate hasn't expired
   - Ensure certificate has signing capability

2. **Check PDF**
   - Ensure PDF is not corrupted
   - Try signing different PDF
   - Verify PDF is not password protected

3. **Check permissions**
   - Verify user has signing permissions
   - Check role includes PDF signing
   - Check resource limits

4. **Check server resources**
   - Monitor CPU: `docker stats`
   - Check memory: `free -h`
   - Review logs for resource errors

### Signature Verification Fails

**Symptoms**: Signed PDF shows as invalid or untrusted

**Solutions**:

1. **Check PDF integrity**
   - Ensure PDF wasn't modified after signing
   - Verify file wasn't corrupted during transfer

2. **Check certificate trust**
   - Verify CA certificate is in trusted store
   - Check certificate chain is complete
   - Verify timestamp if included

3. **Check timestamp**
   - If using timestamp, verify TSA is accessible
   - Check timestamp certificate validity
   - Verify time synchronization

4. **Re-verify signature**
   - Try verifying on different system
   - Use alternative PDF reader
   - Check verification tool version

## Server Issues

### Backend Service Won't Start

**Symptoms**: `docker-compose ps` shows backend as exited

**Solutions**:

1. **Check logs**
   ```bash
   docker-compose logs backend --tail=50
   ```

2. **Check configuration**
   - Verify all required environment variables are set
   - Check `DATABASE_URL` is correct
   - Verify `ENCRYPTED_STORAGE_MASTER_KEY` is set

3. **Check database**
   - Verify PostgreSQL is running: `docker-compose ps`
   - Test connection: `psql $DATABASE_URL`
   - Run migrations: `docker-compose exec backend alembic upgrade head`

4. **Restart service**
   ```bash
   docker-compose restart backend
   ```

### Database Connection Failed

**Symptoms**: Backend logs show "connection refused" or "authentication failed"

**Solutions**:

1. **Verify database is running**
   ```bash
   docker-compose ps db
   ```

2. **Check credentials**
   ```bash
   echo $DATABASE_URL
   # Should be: postgresql://user:password@host:5432/dbname
   ```

3. **Test connection**
   ```bash
   docker-compose exec db psql -U postgres -h db
   ```

4. **Check network**
   ```bash
   docker network ls
   docker network inspect ca_pdf_default
   ```

### API Endpoints Return 500 Error

**Symptoms**: API calls return HTTP 500

**Solutions**:

1. **Check logs**
   ```bash
   docker-compose logs backend | tail -100
   ```

2. **Identify error type**
   - Database error: Check database connectivity
   - Validation error: Check request parameters
   - Permission error: Check user role
   - Not found error: Check resource exists

3. **Test with curl**
   ```bash
   curl -v http://localhost:8000/api/v1/auth/me \
        -H "Authorization: Bearer TOKEN"
   ```

4. **Check server resources**
   - Memory: `docker stats`
   - Disk: `df -h`
   - CPU: `top`

### Port Already in Use

**Symptoms**: "Address already in use" error when starting services

**Solutions**:

1. **Find process using port**
   ```bash
   lsof -i :8000      # Find process using port 8000
   lsof -i :3000      # Find process using port 3000
   ```

2. **Kill process**
   ```bash
   kill -9 <PID>
   ```

3. **Change port in docker-compose.yml**
   ```yaml
   services:
     backend:
       ports:
         - "8001:8000"  # Changed from 8000
   ```

4. **Clean up Docker**
   ```bash
   docker-compose down
   docker system prune -a
   ```

## Frontend Issues

### Page Blank or Showing Errors

**Symptoms**: Frontend loads but shows blank page or error

**Solutions**:

1. **Check console errors**
   - Open Developer Tools (F12)
   - Go to Console tab
   - Look for JavaScript errors

2. **Check network tab**
   - Open Developer Tools → Network tab
   - Look for failed requests
   - Check API responses

3. **Verify backend is running**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. **Clear cache and reload**
   - Ctrl+Shift+R (hard refresh)
   - Clear LocalStorage: DevTools → Application → Clear storage

### Buttons Not Working

**Symptoms**: Clicking buttons has no effect

**Solutions**:

1. **Check console for errors**
   - See "Page Blank or Showing Errors"

2. **Verify API connectivity**
   - Test API manually: `curl http://localhost:8000/api/v1/...`

3. **Check permissions**
   - Verify user role allows the action
   - Check authorization settings

4. **Refresh page**
   - Sometimes React state gets out of sync
   - Reload page to reset

### Slow Performance

**Symptoms**: Page loading is very slow

**Solutions**:

1. **Check network speed**
   - Test connection speed
   - Check network latency

2. **Check server performance**
   - Monitor CPU: `docker stats`
   - Check memory: `free -h`
   - Review database query times

3. **Optimize requests**
   - Reduce data fetched per request
   - Enable pagination
   - Cache on client side

4. **Use browser dev tools**
   - Network tab: Identify slow requests
   - Performance tab: Profile execution

## Database Issues

### Database Locked

**Symptoms**: Operations hang or fail with "database locked"

**Solutions**:

1. **Kill long-running transactions**
   ```sql
   SELECT pid, usename, query, query_start 
   FROM pg_stat_activity;
   SELECT pg_terminate_backend(pid);
   ```

2. **Check for deadlocks**
   - Review application logs
   - Check concurrent operations

3. **Restart database**
   ```bash
   docker-compose restart db
   ```

### Disk Space Full

**Symptoms**: Database operations fail with "no space left"

**Solutions**:

1. **Check disk usage**
   ```bash
   df -h
   du -sh /var/lib/docker/*
   ```

2. **Clean up Docker**
   ```bash
   docker system prune -a
   docker volume prune
   ```

3. **Archive old data**
   - Backup and delete old audit logs
   - Remove old document records

4. **Expand disk**
   - For cloud servers, increase volume size
   - For local, add new storage device

## Common Error Messages

### "Invalid Token"
- Token has expired or been revoked
- Token was modified
- Encode/decode error

**Fix**: Log in again to get new token

### "User Not Found"
- User was deleted
- Username typo
- Account deactivated

**Fix**: Verify username or contact administrator

### "Certificate Not Valid"
- Certificate expired
- Certificate revoked
- Certificate not found

**Fix**: Request new certificate or check certificate ID

### "PDF Signature Invalid"
- PDF was modified after signing
- Certificate chain broken
- Signature corrupted

**Fix**: Re-sign document or verify source PDF

## Performance Optimization

### Improve Response Times

1. **Enable caching**
   - Redis configuration
   - Browser caching headers
   - API response caching

2. **Optimize database**
   - Add indexes on frequently queried columns
   - Analyze query plans
   - Use connection pooling

3. **Frontend optimization**
   - Lazy load components
   - Minimize bundle size
   - Enable gzip compression

### Monitor Performance

```bash
# Database performance
docker-compose exec db psql -U postgres -d ca_pdf \
  -c "SELECT query, calls, mean_time FROM pg_stat_statements;"

# Application metrics
curl http://localhost:8000/metrics

# System resources
docker stats --no-stream
```

## Still Need Help?

If you can't resolve your issue:

1. **Gather information**
   - Error messages from logs
   - Steps to reproduce
   - Environment details (OS, Docker version, etc.)
   - Screenshots if applicable

2. **Contact support**
   - Email: [7780102@qq.com](mailto:7780102@qq.com)
   - Include all gathered information
   - Mention what you've already tried

3. **Report issue on GitHub**
   - GitHub Issues: [ca-pdf/issues](https://github.com/QAQ-AWA/ca-pdf/issues)
   - Use issue template
   - Provide reproducible steps

## For More Detailed Solutions

For comprehensive troubleshooting including:
- Detailed diagnostic procedures
- Advanced debugging techniques
- Recovery procedures
- Performance tuning guides
- Capacity planning

Please refer to the [Complete Troubleshooting Guide (Chinese)](../zh/TROUBLESHOOTING.md).

## Additional Resources

- [User Guide](./USER_GUIDE.md) - Usage instructions
- [Deployment Guide](./DEPLOYMENT.md) - Deployment and configuration
- [Development Guide](./DEVELOPMENT.md) - For development environments
- [Security Guide](./SECURITY.md) - Security issues

---

**Last updated**: 2024
