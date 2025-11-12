# Deployment Guide

> **Status**: Complete deployment reference
> **Target Audience**: DevOps engineers and system administrators
> **Last Updated**: 2024

This page provides an overview of deployment options for ca-pdf. For the **complete English deployment documentation with detailed step-by-step instructions**, please continue reading below.

## Deployment Options

### Option 1: Docker Compose (Recommended)

The fastest way to get started with ca-pdf is using Docker Compose, which includes all necessary services.

**Prerequisites:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4 GB RAM minimum

**Quick Start:**

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
docker-compose up -d
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Services Included:**
- Backend API (FastAPI)
- Frontend (React)
- PostgreSQL Database
- Redis Cache

### Option 2: Kubernetes Deployment

For production environments requiring high availability and scalability.

**Prerequisites:**
- Kubernetes cluster 1.24+
- kubectl configured
- Docker registry access

**Key Components:**
- Frontend Deployment
- Backend Deployment with multiple replicas
- PostgreSQL StatefulSet
- Redis Deployment
- Ingress Controller

### Option 3: Manual Server Deployment

For organizations preferring traditional server deployments.

**Prerequisites:**
- Ubuntu 20.04 LTS or CentOS 8+
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- System access for installation

## Environment Variables

### Core Configuration

```bash
# Application
APP_ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@localhost/ca_pdf
ENCRYPTED_STORAGE_MASTER_KEY=your_secure_key_here

# JWT
JWT_SECRET_KEY=your_jwt_secret_key
JWT_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
```

### Database Setup

```bash
# PostgreSQL Connection
DATABASE_URL=postgresql://username:password@host:5432/ca_pdf

# For Development (SQLite)
DATABASE_URL=sqlite:///./ca_pdf.db
```

## Security Considerations

### SSL/TLS Configuration

Enable HTTPS in production:

```bash
# Using Traefik (Recommended)
TRAEFIK_ENTRYPOINT_HTTPS_ADDRESS=:443
TRAEFIK_SSL_CERTIFICATE_PATH=/path/to/cert.pem
TRAEFIK_SSL_KEY_PATH=/path/to/key.pem
```

### Master Key Encryption

The `ENCRYPTED_STORAGE_MASTER_KEY` must be:
- At least 32 characters long
- Strong and random
- Securely stored and backed up
- Changed only during maintenance windows

Generate a secure key:

```bash
openssl rand -hex 32
```

## Database Configuration

### PostgreSQL Setup

```bash
# Create database and user
createuser ca_pdf_user
createdb ca_pdf -O ca_pdf_user

# Setup connection
export DATABASE_URL=postgresql://ca_pdf_user:password@localhost/ca_pdf
```

### Run Migrations

```bash
alembic upgrade head
```

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -U ca_pdf_user ca_pdf > ca_pdf_backup.sql

# Automated daily backups with Docker
docker exec ca_pdf_db pg_dump -U postgres ca_pdf > /backups/ca_pdf_$(date +%Y%m%d).sql
```

### Key Material Backup

Always backup the encrypted storage master key:

```bash
# Store securely (not in git!)
cp .env .env.backup
chmod 600 .env.backup
```

## Production Deployment

### Using Docker Compose with Traefik

```bash
# Start with Traefik proxy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Performance Tuning

1. **Database Optimization**
   - Enable connection pooling
   - Tune PostgreSQL for your hardware
   - Set up regular VACUUM and ANALYZE

2. **Caching**
   - Enable Redis caching
   - Configure cache TTL appropriately

3. **Load Balancing**
   - Use Traefik or Nginx as reverse proxy
   - Enable gzip compression

## Monitoring and Logging

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/db
```

### Log Management

Logs are available via Docker:

```bash
# Backend logs
docker logs ca_pdf_backend -f

# Database logs
docker logs ca_pdf_db -f
```

## Upgrades and Updates

### Backup First

Always backup your data before upgrading:

```bash
docker-compose down
docker exec ca_pdf_db pg_dump -U postgres ca_pdf > backup.sql
```

### Upgrade Steps

```bash
# Pull latest code
git pull origin main

# Update containers
docker-compose pull
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose ps

# Verify credentials
echo $DATABASE_URL
```

**Port Already in Use**
```bash
# Change ports in docker-compose.yml or use:
docker-compose -p capdf_new up -d
```

**Out of Disk Space**
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

## For Complete Details

For comprehensive deployment instructions including:
- Step-by-step manual server setup
- Kubernetes manifest files and configuration
- Traefik reverse proxy setup
- SSL/TLS certificate configuration
- Performance tuning details
- Disaster recovery procedures
- Monitoring and alerting setup

Please refer to the [Complete Deployment Guide (Chinese)](../zh/DEPLOYMENT.md).

## Additional Resources

- [Security Guide](./SECURITY.md) - Security considerations and best practices
- [User Guide](./USER_GUIDE.md) - Post-deployment user guide
- [Troubleshooting](./TROUBLESHOOTING.md) - Solutions to common problems
- [Development Guide](./DEVELOPMENT.md) - For development deployments

---

**Last updated**: 2024
