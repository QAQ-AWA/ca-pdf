# ca-pdf Documentation (English)

> **Language notice:** This page is the English companion to the primary Chinese documentation. Sections marked with ✅ contain translated highlights. For more detail, refer to the Chinese version until full translations are delivered.

## Project Overview

ca-pdf is a self-hostable digital signature platform that bundles a complete certificate authority (CA), timestamping support, and audit capabilities. Organizations can deploy it on-premises or in the cloud to keep signing workflows and cryptographic material fully under their control.

### Key Capabilities

- **Built-in Root CA**: Generate and manage RSA-4096 or EC-P256 certificate hierarchies.
- **End-to-end PDF Signing**: Visible and invisible signatures, bulk signing, and custom seal artwork.
- **Timestamping & LTV**: RFC3161 timestamp integration and long-term validation packaging.
- **Verification & Audit**: Signature validation, tamper detection, and immutable audit trails.
- **Role-based Access Control**: JWT + refresh tokens with administrator and user roles.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/QAQ-AWA/ca-pdf.git
   cd ca-pdf
   ```
2. **Copy environment templates**
   ```bash
   cp .env.example .env
   cp .env.docker.example .env.docker
   ```
3. **Launch with Docker Compose**
   ```bash
   ./deploy.sh up
   ```
4. **Access the stack**
   - Frontend: <https://app.localtest.me> (or <http://localhost:3000>)
   - API docs: <https://api.localtest.me/docs> (or <http://localhost:8000/docs>)

For detailed guidance, jump to the translated sections below.

## Documentation Map

| Topic | Status | Description |
|-------|--------|-------------|
| [User Guide](./USER_GUIDE.md) | ✅ | Core user journeys (issuing certificates, signing PDFs, troubleshooting basics). |
| [Deployment Guide](./DEPLOYMENT.md) | ✅ | Infrastructure checklist, environment variables, Docker Compose flow. |
| [Developer Guide](./DEVELOPMENT.md) | ✅ | Local development workflow, tooling, coding standards overview. |
| [Architecture Overview](./ARCHITECTURE.md) | ✅ | System components, data flows, and technology stack summary. |
| [API Reference](./API.md) | ✅ | REST endpoints grouped by area with request/response shapes. |
| [Security Guide](./SECURITY.md) | ✅ | Key management, security hardening, compliance reminders. |
| [Troubleshooting](./TROUBLESHOOTING.md) | ✅ | High-priority troubleshooting checklists and tips. |
| [Contributing](./CONTRIBUTING.md) | ✅ | Contribution workflow, review expectations, docs checklist. |
| [Changelog](./CHANGELOG.md) | ✅ | Release notes and documentation updates.

## Contact & Support

- GitHub repository: <https://github.com/QAQ-AWA/ca-pdf>
- Email: [7780102@qq.com](mailto:7780102@qq.com)
- Issue tracker: <https://github.com/QAQ-AWA/ca-pdf/issues>

> ℹ️ Need more detail? Use the language switcher in the navigation bar to jump to the Chinese source material until the full English translation is complete.
