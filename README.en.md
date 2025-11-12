# ca-pdf English README

> 📖 **Documentation Navigation**: [Documentation Index](./DOCUMENTATION.md) · [User Guide](./USER_GUIDE.en.md) · [Deployment Guide](./DEPLOYMENT.en.md) · [Development Guide](./DEVELOPMENT.en.md) · [API Documentation](./API.en.md)
> 🎯 **Target Audience**: All roles
> ⏱️ **Estimated Reading Time**: 15 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This document serves as the entry point for the ca-pdf project, providing an overview of product value, quick start guide, and key features. For detailed topics, please refer to the "Documentation Navigation" section below.

---

ca-pdf is a self-hosted PDF digital signature platform with a complete Certificate Authority (CA) system, timestamp service support, and enterprise-grade audit capabilities. It provides organizations with trustworthy digital signature infrastructure, supporting both on-premises deployment and cloud hosting.

## 📚 Documentation Navigation

README is the entry document for ca-pdf. Please select an appropriate reading order based on your role and use the table below to quickly locate the information you need.

### Recommended Reading Paths

- 🆕 **New Users**: [README](./README.en.md) → [User Guide](./USER_GUIDE.en.md) → [Troubleshooting](./TROUBLESHOOTING.md)
- 👩‍💻 **Developers**: [README](./README.en.md) → [Development Guide](./DEVELOPMENT.en.md) → [Architecture](./ARCHITECTURE.en.md) → [API](./API.en.md)
- 🛡️ **Administrators**: [README](./README.en.md) → [Deployment Guide](./DEPLOYMENT.en.md) → [Security Guide](./SECURITY.md) → [User Guide](./USER_GUIDE.en.md)
- 🤝 **Contributors**: [README](./README.en.md) → [Contributing Guide](./CONTRIBUTING.md) → [Development Guide](./DEVELOPMENT.en.md)

### Key Features Overview

| Document | Target Audience | One-Line Description |
|----------|---------|------------|
| [DOCUMENTATION.md](./DOCUMENTATION.md) | All readers | Complete documentation map and topic entry points |
| [README](./README.en.md) | Everyone | Product overview, quick start, documentation navigation |
| [USER_GUIDE.en.md](./USER_GUIDE.en.md) | Business users | Certificate management and PDF signing workflows |
| [DEVELOPMENT.en.md](./DEVELOPMENT.en.md) | Developers | Local environment setup, code standards, and debugging tips |
| [ARCHITECTURE.en.md](./ARCHITECTURE.en.md) | Architects | System design, technology stack, and component interactions |
| [API.en.md](./API.en.md) | Integration developers | REST API endpoint reference and examples |
| [DEPLOYMENT.en.md](./DEPLOYMENT.en.md) | DevOps / Administrators | Deployment, environment variables, and operations guidelines |
| [SECURITY.md](./SECURITY.md) | Security officers | Key management, security policies, and compliance recommendations |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | All readers | Common issues and troubleshooting guide |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Contributors | Contribution workflow, code standards, and review requirements |
| [CHANGELOG.md](./CHANGELOG.md) | Maintainers | Version history and release dates |

> 📌 Detailed technical stack versions are maintained only in [ARCHITECTURE.en.md](./ARCHITECTURE.en.md); environment variable configuration is centralized in [DEPLOYMENT.en.md](./DEPLOYMENT.en.md); quick start commands follow this README, with other documents referencing it directly.

## 📌 Project Overview

### Core Value Proposition

ca-pdf enables you to quickly build an independent PDF digital signature system with full control over the certificate hierarchy and signing process. No dependence on third-party service providers—your data and key materials are fully managed on your own infrastructure, making it ideal for organizations requiring high customization and privacy protection.

### Core Features

