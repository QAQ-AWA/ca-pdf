# ca-pdf Architecture Design Document

> 📖 **Documentation Navigation**: [README](./README.en.md) · [Documentation Index](./DOCUMENTATION.md) · [Development Guide](./DEVELOPMENT.en.md) · [API Reference](./API.en.md) · [Security Guide](./SECURITY.md)
> 🎯 **Target Audience**: Architects / Senior Developers
> ⏱️ **Estimated Reading Time**: 35 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This document focuses on system design and technology stack. For product capabilities, see [README.en.md](./README.en.md); for implementation details, see [DEVELOPMENT.en.md](./DEVELOPMENT.en.md); for API interaction, see [API.en.md](./API.en.md); for security strategy, see [SECURITY.md](./SECURITY.md).

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

ca-pdf is composed of React frontend, FastAPI backend, and PostgreSQL data layer, unified under HTTPS entry via Traefik. Frontend outputs static resources packaged by Vite, hosted by independent container (Nginx); user business requests route via Traefik to FastAPI service. FastAPI internally uses layered architecture: api layer handles protocol conversion, service layer carries core business logic, crud/model layer interacts with database, while EncryptedStorageService manages sensitive files and keys. CA/PDF related services interact with external TSA/OCSP services, all critical operations logged to audit_logs for tracking.

**Key Components**:
- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL + async driver
- **Proxy**: Traefik (SSL/TLS, routing)
- **Security**: JWT, bcrypt, Fernet encryption
- **Signing**: pyHanko (PDF signatures), RFC3161 (timestamps)

### 1.2 Three-Layer Architecture

- **Presentation Layer**: React single-page application handles all user interaction logic with React Router, Context, custom components for UI rendering; requests via axios/httpClient to backend JSON API; frontend manages local state, token storage, visual feedback.

- **Application Layer**: FastAPI API Router, dependency injection system, and service classes (CertificateAuthorityService, PDFSigningService) form middleware layer handling parameter validation, authorization, business orchestration, audit logging, error handling, maintaining interface stability.

- **Data Layer**: SQLAlchemy ORM models and CRUD repositories abstract PostgreSQL data reads/writes; EncryptedStorageService encrypts files and private keys with Fernet or AES-GCM; audit logs, token blacklists support compliance and security requirements.

---

## 2. Backend Architecture

### 2.1 Directory Structure

```
backend/app
├── api/                 # FastAPI routes & dependencies
│   ├── endpoints/       # Route implementations
│   └── dependencies/    # Dependency injection
├── core/               # Configuration & utilities
├── crud/               # Database CRUD operations
├── db/                 # Database session & initialization
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic data contracts
└── services/           # Core business logic
```

### 2.2 Authentication & Authorization

**JWT Token Workflow**:
- Access Token: 15-minute default expiration
- Refresh Token: 3-day default expiration
- Token Rotation: Sliding expiration on refresh
- Blacklist: Immediate revocation via jti tracking

**RBAC Model**:
- Roles: admin, user
- Permission checks via `require_roles` decorator
- End-to-end consistency (frontend ProtectedRoute + backend middleware)

### 2.3 Core Services

**CertificateAuthorityService**: CA management (root generation, certificate issuance, revocation, CRL)

**PDFSigningService**: PDF signing with pyHanko (visible/invisible signatures, timestamps, LTV)

**PDFVerificationService**: Signature verification (validity, trust chain, timestamp)

**EncryptedStorageService**: Encrypted file & key storage (Fernet, AES-GCM)

---

## 3. Frontend Architecture

### 3.1 Directory Structure

```
frontend/src
├── pages/              # Page components
├── components/         # Reusable UI components
├── lib/               # Utilities & API client
│   ├── api.ts         # REST client
│   ├── auth.ts        # Auth logic
│   └── types.ts       # TypeScript types
└── main.tsx          # Entry point
```

### 3.2 State Management

- **Context API**: Authentication state (user, tokens)
- **Component State**: Local UI state (forms, modals)
- **API Calls**: Direct via httpClient (axios)

### 3.3 Key Features

- **Token Management**: Auto-refresh, local storage
- **Error Handling**: Global error boundary
- **Loading States**: Request pending feedback
- **Form Validation**: Client-side + server-side

---

## 4. Data Models

### 4.1 Core Tables

**users**: User accounts, roles, credentials
**certificates**: User certificates, status, validity
**ca_artifacts**: Root CA, intermediate certs, CRL
**pdf_signatures**: Signing records, metadata
**audit_logs**: Operation tracking
**seals**: Corporate seal images

### 4.2 Key Relationships

- Users → Certificates (1:N)
- Users → Audit Logs (1:N)
- Certificates → PDF Signatures (1:N)
- Users → Seals (N:N via user_seals)

---

## 5. Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 12+
- **Async**: asyncpg, asyncio
- **Validation**: Pydantic 2.0+
- **PDF**: pyHanko 0.16+
- **Crypto**: cryptography, bcrypt
- **Testing**: pytest, pytest-asyncio
- **Type**: mypy, Python 3.11+

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Build**: Vite 5+
- **Routing**: React Router 6+
- **HTTP**: axios
- **UI**: Tailwind CSS / shadcn/ui
- **Testing**: Vitest, React Testing Library
- **Linting**: ESLint, Prettier

