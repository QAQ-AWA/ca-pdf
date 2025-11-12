# Architecture Overview (Preview)

> **Note:** This English outline summarizes the system structure. The Chinese document contains detailed diagrams, sequence flows, and deployment topologies.

## High-level Components

- **Frontend (React + Vite)** — user interface for certificate management, signing, and verification.
- **Backend (FastAPI)** — REST API, business logic, audit logging, and integration points.
- **Database (PostgreSQL)** — stores users, certificates, signing records, and audit logs.
- **Storage** — encrypted file storage for seals and uploaded PDFs using Fernet master key.
- **Timestamp Authority (TSA)** — optional external service for RFC3161 timestamps.

## Backend Modules

| Module | Description |
|--------|-------------|
| `app/api/endpoints` | FastAPI routers for auth, CA, PDF signing, audit, and users. |
| `app/services` | Business logic (certificate issuance, PDF operations, audit writing). |
| `app/models` | SQLAlchemy ORM models for persistent entities. |
| `app/core` | Configuration, security utilities, and encryption helpers. |
| `app/db` | Database session management and Alembic migration hooks. |

## Security Layers

- JWT-based authentication with short-lived access tokens and refresh tokens.
- Role-based authorization (admin vs. user) enforced via dependency injection.
- Password hashing with `bcrypt` plus minimum complexity validation.
- Encrypted storage for private keys, seal files, and timestamp credentials.
- Comprehensive audit trail with IP, user agent, and resource metadata.

## Signing Workflow

1. User uploads a PDF.
2. Backend retrieves private key material and seal assets (encrypted at rest).
3. PDF is signed using pyHanko with optional visible annotations.
4. Timestamping step contacts TSA when enabled.
5. Resulting PDF and metadata are stored; audit log entry is recorded.

## Verification Workflow

1. PDF is uploaded to the verification endpoint.
2. Signatures are analyzed for cryptographic validity and trust chain status.
3. Timestamp validity and document modification status are reported.
4. Results are returned with human-readable summaries for end users.

## Scaling Considerations

- Run backend workers behind a reverse proxy (Traefik) with sticky sessions when needed.
- Offload heavy signing batches to background workers (Celery/Redis) if volume grows.
- Store uploaded documents on an object storage service with server-side encryption.

## Observability

- Structured logging with request identifiers.
- Prometheus-compatible metrics for throughput, errors, and signing latency.
- Alerting for certificate expiration, disk usage, and queue backlogs.