| Feature | Description |
|---------|------------|
| **Self-Hosted Root CA** | Self-signed root certificate, full key control, supports RSA-4096/EC-P256 algorithms |
| **Certificate Lifecycle** | Issue/import/revoke/renew certificates, PKCS#12 format, automatic CRL generation |
| **PDF Digital Signature** | Single/batch signing, visible/invisible signatures, corporate seal application |
| **Timestamp & LTV** | RFC3161 TSA integration, long-term validation material embedding, Acrobat compatible |
| **Signature Verification** | Multi-signature parsing, trust chain verification, timestamp validity checking |
| **Audit & Security** | Complete operation logs, IP and User-Agent tracking, tamper-proof records |
| **User Permission Management** | JWT + Refresh Token authentication, RBAC role control, multi-user support |
| **Corporate Seal Management** | PNG/SVG seal upload, encrypted storage, version management, reusable application |

### Use Cases

- 🏢 **Enterprise Contract Signing**: Internal workflow documents, vendor agreements, employee documentation
- 📋 **Administrative Approval**: Approval forms, workflow processes, authorization documents
- 🏥 **Healthcare**: Prescriptions, diagnostic reports, medical orders
- ⚖️ **Legal Compliance**: Contract archiving, evidence preservation, regulatory compliance
- 📦 **Logistics**: Document signing, receipt confirmation, handoff documents

---

## 🚀 Quick Start

### System Requirements

- **Docker Engine** 23+ and **Docker Compose** V2
- **Python** 3.11+ (for local development)
- **Node.js** 16+ (for frontend development)
- **PostgreSQL** 12+ (recommended for production, SQLite available for local development)
- A domain resolvable to the host machine (use `*.localtest.me` or `localhost` for development)

### One-Command Installation (Recommended)

Execute this command on a fresh host to automatically check dependencies, download scripts, and initialize deployment:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
```

The installer will automatically:

1. Check Bash version, Docker, Docker Compose, ports 80/443, memory and disk space requirements.
2. Detect your Linux distribution and automatically install curl, git, jq, openssl, docker, docker compose, and other dependencies.
3. Download deployment templates (docker-compose.yml, Traefik configuration, environment variable examples) and generate `.env` / `.env.docker`.
4. Generate admin credentials, database passwords, JWT keys, and Fernet master keys, supporting localtest.me self-signed or Let's Encrypt certificates.
5. Start the complete container stack, automatically run database migrations, with all logs saved to `logs/installer-YYYYMMDD.log`.

After installation, the `capdf` command will be registered in `/usr/local/bin`, allowing you to access the interactive menu anytime:

```bash
capdf menu
```

Example common subcommands:

```bash
capdf install     # Re-enter the installation wizard
capdf up          # Build and start (or upgrade) services
capdf down        # Stop services (add --clean to remove data volumes)
capdf logs -f     # View real-time logs for all services
capdf backup      # Generate database and configuration backup
capdf restore     # Restore from existing backup
capdf self-update # Pull the latest installation script
```

For offline deployment or custom images and configurations, see the manual steps below and [DEPLOYMENT.en.md](./DEPLOYMENT.en.md).

### Local Development Installation

#### 1. Clone the Repository and Enter Project Directory

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
```

#### 2. Configure Environment Variables

```bash
# Copy example configuration files
cp .env.example .env
cp .env.docker.example .env.docker

# Edit .env to fill in necessary variables
# Generate secure keys
openssl rand -base64 32  # for SECRET_KEY
openssl rand -base64 32  # for ENCRYPTED_STORAGE_MASTER_KEY
```

Key environment variables:

| Variable | Description | Example |
|----------|------------|---------|
| `SECRET_KEY` | JWT signing key | Generated via `openssl rand -base64 32` |
| `ENCRYPTED_STORAGE_MASTER_KEY` | Master key for encrypting private keys (required, must be safeguarded) | 32-byte Fernet key |
| `DATABASE_URL` | Async SQLAlchemy connection string | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Auto-created admin credentials on first startup | `admin@example.com` / `SecurePass123` |
| `BACKEND_DOMAIN` | API service domain (Traefik exposed) | `api.localtest.me` |
| `FRONTEND_DOMAIN` | Frontend domain (Traefik exposed) | `app.localtest.me` |

