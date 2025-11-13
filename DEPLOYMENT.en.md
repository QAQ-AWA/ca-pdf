# ca-pdf Deployment Guide

> 📖 **Documentation Navigation**: [README](./README.en.md) · [Documentation Index](./DOCUMENTATION.md) · [Security Guide](./SECURITY.md) · [Troubleshooting](./TROUBLESHOOTING.md)
> 🎯 **Target Audience**: DevOps Engineers / Administrators
> ⏱️ **Estimated Reading Time**: 40 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This document provides a complete deployment and operations guide. For basic project overview, see [README.en.md](./README.en.md); for security hardening strategies, see [SECURITY.md](./SECURITY.md). For deployment issues, first check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

This is the complete deployment guide for ca-pdf, covering local development environment, Docker Compose deployment, and production environment configuration.

## 📋 Deployment Overview

### Supported Deployment Methods

| Method | Use Case | Difficulty | Data Persistence |
|--------|----------|-----------|------------------|
| **Local Development** | Local development & debugging | ⭐ | SQLite file |
| **Docker Compose** | Testing, demos, small-scale deployment | ⭐⭐ | PostgreSQL container volume |
| **Production** | Enterprise deployment | ⭐⭐⭐ | External PostgreSQL + backup |

### System Requirements

#### Minimum Configuration
- **Operating System**: Linux (Ubuntu 22.04+ recommended) / macOS / Windows (WSL2)
- **CPU**: 2 cores or more
- **Memory**: 4GB RAM (8GB+ recommended)
- **Disk**: 10GB available space (50GB+ recommended for production)
- **Network**: Stable internet connection (for pulling images and dependencies)

#### Recommended Configuration (Production)
- **Operating System**: Ubuntu 22.04 LTS
- **CPU**: 4 cores or more
- **Memory**: 16GB RAM
- **Disk**: 100GB SSD storage
- **Database**: PostgreSQL 12+ on separate server

### Network Requirements

#### Ports to Open

| Port | Service | Description |
|------|---------|-------------|
| **80** | HTTP | HTTP traffic for frontend and backend |
| **443** | HTTPS | HTTPS traffic for frontend and backend (recommended for production) |
| **5432** | PostgreSQL | Database access (internal network only) |
| **8000** | Backend API | Backend development debugging (optional) |
| **3000** | Frontend Dev | Frontend dev server (development only) |

#### Firewall Configuration Example (Ubuntu)
```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow specific IP to access database (if separate DB server)
sudo ufw allow from 10.0.0.0/24 to any port 5432 proto tcp
```

---

## 🖥️ Local Development Deployment

### Prerequisites

- **Python 3.11+** and Poetry
- **Node.js 16+** and npm
- **PostgreSQL 12+** or SQLite (recommended for development)
- **Docker** and **Docker Compose** (optional, for quick PostgreSQL startup)

### Complete Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
```

#### 2. Install Dependencies

```bash
# Complete installation (backend and frontend)
make install

# Or install separately
cd backend && poetry install
cd ../frontend && npm install
```

#### 3. Configure Environment Variables

```bash
# Copy example configuration files
cp .env.example .env

# Edit .env file and configure necessary variables
# Generate secure keys
openssl rand -base64 32  # for SECRET_KEY
openssl rand -base64 32  # for ENCRYPTED_STORAGE_MASTER_KEY
```

Example .env configuration (local development):
```bash
# Application configuration
APP_NAME=ca-pdf
API_V1_PREFIX=/api/v1
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# Database configuration (SQLite recommended for local development)
DATABASE_URL=sqlite+aiosqlite:///./test.db

# Security configuration
SECRET_KEY=your-generated-secret-key-here
ENCRYPTED_STORAGE_MASTER_KEY=your-fernet-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=4320

# CORS configuration (JSON format)
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Admin configuration
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SecurePassword123

# File limits
PDF_MAX_BYTES=52428800
PDF_BATCH_MAX_COUNT=10
SEAL_IMAGE_MAX_BYTES=1048576

# Frontend configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=ca-pdf
```

#### 4. Initialize Database

##### Using SQLite (Recommended for Local Development)

```bash
cd backend

# Create database and run migrations
poetry run alembic upgrade head

# Verify migration status
poetry run alembic current
```

##### Using PostgreSQL (Local)

First start PostgreSQL:

```bash
# Quick start PostgreSQL with Docker
docker run --name ca-pdf-db -e POSTGRES_DB=app_db \
  -e POSTGRES_USER=app_user -e POSTGRES_PASSWORD=app_password \
  -p 5432:5432 -d postgres:16

