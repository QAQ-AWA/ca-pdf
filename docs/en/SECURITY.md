# Security Guide (Preview)

> **Scope:** Highlights of the security program. The Chinese document contains exhaustive checklists, compliance notes, and incident response playbooks.

## Responsible Disclosure

- Report vulnerabilities privately via [7780102@qq.com](mailto:7780102@qq.com).
- Provide reproduction steps and affected versions.
- Expect acknowledgment within 3 business days and coordinated disclosure.

## Key Management

- Protect `ENCRYPTED_STORAGE_MASTER_KEY`, `SECRET_KEY`, and database credentials.
- Rotate keys at least annually and after security incidents.
- Store offline backups of the Fernet master key and root CA private key.

## Authentication & Authorization

- Passwords hashed with bcrypt; enforce complexity policies.
- JWT access tokens (15 minutes) + refresh tokens (3 days).
- Role-based access control ensures admin-only endpoints remain protected.

## API Security Controls

- Input validation via Pydantic schemas.
- Rate limiting on critical endpoints (login, certificate issuance).
- CORS configuration requires JSON-formatted origin lists.

## Data Protection

- Seals and private keys encrypted at rest using Fernet.
- PDF uploads stored on persistent volumes with restricted access.
- Audit logs are immutable and timestamped for forensic accuracy.

## Deployment Hardening

- Enforce HTTPS with modern TLS configurations (Traefik or Nginx).
- Enable firewall rules or security groups limiting inbound traffic.
- Run services with non-root containers and minimal privileges.

## Monitoring & Incident Response

- Collect backend logs, audit events, and infrastructure metrics.
- Alert on repeated login failures, signing anomalies, and disk usage spikes.
- Follow the incident response checklist in the Chinese documentation for containment and recovery.