#### 3. Run Locally (Docker Compose)

```bash
# One-click startup of full stack (including PostgreSQL, backend, frontend, Traefik)
capdf up

# Check service status
capdf status

# View logs
capdf logs -f backend
```

> 💡 If you haven't run the installer yet, you can run `scripts/deploy.sh <command>` in the repository directory for the same effect.

Or local development mode (requires manually starting PostgreSQL):

```bash
# Install dependencies
make install

# Start backend API (with hot reload)
make dev-backend

# In another terminal, start frontend (Vite dev server)
make dev-frontend
```

#### 4. First Access and Login

- **Frontend Application**: https://app.localtest.me (or http://localhost:3000)
- **API Documentation**: https://api.localtest.me/docs (or http://localhost:8000/docs)
- **Default Credentials**: `ADMIN_EMAIL` / `ADMIN_PASSWORD` from .env

After first login, go to "Certificate Management" to generate a root CA, then you can begin the signing process.

---

## 📊 Feature Overview

### Authentication and Authorization

- **JWT Authentication**: Access Token (15 minutes) + Refresh Token (3 days)
- **RBAC Permissions**: Admin (administrator) / User (regular user) two-level roles
- **Token Rotation**: Automatically rotates on refresh token exchange for enhanced security
- **Rate Limiting**: Login endpoint restricted (default 5 attempts/60 seconds to prevent brute force)

### Certificate Management

| Operation | Description |
|-----------|------------|
| Generate Root CA | Self-signed root certificate, supports RSA-4096/EC-P256, customizable validity period |
| Issue Certificate | Issue user certificate based on root CA, returns PKCS#12 bundle |
| Import Certificate | Import external PKCS#12 format certificates into the system |
| View List | List current user's or all certificates (for admins), display status and expiration |
| Revoke Certificate | Immediately revoke certificate, automatically generate CRL list |
| Download CRL | Get latest certificate revocation list for client verification |

### PDF Digital Signing

| Type | Description |
|------|------------|
| Single Signature | Upload PDF, select position and signature style, one-click signing |
| Batch Signing | Sign multiple PDFs simultaneously (default max 10), apply same parameters to all |
| Visible Signature | Display signature box at specified PDF location (includes timestamp and certificate info) |
| Invisible Signature | Embed digital signature without changing PDF visual appearance |
| Corporate Seal | Upload company logo/seal, apply to signature box |
| Signature Metadata | Support recording signing reason, location, contact info, etc. |
| TSA Timestamp | Integrate RFC3161-compatible timestamp service for legal validity |
| LTV Embedding | Embed validation materials (OCSP/CRL) in signature for long-term validity |

### Signature Verification

- **Multi-Signature Verification**: Verify all digital signatures in a file in a single upload
- **Validity Assessment**: Valid / Invalid / Unsigned status
- **Trust Chain Verification**: Trusted / Untrusted verification results
- **Timestamp Checking**: Display signature time, timestamp provider, validity status
- **Modification Detection**: DocMDP level judgment on whether file was modified after signing

### Audit Logs

- **Complete Operation Records**: All critical operations including certificate generation, signing, revocation, login, access
- **Metadata Recording**: Executor, IP address, User-Agent, operation time, resource identification
- **Log Queries**: Support filtering by user, event type, date range, and other dimensions
- **Export Functions**: Support exporting to CSV/JSON format for external audits

### Users and Permissions

- **Multi-User Support**: Multiple users in an organization can use the system simultaneously
- **Permission Control**: Role-based access control (RBAC)
- **User Management**: Admins can create/enable/disable user accounts
- **Password Policy**: Support password complexity checking and expiration management

### Corporate Seals