# Configure DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://app_user:app_password@localhost:5432/app_db
```

Then run migrations:

```bash
cd backend
poetry run alembic upgrade head
```

#### 5. Start Application

Run these commands in different terminal windows:

```bash
# Terminal 1: Start backend API (with auto-reload)
make dev-backend

# Terminal 2: Start frontend dev server (Vite)
make dev-frontend
```

#### 6. First Access

- **Frontend Application**: http://localhost:3000
- **Backend API Documentation**: http://localhost:8000/docs
- **Backend Health Check**: http://localhost:8000/health

Use `ADMIN_EMAIL` and `ADMIN_PASSWORD` configured in .env to login.

#### 7. Initial Setup

After first login:

1. Go to "Certificate Management" page
2. Click "Generate Root CA"
3. Select key algorithm (RSA-4096 or EC-P256) and validity period
4. Click "Generate" to complete root CA creation

After that you can begin signing and verification operations.

---

## 🐳 Docker Compose Deployment

### One-Command Installation & Menu-Based Operations

ca-pdf provides `scripts/install.sh` installer for completing dependency preparation and first-time deployment with a single command on a fresh host:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
```

Installer capabilities overview:

1. **Automatic Environment Detection**: Verify Bash version, Docker/Compose availability, check ports 80/443, memory and disk space requirements.
2. **Automatic Dependency Installation**: Identify Ubuntu/Debian, CentOS/Alma/Rocky, Fedora, openSUSE, Arch and other distributions; automatically install curl, git, jq, openssl, docker, docker compose v2 and other packages, attempt sudo if necessary.
3. **Secure Configuration Generation**: Download latest `.env.example`, `.env.docker.example`, `docker-compose.yml`, Traefik configuration templates; generate `.env`/`.env.docker` with strong random keys using `openssl rand -hex 32`.
4. **Multi-Mode Certificate Support**: Production mode uses Let's Encrypt by default with automatic ACME configuration; local mode generates `localtest.me` self-signed certificates.
5. **Idempotent Deployment**: Create or update Docker Compose stack, wait for health checks to complete, then automatically run Alembic migrations; logs saved to `logs/installer-YYYYMMDD.log`.
6. **Menu-Based Management**: After installation, register `capdf` command in `/usr/local/bin` for interactive menu to execute installation, upgrade, backup, restore, self-update operations.

After installation, run directly:

```bash
capdf menu
```

Common subcommands:

```bash
capdf install      # Re-enter installation wizard
capdf up           # Build and start (or upgrade) all services
capdf down         # Stop services, preserve data volumes
capdf down --clean # Stop and remove containers & data volumes
capdf logs -f      # View real-time logs for all services
capdf backup       # Export database + configuration backup
capdf restore      # Restore from backup
capdf doctor       # Health check (ports, resources, database connection, etc.)
capdf self-update  # Pull latest script from remote repository
```

> ℹ️ For offline or CI environments, you can still use `scripts/deploy.sh` / `./deploy.sh` in the repository root; subcommands match `capdf` but dependencies must be manually satisfied.

### Environment Preparation

1. **Install Docker** (version 23+) and **Docker Compose** (V2)
2. **Prepare environment files**

```bash
cp .env.example .env
cp .env.docker.example .env.docker
```

### Configuration Details

#### docker-compose.yml Services

| Service | Image | Description |
|---------|-------|-------------|
| **traefik** | traefik:v3.1 | Reverse proxy, handles SSL/TLS and routing |
| **db** | postgres:16 | PostgreSQL database |
| **backend** | custom build | FastAPI backend application |
| **frontend** | custom build | React frontend application |

### Quick Start

```bash
# One-click startup of full stack (all services)
capdf up

# Check container status
capdf status

# View real-time logs
capdf logs -f

# View specific service logs
capdf logs backend
capdf logs frontend
capdf logs db
```

### Build Images

```bash
# Automatically build images on first startup
capdf up

# Rebuild images (without updating running containers)
docker compose build

# Force rebuild and restart
docker compose up -d --build
```

### View Logs

```bash
# View all logs in real-time
capdf logs -f

# View last 100 lines of specific service logs
capdf logs backend --tail 100

# View logs from specific time
docker compose logs --since 10m backend
```

### Stop and Cleanup

