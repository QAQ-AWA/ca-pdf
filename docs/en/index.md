# ca-pdf - English Documentation

> 📖 **Documentation Navigation**: [Documentation Index](./DOCUMENTATION.md) · [User Guide](./USER_GUIDE.md) · [Deployment Guide](./DEPLOYMENT.md) · [Development Guide](./DEVELOPMENT.md) · [API Documentation](./API.md)
> 🎯 **Applicable to**: All roles
> ⏱️ **Estimated Reading Time**: 15 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This document serves as the entry point for the ca-pdf project, providing an overview of the product value, quick start guide, and key features. For specialized topics, please refer to the "Documentation Navigation" section below.

---

ca-pdf is a self-hosted PDF digital signature platform with a built-in Certificate Authority (CA) system, timestamp service support, and enterprise-grade audit capabilities. It provides organizations with trustworthy digital signature infrastructure, supporting both local deployment and cloud deployment.

## 📚 Documentation Navigation

This index is the entry point for ca-pdf documentation. Please select the appropriate reading order based on your role and use the table below to quickly locate the information you need.

### Recommended Reading Paths

- 🆕 **New Users**: [README](./index.md) → [USER_GUIDE](./USER_GUIDE.md) → [TROUBLESHOOTING](./TROUBLESHOOTING.md)
- 👩‍💻 **Developers**: [README](./index.md) → [DEVELOPMENT](./DEVELOPMENT.md) → [ARCHITECTURE](./ARCHITECTURE.md) → [API](./API.md)
- 🛡️ **Administrators**: [README](./index.md) → [DEPLOYMENT](./DEPLOYMENT.md) → [SECURITY](./SECURITY.md) → [USER_GUIDE](./USER_GUIDE.md)
- 🤝 **Contributors**: [README](./index.md) → [CONTRIBUTING](./CONTRIBUTING.md) → [DEVELOPMENT](./DEVELOPMENT.md)

### Main Documentation Overview

| Document | Target Audience | One-Sentence Description |
|----------|-----------------|--------------------------|
| [DOCUMENTATION.md](./DOCUMENTATION.md) | All readers | Complete documentation map and topic index |
| [README](./index.md) | Everyone | Product overview, quick start, and navigation |
| [USER_GUIDE.md](./USER_GUIDE.md) | Business users | Certificate management and PDF signing workflows |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Developers | Local environment, code standards, and debugging |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architects | System design, tech stack, and component interaction |
| [API.md](./API.md) | Integration developers | REST API endpoints reference and examples |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | DevOps / Administrators | Deployment, environment variables, and operations |
| [SECURITY.md](./SECURITY.md) | Security officers | Key management, security policies, and compliance |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | All readers | Common issues and troubleshooting guides |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Contributors | Contribution process, code standards, and reviews |
| [CHANGELOG.md](./CHANGELOG.md) | Maintainers | Version history and release notes |

> 📌 Detailed tech stack version information is maintained only in [ARCHITECTURE.md](./ARCHITECTURE.md); environment variable configuration is centralized in [DEPLOYMENT.md](./DEPLOYMENT.md); quick start commands follow this README as the source of truth.

## 📌 Project Introduction

### Core Value Proposition

ca-pdf enables you to quickly establish an independent PDF digital signature system with complete control over your certificate system and signing workflow. No dependence on third-party service providers - your data and key materials are fully managed in your own infrastructure, making it ideal for enterprises requiring high customization and privacy protection.

### Key Features