- **Upload Management**: Support PNG (recommended transparent background) and SVG vector formats
- **Size Limits**: Default max 1 MiB, adjustable via environment variable
- **Encrypted Storage**: Seal files encrypted with master key for secure storage
- **Version Management**: Support updating seals, old versions queryable but not reused
- **Batch Application**: Apply same seal to multiple documents in batch signing

---

## 🛠️ Technology Stack Overview

The complete technology stack version matrix is maintained only in [ARCHITECTURE.en.md](./ARCHITECTURE.en.md) in the "Technology Stack" section. This section briefly lists core components to help quickly locate relevant documentation.

- **Backend**: FastAPI, SQLAlchemy, Alembic, pyHanko
- **Frontend**: React, TypeScript, Vite, React Router
- **Database & Storage**: PostgreSQL, SQLite (testing), Fernet encrypted storage
- **Infrastructure**: Docker, Traefik, Nginx, Prometheus/Grafana
- **Security Components**: JWT, bcrypt, TLS, audit logs

---

## 📁 Project Structure

```
ca-pdf/
├── backend/
│   ├── app/
│   │   ├── api/                    # REST API routes (v1 version)
│   │   │   ├── endpoints/          # Endpoint implementations (certificates, signing, verification, etc.)
│   │   │   └── dependencies.py     # Dependency injection (authentication, permissions, etc.)
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py             # User model
│   │   │   ├── certificate.py      # Certificate model
│   │   │   ├── pdf_signature.py    # Signing records
│   │   │   └── audit_log.py        # Audit logs
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── crud/                   # Database CRUD operations
│   │   ├── services/               # Business logic
│   │   │   ├── ca_service.py       # CA certificate management
│   │   │   ├── pdf_service.py      # PDF signing and verification
│   │   │   ├── audit_service.py    # Audit logs
│   │   │   └── seal_service.py     # Corporate seal management
│   │   ├── core/                   # Core configuration
│   │   │   ├── config.py           # Environment variable configuration
│   │   │   ├── security.py         # Authentication and password handling
│   │   │   └── encryption.py       # Key encryption storage
│   │   ├── db/                     # Database connections
│   │   └── main.py                 # FastAPI application entry point
│   ├── migrations/                 # Alembic database migrations
│   ├── tests/                      # Backend unit and integration tests
│   ├── Dockerfile                  # Backend container image
│   └── pyproject.toml              # Poetry dependency management
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Page components
│   │   │   ├── LoginPage.tsx       # Login page
│   │   │   ├── DashboardPage.tsx   # Dashboard
│   │   │   ├── CertificatePage.tsx # Certificate management
│   │   │   ├── SignaturePage.tsx   # Signing workbench
│   │   │   ├── VerifyPage.tsx      # Verification center
│   │   │   └── AuditPage.tsx       # Audit logs (admin)
│   │   ├── components/             # Reusable UI components
│   │   │   ├── Navigation.tsx
│   │   │   ├── CertificateList.tsx
│   │   │   ├── PDFViewer.tsx
│   │   │   └── SealUploadManager.tsx
│   │   ├── lib/                    # Utility functions and API client
│   │   │   ├── api.ts             # API call wrapper
│   │   │   ├── auth.ts            # Authentication logic
│   │   │   └── types.ts           # TypeScript type definitions
│   │   └── main.tsx                # React application entry point
│   ├── Dockerfile                  # Frontend container image
│   ├── nginx.conf                  # Nginx configuration (production)
│   ├── package.json                # npm dependency management
│   └── tsconfig.json               # TypeScript configuration
│
├── config/                         # Shared configuration
│   ├── .eslintrc.json              # ESLint rules
│   └── prettier.config.js          # Prettier formatting configuration
│
├── scripts/                        # Development helper scripts
│   ├── setup-db.sh                 # Database initialization
│   └── generate-keys.sh            # Generate encryption keys
│
├── docker-compose.yml              # Full stack orchestration configuration
├── Makefile                        # Development command shortcuts
├── deploy.sh                       # Deployment script compatible with capdf subcommands
├── .env.example                    # Environment variable example
├── .env.docker.example             # Docker environment variable example
└── README.en.md                    # This file

```