```bash
# Stop all containers (preserve data volumes)
capdf down

# Stop and remove all containers and data volumes (use with caution!)
capdf down --clean

# Restart application (after updates)
capdf restart
```

### Data Backup

```bash
# Backup PostgreSQL data
docker compose exec db pg_dump -U app_user -d app_db > backup-$(date +%Y%m%d).sql

# Backup Traefik SSL certificates
docker compose exec traefik cat /letsencrypt/acme.json > acme-$(date +%Y%m%d).json

# Backup application data volume
docker run --rm -v ca-pdf_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-data-$(date +%Y%m%d).tar.gz -C /data .
```

---

## 🔐 Environment Variable Configuration

### Key Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| **DATABASE_URL** | String | Database connection string (PostgreSQL or SQLite) | `postgresql+asyncpg://user:pass@host:5432/db` |
| **ENCRYPTED_STORAGE_MASTER_KEY** | String | Master key for encrypted storage (Fernet format, required) | `openssl rand -base64 32` |
| **SECRET_KEY** | String | JWT signing key | `openssl rand -base64 32` |
| **ADMIN_EMAIL** | Email | Admin email auto-created on first startup | `admin@company.com` |
| **ADMIN_PASSWORD** | String | Admin password auto-created on first startup | `SecurePass123!` |
| **BACKEND_CORS_ORIGINS** | JSON | CORS whitelist (**must be JSON format**) | `["https://example.com"]` |
| **ACCESS_TOKEN_EXPIRE_MINUTES** | Int | Access Token expiration time | 15 |
| **REFRESH_TOKEN_EXPIRE_MINUTES** | Int | Refresh Token expiration time (minutes) | 4320 |
| **PDF_MAX_BYTES** | Int | Maximum PDF file size (bytes, default 50MB) | 52428800 |
| **SEAL_IMAGE_MAX_BYTES** | Int | Maximum corporate seal file size (default 1MB) | 1048576 |
| **TSA_URL** | String | Timestamp service URL (optional) | `https://freetsa.org/tsr` |
| **BACKEND_DOMAIN** | String | Backend API domain (Traefik uses) | `api.company.com` |
| **FRONTEND_DOMAIN** | String | Frontend application domain (Traefik uses) | `app.company.com` |
| **TRAEFIK_ACME_EMAIL** | Email | Let's Encrypt certificate email | `admin@company.com` |

### Generate Encryption Keys

```bash
# Generate Fernet key (recommended for ENCRYPTED_STORAGE_MASTER_KEY)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate random key (for SECRET_KEY)
openssl rand -base64 32

# Python method
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### .env File Example

```bash
# Basic configuration
APP_NAME=ca-pdf
API_V1_PREFIX=/api/v1

# Database configuration
DATABASE_URL=postgresql+asyncpg://app_user:secure_password@db:5432/app_db

# Security configuration
SECRET_KEY=your-secret-key-from-openssl-rand
ENCRYPTED_STORAGE_MASTER_KEY=your-fernet-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=4320

# CORS configuration (JSON format)
BACKEND_CORS_ORIGINS=["https://app.company.com"]

# Admin configuration
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=SecureAdminPassword123!

# File limits
PDF_MAX_BYTES=52428800
SEAL_IMAGE_MAX_BYTES=1048576

# Traefik configuration
BACKEND_DOMAIN=api.company.com
FRONTEND_DOMAIN=app.company.com
TRAEFIK_ACME_EMAIL=admin@company.com

# Frontend configuration
VITE_API_BASE_URL=https://api.company.com
VITE_APP_NAME=CA PDF Signature
```

---

## 💾 Database Configuration

### PostgreSQL Initialization

#### Local PostgreSQL Installation (Ubuntu)

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE USER app_user WITH PASSWORD 'secure_password';
CREATE DATABASE app_db OWNER app_user;
GRANT ALL PRIVILEGES ON DATABASE app_db TO app_user;
EOF

# Verify connection
psql -h localhost -U app_user -d app_db -c "SELECT version();"
```

#### Cloud-Hosted PostgreSQL (Recommended for Production)

- **AWS RDS**: https://aws.amazon.com/rds/postgresql/
- **Azure Database**: https://azure.microsoft.com/services/postgresql/
- **Google Cloud SQL**: https://cloud.google.com/sql/docs/postgres
- **DigitalOcean Managed Database**: https://www.digitalocean.com/products/managed-databases/

### Run Alembic Migrations