- **Self-Hosted CA System**: Built-in X.509 certificate authority for issuing and managing digital certificates
- **PDF Digital Signatures**: Support for multiple signature types (PKCS#7, PDF signature) with timestamp validation
- **Enterprise Audit**: Complete audit trails for all operations with tamper-proof logging
- **Multi-User Support**: Role-based access control (RBAC) for managing users and permissions
- **REST API**: Comprehensive API for programmatic integration
- **Web Dashboard**: User-friendly web interface for certificate and document management
- **Timestamp Service**: Integration with RFC 3161 timestamp authorities for legal compliance
- **Database Flexibility**: Support for PostgreSQL and SQLite
- **Docker Deployment**: Ready-to-use Docker and Docker Compose configurations

## 🚀 Quick Start

### 1. Prerequisites

- Docker and Docker Compose (or Python 3.11+)
- PostgreSQL 14+ (or use SQLite for development)
- Node.js 18+ (for frontend development)

### 2. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf

# Start services with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 3. First Steps

1. Log in to the dashboard with default credentials
2. Create your first CA certificate
3. Issue a certificate to a user
4. Upload a PDF document and sign it
5. Verify the signature

For detailed setup instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## 🏗️ Architecture Overview

ca-pdf consists of three main components:

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (async) with SQLite support for testing
- **Authentication**: JWT-based with role-based access control
- **API**: RESTful endpoints for all operations

### Frontend
- **Framework**: React 18 with TypeScript
- **UI Components**: Material-UI (MUI)
- **State Management**: Redux Toolkit
- **Build Tool**: Vite

### Certificate Authority (CA)
- **Certificate Format**: X.509 v3
- **Signature Algorithm**: RSA-2048/4096, ECDSA
- **Key Storage**: Encrypted storage with AES-256

For more details, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## 📋 System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB
- **Network**: Standard internet connection

### Recommended
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 50 GB
- **Network**: Stable high-speed connection

## 🔒 Security

ca-pdf implements multiple security layers:

- **Encrypted Key Storage**: Master key encryption with AES-256
- **HTTPS/TLS**: All communications encrypted
- **Authentication**: JWT tokens with configurable expiration
- **Authorization**: Fine-grained role-based access control
- **Audit Logging**: Comprehensive operation audit trails
- **Input Validation**: Strict validation on all inputs

For security best practices, see [SECURITY.md](./SECURITY.md).

## 📈 Deployment Options

### Option 1: Docker Compose (Recommended for Quick Start)
- All-in-one setup with PostgreSQL and backend services
- Suitable for development and small production deployments
- Quick to set up and tear down

### Option 2: Kubernetes
- Scalable deployment for high-traffic environments
- Requires existing Kubernetes infrastructure
- Advanced load balancing and auto-scaling capabilities

### Option 3: Traditional Server Deployment
- Install on Ubuntu/CentOS servers
- More control over system configuration
- Suitable for organizations with existing DevOps practices

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions for each option.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:

- Contribution guidelines
- Development environment setup
- Code standards and best practices
- Pull request process
- Commit message format

## 📞 Support and Community

- **Issues & Bug Reports**: [GitHub Issues](https://github.com/QAQ-AWA/ca-pdf/issues)
- **Discussions**: [GitHub Discussions](https://github.com/QAQ-AWA/ca-pdf/discussions)
- **Email**: [7780102@qq.com](mailto:7780102@qq.com)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## 🗺️ Roadmap

Planned features for upcoming releases:

- **v0.2.0**: Advanced certificate templates and batch operations
- **v0.3.0**: Multi-factor authentication (MFA) support
- **v0.4.0**: Hardware security module (HSM) integration
- **v0.5.0**: Mobile app for document signing

For the complete roadmap, see [CHANGELOG.md](./CHANGELOG.md).

## 🙏 Acknowledgments

ca-pdf builds upon the work of many open-source projects:

- FastAPI for the web framework
- React for the frontend framework
- PostgreSQL for data storage
- OpenSSL for cryptographic operations
- MkDocs Material for documentation

## 📚 Additional Resources

- [API Documentation](./API.md) - Complete REST API reference
- [User Guide](./USER_GUIDE.md) - Step-by-step usage instructions
- [Development Guide](./DEVELOPMENT.md) - For developers and contributors
- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Solutions to common problems
- [Security Guide](./SECURITY.md) - Security best practices

---

Last updated: 2024