---

## 🐳 Deployment Options

### Local Development (Docker Compose)

The fastest way to start is using the global `capdf` command (automatically configured by the one-click installer), with a single command to start the complete development stack:

```bash
# One-click startup
capdf up

# First startup will automatically:
# 1. Build frontend and backend images
# 2. Start Traefik (reverse proxy)
# 3. Start PostgreSQL (database)
# 4. Start backend API (FastAPI)
# 5. Start frontend application (React)
# 6. Run database migrations (Alembic)
# 7. Create default admin account

# Stop services
capdf down

# Restart application
capdf restart

# Complete cleanup (including data volumes)
capdf down --clean
```

> If you haven't installed the global command in the source repository, you can continue using `scripts/deploy.sh <command>` or `./deploy.sh <command>` in the project root for the same operations.

### Production Deployment Overview

For production environment deployment, please refer to the **[DEPLOYMENT.en.md](./DEPLOYMENT.en.md)** document, which includes:

- 🔒 **SSL/TLS Configuration**: Let's Encrypt certificate auto-renewal
- 🔑 **Key Management**: Master key offline backup and recovery
- 📊 **High Availability**: Load balancing and failover
- 📈 **Monitoring & Alerting**: Prometheus + Grafana integration
- 🔄 **Backup & Recovery**: Database and critical data backup strategies

### Environment Variable Configuration

For complete environment variable descriptions, default values, and security considerations, please refer to the "Environment Variable Checklist" section in [DEPLOYMENT.en.md](./DEPLOYMENT.en.md). This README retains only the core guidance needed for quick startup.

---

## 📄 License and Contact

### Open Source License

ca-pdf is open-sourced under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

You are free to use this software in commercial and non-commercial projects, but please retain the original license notice.

### How to Contribute

We welcome community contributions! Contribution steps:

1. **Fork** this repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push the branch** (`git push origin feature/amazing-feature`)
5. Create a **Pull Request**

Please ensure:
- Code passes all tests (`make test`)
- Code quality checks pass (`make lint`)
- Commit messages are clear and concise
- New features include documentation and tests

### Report Issues

