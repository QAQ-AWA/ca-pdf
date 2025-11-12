# Security Guide

> **Status**: Security best practices and policies
> **Target Audience**: Security officers and administrators
> **Last Updated**: 2024

This guide covers security considerations for ca-pdf deployment and usage. For detailed security policies and procedures, please refer to the [Complete Security Guide (Chinese)](../zh/SECURITY.md).

## Security Principles

ca-pdf is built with security as a core principle:

1. **Defense in Depth**: Multiple security layers
2. **Least Privilege**: Minimal required permissions
3. **Encryption First**: Data encrypted at rest and in transit
4. **Audit Everything**: Comprehensive logging and monitoring
5. **Secure by Default**: Safe configurations out of the box

## Key Management

### Master Key (ENCRYPTED_STORAGE_MASTER_KEY)

The master key is critical for security:

**Requirements**:
- Minimum 32 characters (256-bit equivalent)
- Cryptographically random
- Must be changed on regular schedule
- Never committed to version control
- Never logged or transmitted unencrypted

**Generation**:
```bash
# Generate secure key
openssl rand -hex 32
# Example output: 7a8c9d3f2e1b4c6a9f8e7d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b
```

**Storage**:
- Store in `.env` file (not committed to git)
- Backup in secure location (encrypted)
- Rotate annually or after suspected compromise
- Never share with unauthorized personnel

### JWT Secret Key (JWT_SECRET_KEY)

JWT tokens authenticate API requests:

**Requirements**:
- At least 32 characters
- Cryptographically random
- Separate from master key
- Rotated on schedule or after compromise

**Rotation Impact**:
- All existing tokens become invalid
- Users must log in again
- Plan rotation during maintenance window

## Database Security

### Authentication

**PostgreSQL Configuration**:
```bash
# Use strong passwords
# Minimum: 16 characters, mixed case, numbers, special chars
POSTGRES_PASSWORD=YourSecurePassword123!@#

# Restrict user permissions
CREATE USER ca_pdf_user WITH PASSWORD 'secure_password';
GRANT USAGE ON SCHEMA public TO ca_pdf_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ca_pdf_user;
```

### Encryption

**Database-Level Encryption**:
- Enable PostgreSQL encryption
- Use encrypted connections (SSL/TLS)
- Backup encryption

**Column-Level Encryption**:
- Sensitive data fields encrypted
- Passwords hashed with bcrypt
- Keys encrypted with master key

### Backup Security

```bash
# Encrypted backup
pg_dump -U ca_pdf_user ca_pdf | \
  openssl enc -aes-256-cbc -salt -out backup.sql.enc

# Secure backup storage
# - Encrypt before transmission
# - Use secure cloud storage
# - Verify backup integrity regularly
# - Test restore procedures
```

## Authentication Security

### Password Policies

Enforce strong passwords:

```python
# Requirements from config
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True
```

Example: `Secure@Pass123`

### Multi-Factor Authentication

Planned for future versions:

```
2FA Methods:
- Time-based One-Time Password (TOTP)
- SMS verification
- Hardware security keys
```

### Session Management

**Token Configuration**:
```bash
# JWT expiration: 30 minutes recommended
JWT_EXPIRE_MINUTES=30

# Refresh token lifetime: 7 days
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Session Security**:
- Tokens stored in memory (not localStorage for sensitive operations)
- HTTPS enforced for all communications
- Automatic logout on inactivity
- Session audit logging

## API Security

### Rate Limiting

Protect against brute force and abuse:

```
Login: 5 requests/minute per IP
API: 100 requests/minute per authenticated user
```

### Input Validation

All inputs validated:

```python
from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)  # String constraints
    email: EmailStr  # Email format validation
    password: constr(min_length=8)  # Password requirements
```

### CORS Configuration

**Secure CORS Setup**:
```bash
# Only trusted origins
BACKEND_CORS_ORIGINS='["https://yourdomain.com", "https://app.yourdomain.com"]'

