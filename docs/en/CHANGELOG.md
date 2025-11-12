# Changelog

All notable changes to ca-pdf are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added
- Multilingual documentation site (Chinese and English)
- MkDocs Material-based documentation platform
- GitHub Pages documentation deployment

### Changed
- Documentation reorganized into `docs/zh/` and `docs/en/` directories

### Planned
- Multi-factor authentication (2FA/TOTP)
- Hardware security module (HSM) support
- Advanced certificate templates
- Batch signing operations
- Mobile signing application

## [0.1.0] - 2024-01-15

### Added

#### Core Features
- Self-hosted Certificate Authority (CA) system
- X.509 certificate generation and management
- PDF digital signature support
- Enterprise audit logging
- Role-based access control (RBAC)
- JWT-based authentication
- Multi-user support
- Web dashboard

#### Backend
- FastAPI REST API
- PostgreSQL database with async support
- SQLAlchemy ORM
- Alembic database migrations
- JWT authentication with bcrypt
- CORS support
- Comprehensive API documentation

#### Frontend
- React 18 application
- TypeScript support
- Material-UI component library
- Redux Toolkit state management
- Responsive design
- Dark/light theme support

#### Certificate Management
- Create CA root certificates
- Issue end-entity certificates
- Certificate validation
- Certificate chain management
- Certificate revocation support
- Certificate status tracking

#### Document Management
- PDF upload and management
- Digital signature application
- Signature verification
- Document download
- Batch processing support

#### Security Features
- Encrypted key storage (AES-256)
- HTTPS/TLS support
- Encrypted database connections
- Input validation
- Rate limiting
- CORS configuration
- Audit trail logging
- Tamper detection

#### Deployment
- Docker Compose setup
- PostgreSQL integration
- Redis caching (optional)
- Traefik reverse proxy support
- Health check endpoints
- Environment variable configuration

#### Documentation
- Comprehensive README
- User Guide (中文/English)
- Deployment Guide (中文/English)
- Development Guide (中文/English)
- Architecture documentation
- API documentation
- Troubleshooting guide
- Security guide
- Contributing guidelines

#### Testing
- Unit tests for backend services
- Integration tests for APIs
- Frontend component tests
- Database migration tests
- 80%+ code coverage

#### Operations
- Docker deployment
- Backup and recovery procedures
- Monitoring and logging
- Performance metrics
- System health checks

### Security

- Built-in encryption for sensitive data
- Secure password hashing (bcrypt)
- JWT token-based authentication
- Role-based access control
- Comprehensive audit logging
- Input validation and sanitization
- XSS and CSRF protection
- SQL injection prevention

### Documentation

- Comprehensive English documentation
- Chinese documentation (繁體中文)
- Code examples in multiple languages
- Interactive API documentation
- Troubleshooting guides
- Security best practices
- Deployment procedures

## Future Releases

### v0.2.0 (Q2 2024)

Planned features:

- **Certificate Templates**: Pre-configured certificate templates for common use cases
- **Batch Signing**: Sign multiple documents in one operation
- **Certificate Chain Validation**: Full chain validation including intermediates
- **CRL/OCSP Support**: Certificate revocation list and online status protocol
- **Performance Optimization**: Database query optimization and caching improvements
- **Monitoring**: Prometheus metrics and monitoring integration

### v0.3.0 (Q3 2024)

Planned features:

- **Multi-Factor Authentication (MFA)**: TOTP and SMS support
- **SSO Integration**: OIDC/OAuth2 support
- **Advanced Audit**: Enhanced audit trail with advanced filtering
- **Compliance Reports**: GDPR and PCI-DSS compliance reports
- **API Rate Limiting**: Advanced rate limiting strategies
- **Webhooks**: Event-driven webhooks for integrations

### v0.4.0 (Q4 2024)

Planned features:

- **Hardware Security Module (HSM) Support**: SafeNet, Thales integration
- **Mobile Application**: iOS/Android signing app
- **Advanced Encryption**: Post-quantum cryptography preparation
- **Distributed Deployment**: Multi-region support
- **GraphQL API**: Alternative API interface
- **Performance Monitoring**: Advanced performance tracking

### v0.5.0 (2025)

Planned features:

- **Blockchain Integration**: Timestamping on blockchain
- **Advanced Analytics**: User behavior and usage analytics
- **Custom Workflows**: Visual workflow builder
- **Integration Marketplace**: Third-party integrations
- **Enterprise Features**: Advanced permission management

## Breaking Changes

### v0.1.0

No breaking changes (initial release).

## Deprecations

None yet.

## Known Issues

### Current Limitations

- **Database**: PostgreSQL 14+ required for production (SQLite for development)
- **Performance**: Signing operations are CPU-bound; scale horizontally for high throughput
- **Storage**: Encrypted key storage requires secure backup procedures
- **Browser**: Modern browser required (Chrome 90+, Firefox 88+, Safari 14+)

## Installation

### Latest Release

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
docker-compose up -d
```

### From Source

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf

# Backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Upgrade Guide

### From v0.0.x to v0.1.0

1. **Backup Database**: Always backup before upgrading
   ```bash
   pg_dump ca_pdf > backup.sql
   ```

2. **Update Code**:
   ```bash
   git pull origin main
   ```

3. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Restart Services**:
   ```bash
   docker-compose restart
   ```

5. **Verify Deployment**:
   ```bash
   curl http://localhost:8000/health
   ```

## Contributors

- Main development team at [QAQ-AWA](https://github.com/QAQ-AWA)
- Community contributors via GitHub

## License

This project is licensed under the MIT License. See [LICENSE](../LICENSE) file for details.

## Support

- 📧 Email: [7780102@qq.com](mailto:7780102@qq.com)
- 🐛 Issues: [GitHub Issues](https://github.com/QAQ-AWA/ca-pdf/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/QAQ-AWA/ca-pdf/discussions)
- 📖 Documentation: [GitHub Pages](https://qaq-awa.github.io/ca-pdf/)

## Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Timeline

| Version | Release Date | Status |
|---------|--------------|--------|
| 0.1.0 | 2024-01-15 | Current |
| 0.2.0 | Q2 2024 | Planned |
| 0.3.0 | Q3 2024 | Planned |
| 0.4.0 | Q4 2024 | Planned |
| 0.5.0 | 2025 | Planned |

---

**Last updated**: 2024-01-15

For the complete Chinese changelog, see [CHANGELOG (Chinese)](../zh/CHANGELOG.md).