### Infrastructure
- **Containers**: Docker 23+
- **Orchestration**: Docker Compose V2
- **Proxy**: Traefik 3.1+
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt (ACME)
- **Monitoring**: Prometheus/Grafana (optional)

---

## 6. Security Architecture

### 6.1 Encryption Strategy

- **Transport**: TLS 1.3+ (HTTPS)
- **Authentication**: JWT (HS256)
- **Passwords**: bcrypt (cost: 12)
- **Secrets**: Fernet (symmetric, with timestamp validation)
- **Private Keys**: AES-GCM encryption + Fernet

### 6.2 Access Control

- **Authentication**: JWT tokens (access + refresh)
- **Authorization**: RBAC (admin/user roles)
- **Rate Limiting**: Per-endpoint limits (5 req/min default)
- **CORS**: Configurable whitelist

### 6.3 Audit Trail

- **Logging**: All operations tracked with user, IP, timestamp, resource
- **Immutability**: Append-only logs, no deletion
- **Export**: CSV/JSON export for compliance

---

## 7. Performance Considerations

### 7.1 Database Optimization

- **Indexes**: On frequently queried columns (email, serial_number, status)
- **Pagination**: Default limit 50, max 500
- **Lazy Loading**: Relations loaded on demand
- **Connection Pooling**: 20 default, 50 max connections

### 7.2 API Performance

- **Response Caching**: ETags for GET requests (optional)
- **Compression**: gzip enabled by default
- **Pagination**: Cursor-based for large datasets
- **Query Optimization**: SELECT specific fields

### 7.3 Frontend Performance

- **Code Splitting**: Route-based lazy loading
- **Asset Optimization**: minification, tree-shaking
- **Bundling**: Vite fast HMR for development

---

## 8. Deployment Architecture

### 8.1 Development

- **Database**: SQLite (file-based)
- **Services**: Running locally
- **Ports**: Backend 8000, Frontend 3000

### 8.2 Docker Compose

- **Database**: PostgreSQL container + volume
- **Backend**: FastAPI container
- **Frontend**: Nginx + static React build
- **Proxy**: Traefik with self-signed/Let's Encrypt

### 8.3 Production

- **Database**: Managed PostgreSQL (AWS RDS, Azure, GCP)
- **Backend**: Kubernetes or managed services
- **Frontend**: CDN + managed hosting
- **SSL**: Let's Encrypt auto-renewal
- **Backups**: Daily automated snapshots

---

## 9. Scalability Strategy

### 9.1 Horizontal Scaling

- **Stateless Backend**: Sessions stored in database, not memory
- **Load Balancing**: Traefik distributes traffic
- **Database Replication**: Primary-replica for read scaling

### 9.2 Vertical Scaling

- **Resource Limits**: Configurable CPU/memory per container
- **Database Tuning**: Index optimization, query analysis
- **Connection Pooling**: Appropriate pool size

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

- **Database**: Daily snapshots, 30-day retention
- **Configuration**: Encrypted backup of secrets
- **Private Keys**: Offline backup of master key
- **Test Recovery**: Monthly restoration drills

### 10.2 High Availability

- **Redundancy**: Multi-container deployments
- **Failover**: Automatic via orchestration
- **Monitoring**: Health checks every 30 seconds
- **Alerting**: Email/Slack notifications

---

## 11. Extension Points

### 11.1 Adding New Signing Methods

1. Extend `BaseSigningService`
2. Implement `sign()`, `verify()` methods
3. Register in service factory
4. Add endpoints in `api/endpoints/`

### 11.2 Custom Database

1. Update `DATABASE_URL` in configuration
2. Ensure SQLAlchemy dialect support
3. Run Alembic migrations
4. Test with new backend

### 11.3 Third-Party Integrations

- **TSA**: Configurable endpoint URL
- **OCSP**: For certificate status
- **CRL**: Automatic distribution
- **LDAP**: User directory (future)

---

## 12. Monitoring & Observability

### 12.1 Logging

- **Application**: Structured JSON logs
- **Database**: Query logging (optional)
- **Access**: Request/response logs
- **Level**: DEBUG, INFO, WARNING, ERROR

### 12.2 Metrics

- **Performance**: Response time, request count
- **Business**: Signatures created, certificates issued
- **System**: CPU, memory, disk usage

### 12.3 Tracing

- **OpenTelemetry**: Request tracing across services
- **Correlation ID**: Track request through system

---

## 13. Development Workflow

### 13.1 Local Development

1. Clone repository
2. Install dependencies (`make install`)
3. Configure `.env`
4. Initialize database (`poetry run alembic upgrade head`)
5. Start servers (`make dev-backend`, `make dev-frontend`)
6. Make changes and test

### 13.2 Testing

- Unit tests: Individual components/functions
- Integration tests: API endpoints with database
- E2E tests: Full user workflows
- Coverage: Aim for >80%

### 13.3 Code Review

- Automated checks: Linting, formatting, type checking, tests
- Manual review: Logic, security, performance
- Approval required before merge

---

**Last Updated**: 2024
**Version**: 1.0