# NOT: "*" (never in production)
# NOT: "http://localhost:3000" (only in development)
```

## Data Protection

### Encryption in Transit

- **HTTPS/TLS 1.2+**: All communications encrypted
- **Certificate Validation**: Verify server certificate
- **Certificate Pinning**: Optional, for high security

**Nginx Configuration**:
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

### Encryption at Rest

- **Database Encryption**: PostgreSQL pgcrypto
- **File Encryption**: Stored PDFs and keys
- **Backup Encryption**: All backups encrypted

## Certificate Security

### CA Root Certificate

**Protection**:
- Stored securely with restricted access
- Never transmitted over network
- Backup in secure location
- Rotation every 10 years

### User Certificates

**Lifecycle**:
- Generated with 2048-bit RSA minimum
- Valid for 1-3 years (configurable)
- Revocation capability
- Chain verification

### Certificate Revocation

```
Methods:
1. Manual revocation via dashboard
2. Automatic on expiration
3. CRL (Certificate Revocation List)
4. OCSP (Online Certificate Status Protocol)
```

## Deployment Security

### Docker Security

```yaml
# docker-compose.yml
services:
  backend:
    image: ca-pdf:latest
    environment:
      - ENCRYPTED_STORAGE_MASTER_KEY=${ENCRYPTED_STORAGE_MASTER_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    # Do NOT run as root
    user: "1000:1000"
    # Read-only filesystem where possible
    read_only: true
    volumes:
      - /tmp  # Writable temp only
```

### Network Security

```
Deployment Architecture:
┌─────────────────────┐
│  Public Internet    │
└──────────┬──────────┘
           │ (HTTPS)
      ┌────▼─────┐
      │ Firewall │
      └────┬─────┘
           │
    ┌──────▼──────────┐
    │  Load Balancer  │ (Reverse Proxy/Traefik)
    └──────┬──────────┘
           │
    ┌──────▼──────────┐
    │   API Server    │ (Private Network)
    └──────┬──────────┘
           │
    ┌──────▼──────────┐
    │   Database      │ (Private Network, no internet)
    └─────────────────┘
```

### Secrets Management

Never commit secrets to git:

```bash
# .gitignore
.env
.env.local
.env.*.local
secrets/
keys/
```

Use environment variables or secret managers:

```bash
# Option 1: Environment variables
export ENCRYPTED_STORAGE_MASTER_KEY=$(openssl rand -hex 32)

# Option 2: HashiCorp Vault
vault kv get secret/ca-pdf/master-key

# Option 3: AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id ca-pdf-master-key
```

## Audit and Compliance

### Audit Logging

Every operation logged:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": 123,
  "action": "SIGN_PDF",
  "resource": "document_456",
  "status": "SUCCESS",
  "ip_address": "192.168.1.100",
  "details": {
    "document_name": "contract.pdf",
    "certificate_id": 789
  }
}
```

**Audit Trail Protection**:
- Immutable (append-only)
- Encrypted storage
- Tamper detection
- Long-term retention

### Compliance Requirements

**GDPR Compliance**:
- Data minimization
- User consent management
- Right to deletion
- Breach notification

**PCI-DSS** (if processing payment data):
- Network security
- Data protection
- Access control
- Vulnerability management

## Security Best Practices

### For Administrators

1. ✅ Keep system updated
2. ✅ Use strong passwords
3. ✅ Enable HTTPS/TLS
4. ✅ Regular backups
5. ✅ Monitor logs
6. ✅ Restrict network access
7. ✅ Use firewall rules
8. ✅ Regular security audits
9. ✅ Incident response plan
10. ✅ Employee training

### For Users

1. ✅ Use strong passwords
2. ✅ Never share credentials
3. ✅ Verify before signing
4. ✅ Logout when finished
5. ✅ Report suspicious activity
6. ✅ Keep email secure
7. ✅ Use official links only
8. ✅ Enable 2FA (when available)

### For Developers

1. ✅ Code review process
2. ✅ SAST tools (static analysis)
3. ✅ Dependency scanning
4. ✅ Security testing
5. ✅ No secrets in code
6. ✅ Input validation
7. ✅ Error handling
8. ✅ Security logging

## Vulnerability Management

### Reporting Vulnerabilities

**Responsible Disclosure**:
- Email: [7780102@qq.com](mailto:7780102@qq.com)
- Include reproduction steps
- Allow time for fix before disclosure
- Do not exploit vulnerability

### Patching

```bash
# Update dependencies
pip install -U -r requirements.txt
npm audit fix

# Check for vulnerabilities
safety check           # Python
npm audit              # Node.js
```

## Incident Response

### Breach Response Plan

1. **Detect**: Monitor logs for unauthorized access
2. **Contain**: Disable compromised accounts
3. **Investigate**: Determine scope and impact
4. **Notify**: Inform affected users (if required)
5. **Recover**: Restore from clean backup
6. **Improve**: Implement preventive measures

### Emergency Procedures

**Compromised Master Key**:
```bash
1. Immediately disable current key
2. Rotate to new master key
3. Re-encrypt all sensitive data
4. Audit all access logs
5. Force user password resets
6. Restore from backups if needed
```

## For Complete Security Details

For comprehensive security documentation including:
- Detailed threat models
- Security audit procedures
- Penetration testing guide
- Security configuration examples
- Incident response procedures
- Compliance checklists

Please refer to the [Complete Security Guide (Chinese)](../zh/SECURITY.md).

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Web security risks
- [CWE Top 25](https://cwe.mitre.org/top25/) - Most dangerous weaknesses
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)

## Additional Guides

- [Deployment Guide](./DEPLOYMENT.md) - Secure deployment
- [Contributing Guide](./CONTRIBUTING.md) - Secure development
- [Troubleshooting](./TROUBLESHOOTING.md) - Security issues

---

**Last updated**: 2024