Encountered an issue or have a suggestion?

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/QAQ-AWA/ca-pdf/issues)
- 💡 **Feature Suggestions**: [GitHub Discussions](https://github.com/QAQ-AWA/ca-pdf/discussions)
- 📧 **Contact Us**: [7780102@qq.com](mailto:7780102@qq.com)

## 📘 Documentation Maintenance

We are committed to keeping documentation synchronized with code changes. Users will receive responses to feedback within 3 business days and all necessary documentation synchronization will be completed within 7 days of changes.

### Long-term Maintenance Commitment
- Any changes affecting users, deployment, security, or operations must be synchronized with corresponding documentation before merging and noted in the PR.
- New features must have README / USER_GUIDE / API documentation updates completed within 1 week of merge.
- Each release generates corresponding documentation version records with historical versions retained for reference.

### Regular Maintenance Rhythm
- **Weekly**: Check GitHub Issues and PR comments tagged with `documentation` to collect and process documentation feedback.
- **At each feature merge**: Confirm associated documentation (API, user guide, code examples, etc.) are updated and logged in [docs/MAINTENANCE_LOG.md](./docs/MAINTENANCE_LOG.md).
- **Before each version release**: Execute the pre-release documentation checklist and update [CHANGELOG.md](./CHANGELOG.md) and version notes.
- **Quarterly**: Conduct comprehensive documentation review, focusing on accuracy, timeliness, and link validity.

### Pre-Release Documentation Checklist
- [ ] All new features are documented in [API.en.md](./API.en.md)
- [ ] All API changes are recorded in [CHANGELOG.md](./CHANGELOG.md)
- [ ] User guide updated with new features
- [ ] Architecture documentation aligns with code
- [ ] New common questions added to [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- [ ] All documentation links verified with `scripts/validate-docs.sh`
- [ ] Code examples in documentation verified executable

### Documentation Ownership
| Document | Primary Owner | Backup Team |
|----------|------------|----------|
| README.en.md | Project Manager | Core Maintainers |
| API.en.md | Backend Technical Lead | Core Development Team |
| DEPLOYMENT.en.md | DevOps Lead | DevOps & Security Team |
| DEVELOPMENT.en.md | Development Team | Core Maintainers |
| USER_GUIDE.en.md | Product / Documentation Team | Technical Support Team |
| ARCHITECTURE.en.md | Technical Architect | Core Development Team |
| TROUBLESHOOTING.md | Technical Support Team | DevOps Team |
| CONTRIBUTING.md | Project Lead | Core Maintainers |
| SECURITY.md | Security Officer | DevOps & Security Team |
| CHANGELOG.md | Project Manager | Release Manager |

### Automation Guards
- PR template includes "documentation checklist" to confirm each item before merging.
- [scripts/validate-docs.sh](./scripts/validate-docs.sh) validates internal links, CHANGELOG format, API documentation consistency, and Python code syntax in Markdown.
- `.github/workflows/documentation-guardrails.yml` enforces in PRs: code changes must have documentation updates, API changes must sync to API.md, and CHANGELOG must be updated.

### Documentation Version Management and Records
- Release documentation version information in [CHANGELOG.md](./CHANGELOG.md) with old versions moved to `docs/versions/` when necessary.
- All documentation maintenance activities must be logged in [docs/MAINTENANCE_LOG.md](./docs/MAINTENANCE_LOG.md) for tracking responsibility and update time.
- Deprecated or breaking changes must be marked with deprecation notice and migration guide in relevant documents.

### Feedback Channels and Quality Metrics
- Feedback channels: GitHub Issues tagged with `documentation`, PR comments, and email [7780102@qq.com](mailto:7780102@qq.com).
- Quality metrics: Track documentation update frequency, user feedback volume, documentation accuracy rate (error report count), and coverage rate (whether affected features have documentation).
- Documentation contribution guidelines and templates are available in [CONTRIBUTING.md](./CONTRIBUTING.md) "Documentation Contribution" section.

---

## 🎯 Quick Command Reference

### Development Commands

```bash
# Complete installation
make install

# Start development services
make dev-backend      # Start backend (port 8000)
make dev-frontend     # Start frontend (port 3000)

# Code checks
make lint             # Code standard checks
make format           # Code formatting
make typecheck        # Type checking (mypy + tsc)

# Testing
make test             # Backend pytest + frontend vitest
make test-backend     # Backend tests only
make test-frontend    # Frontend tests only
```

### Deployment Commands

```bash
# Using capdf command (after installation)
capdf up              # Start services
capdf down            # Stop services
capdf logs -f         # View logs
capdf backup          # Create backup
capdf restore         # Restore from backup

# Using deploy.sh script
./deploy.sh up
./deploy.sh down
./deploy.sh logs
./deploy.sh backup
./deploy.sh restore
```

---

## 💡 Next Steps

- **New to ca-pdf?** Start with the [User Guide](./USER_GUIDE.en.md)
- **Need to deploy?** Follow [Deployment Guide](./DEPLOYMENT.en.md)
- **Developing a feature?** Read [Development Guide](./DEVELOPMENT.en.md)
- **Integrating with ca-pdf?** Check [API Documentation](./API.en.md)
- **Ran into issues?** Refer to [Troubleshooting](./TROUBLESHOOTING.md)

---

**Last Updated**: 2024
**Version**: 1.0