> ♻️ **Automated Container Migrations**: As of November 2024, backend containers automatically execute `backend/scripts/prestart.sh` on startup, performing:
> - Database connection polling with exponential backoff (initial 1s, max 30 retries)
> - Up to 3 retry attempts for `alembic upgrade head` to handle transient network or locking issues
> - Gunicorn only starts after successful migration, ensuring service runs on the latest schema
>
> If automated migration fails, the container exits immediately with detailed logs accessible via `docker compose logs backend`.

#### Manual Execution (Development / Debugging)

For local development or troubleshooting, you can still run migrations manually:

```bash
cd backend

# Upgrade to latest version
poetry run alembic upgrade head

# View current version
poetry run alembic current

# View migration history
poetry run alembic history --verbose

# Downgrade to specific version (use with caution)
poetry run alembic downgrade -1
```

### Data Backup Strategy

```bash
# Create backup directory
mkdir -p /var/backups/ca-pdf

# Complete backup script
#!/bin/bash
BACKUP_DIR="/var/backups/ca-pdf"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="app_db"
DB_USER="app_user"

# Backup database
pg_dump -h localhost -U ${DB_USER} -d ${DB_NAME} | \
  gzip > ${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz

# Keep backups from last 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
```

#### Scheduled Backup (Cron)

```bash
# Run backup every day at 2 AM
0 2 * * * /var/backups/ca-pdf/backup.sh

# Edit crontab
crontab -e
```

### Data Recovery Steps

```bash
# List available backups
ls -lh /var/backups/ca-pdf/

# Restore from backup
gunzip < /var/backups/ca-pdf/app_db_20240115_000000.sql.gz | \
  psql -h localhost -U app_user -d app_db

# Verify restore
psql -h localhost -U app_user -d app_db -c "SELECT COUNT(*) FROM users;"
```

---

## 🔄 Upgrade and Maintenance

### Update Services

```bash
# Pull latest image
docker compose pull

# Rebuild and restart services
capdf up --build

# Verify running version
curl http://localhost:8000/api/v1/health | jq '.version'
```

### Database Migration After Updates

```bash
cd backend

# Check if migrations are needed
poetry run alembic current

# Apply pending migrations
poetry run alembic upgrade head

# Verify migration status
poetry run alembic history | head -20
```

### Monitor Disk Space

```bash
# Check disk usage
df -h

# Clean up old Docker images
docker image prune -a --force

# Clean up unused volumes
docker volume prune
```

---

## 📊 Monitoring and Logging

### View Application Logs

```bash
# All services
capdf logs -f

# Specific service
capdf logs backend -f --tail 50

# With timestamp
docker compose logs --timestamps backend
```

### System Resources

```bash
# CPU and memory usage
docker stats

# Check specific container
docker stats ca-pdf_backend_1
```

### Database Connections

```bash
# Check current connections
docker compose exec db psql -U app_user -d app_db -c \
  "SELECT datname, usename, count(*) FROM pg_stat_activity GROUP BY datname, usename;"
```

---

## 🆘 Troubleshooting Deployment

### Port Already in Use

```bash
# Find process using port 80
lsof -i :80

# Kill process (if safe to do so)
kill -9 <PID>

# Or use different port
# Update BACKEND_DOMAIN and FRONTEND_DOMAIN in .env
```

### Database Connection Error

```bash
# Test PostgreSQL connection
docker compose exec backend bash -c \
  'psql $DATABASE_URL -c "SELECT 1;"'

# Check database logs
docker compose logs db
```

### Out of Memory

```bash
# Check Docker resources
docker system df

# Increase Docker memory limit (change in Docker Desktop settings)
# Or in docker-compose.yml add:
# services:
#   backend:
#     mem_limit: 1g
```

---

## 🚀 Production Deployment Checklist

Before deploying to production:

- [ ] Use Let's Encrypt certificates (automatic via Traefik)
- [ ] Configure strong SECRET_KEY and ENCRYPTED_STORAGE_MASTER_KEY
- [ ] Set up PostgreSQL on separate server or managed service
- [ ] Configure automated backups (daily recommended)
- [ ] Enable monitoring and alerting
- [ ] Set BACKEND_CORS_ORIGINS to production domain only
- [ ] Disable debug mode (DEBUG=False in .env)
- [ ] Use strong admin password
- [ ] Configure firewall rules
- [ ] Enable HTTPS redirect
- [ ] Set up log aggregation
- [ ] Document runbook for common operations

---

**Last Updated**: 2024
**Version**: 1.0
