# Architecture Guide

> **Status**: System design and architecture reference
> **Target Audience**: Architects and senior developers
> **Last Updated**: 2024

This guide provides an overview of the ca-pdf system architecture. For detailed technical specifications and design decisions, please refer to the [Complete Architecture Guide (Chinese)](../zh/ARCHITECTURE.md).

## System Overview

ca-pdf is a three-tier architecture consisting of:

### Layers

```
┌─────────────────────────────┐
│    Frontend (React)         │  - Web UI
│  - Browser-based            │  - User interfaces
│  - TypeScript               │  - Real-time updates
└──────────────┬──────────────┘
               │ REST API
┌──────────────▼──────────────┐
│    Backend (FastAPI)        │  - API endpoints
│  - Business logic           │  - Authentication
│  - Database operations      │  - PDF signing
│  - CA operations            │
└──────────────┬──────────────┘
               │ SQL
┌──────────────▼──────────────┐
│    Database (PostgreSQL)    │  - Persistent storage
│  - Certificates             │  - User data
│  - Documents                │  - Audit logs
│  - Key material             │
└─────────────────────────────┘
```

## Frontend Architecture

### Technology Stack

- **Framework**: React 18
- **Language**: TypeScript
- **UI Library**: Material-UI (MUI)
- **State Management**: Redux Toolkit
- **HTTP Client**: Axios
- **Build Tool**: Vite
- **Package Manager**: npm

### Key Components

1. **Authentication Module**
   - Login and logout flows
   - JWT token management
   - Session handling

2. **Certificate Management**
   - Certificate browser
   - Request creation
   - Certificate details view

3. **Document Management**
   - File upload
   - Signing interface
   - Verification viewer

4. **User Management**
   - User list
   - Profile management
   - Password change

### Directory Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   ├── pages/          # Page components
│   ├── store/          # Redux store
│   ├── api/            # API client
│   ├── types/          # TypeScript types
│   ├── utils/          # Utility functions
│   ├── hooks/          # Custom hooks
│   └── App.tsx         # Main app
├── public/             # Static assets
└── package.json
```

## Backend Architecture

### Technology Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: SQLAlchemy ORM with async support
- **Database Server**: PostgreSQL 14+
- **Authentication**: JWT with bcrypt
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest with asyncio
- **Validation**: Pydantic

### Core Modules

1. **Authentication** (`app/api/auth.py`)
   - User login/logout
   - JWT token generation
   - Password management

2. **Certificate Authority** (`app/api/ca.py`)
   - Certificate generation
   - Certificate validation
   - Revocation management

3. **PDF Operations** (`app/api/pdf.py`)
   - Document upload
   - PDF signing
   - Signature verification

4. **User Management** (`app/api/users.py`)
   - User CRUD operations
   - Role assignment
   - Permission management

5. **Audit** (`app/api/audit.py`)
   - Operation logging
   - Audit trail access
   - Compliance reporting

### Directory Structure

```
backend/
├── app/
│   ├── core/           # Core utilities
│   │   ├── config.py   # Configuration
│   │   ├── security.py # Security functions
│   │   └── deps.py     # Dependencies
│   ├── models/         # Database models
│   ├── schemas/        # Pydantic schemas
│   ├── api/            # API endpoints
│   ├── db/             # Database utilities
│   └── main.py         # App entry point
├── alembic/            # Database migrations
├── tests/              # Test suite
└── pyproject.toml      # Dependencies
```

## Database Schema

### Key Tables

1. **users**
   - User accounts
   - Hashed passwords
   - Role assignments

2. **certificates**
   - CA certificates
   - User certificates
   - Certificate chains

3. **documents**
   - PDF documents
   - Metadata
   - Signatures

4. **audit_logs**
   - Operation records
   - Timestamps
   - User information

5. **keys**
   - Encryption keys
   - Key rotation history
   - Master key information

### Entity Relationships

```
users
├── certificates (1:many)
├── documents (1:many)
└── audit_logs (1:many)

certificates
├── documents (1:many)
└── signatures (1:many)

documents
├── signatures (1:many)
└── audit_logs (1:many)
```

## API Design

### REST Principles

- Use standard HTTP methods (GET, POST, PUT, DELETE)
- Consistent resource naming (/api/v1/resource)
- Standard status codes
- JSON request/response format

### Versioning

Current version: **v1**

All endpoints use `/api/v1/` prefix.

### Authentication

JWT tokens in Authorization header:

```
Authorization: Bearer <JWT_TOKEN>
```

Token includes:
- User ID
- User role
- Expiration time
- Issued at time

### Error Handling

Standard error response:

```json
{
  "detail": "Error description",
  "code": "ERROR_CODE"
}
```

## Security Architecture

### Authentication Flow

```
1. User submits credentials
2. Backend validates credentials
3. Backend generates JWT token
4. Frontend stores token in memory
5. Frontend includes token in API requests
6. Backend validates token
7. Request proceeds or returns 401
```

### Data Protection

1. **Encryption at Rest**
   - Database encryption enabled
   - Sensitive fields encrypted
   - Master key derived from environment

2. **Encryption in Transit**
   - HTTPS/TLS for all communications
   - Certificate pinning supported
   - Strong cipher suites

3. **Key Management**
   - Master key encrypted and stored securely
   - Key rotation support
   - Audit logging for key operations

## Performance Architecture

### Caching Strategy

1. **Frontend Cache**
   - LocalStorage for tokens
   - Redux state management
   - In-memory component cache

2. **Backend Cache**
   - Redis for session cache
   - Database query result caching
   - JWT validation cache

### Database Optimization

1. **Indexing**
   - Indexed frequently queried columns
   - Composite indexes for common queries
   - Foreign key indexes

2. **Connection Pooling**
   - Configured connection pool size
   - Connection timeout settings
   - Automatic reconnection

3. **Query Optimization**
   - Pagination for large result sets
   - Select specific columns
   - Eager loading relationships

## Deployment Architecture

### Docker Containers

1. **Frontend Container**
   - Nginx web server
   - React application
   - Static asset serving

2. **Backend Container**
   - FastAPI application
   - Uvicorn ASGI server
   - Multiple worker processes

3. **Database Container**
   - PostgreSQL server
   - Volume mounts for persistence
   - Backup scripts

4. **Redis Container** (optional)
   - Session cache
   - Rate limiting
   - Background jobs

### Orchestration

#### Docker Compose
- Local development
- Small production deployments
- Easy setup and teardown

#### Kubernetes
- Scalable production deployments
- High availability
- Auto-scaling capabilities

## Integration Points

### External Services

1. **Time Stamp Authority (TSA)**
   - RFC 3161 compliant
   - Certificate validation
   - Response handling

2. **Email Service** (optional)
   - Notification delivery
   - Template rendering
   - Delivery tracking

3. **Logging Service** (optional)
   - Centralized logging
   - Log aggregation
   - Analysis tools

## Scalability Considerations

### Horizontal Scaling

- Stateless API servers (multiple instances)
- Load balancer distribution
- Shared database connection pool

### Vertical Scaling

- Increase CPU/memory allocation
- Database optimization
- Caching layer improvements

## Monitoring and Observability

### Metrics

- API response times
- Error rates
- Database query performance
- Resource utilization

### Logging

- Application logs (stdout/stderr)
- Access logs (HTTP requests)
- Error logs (exceptions)
- Audit logs (operations)

### Health Checks

- API health endpoint
- Database connectivity check
- Service dependency verification

## For Complete Details

For comprehensive architecture documentation including:
- Detailed system design diagrams
- Database schema documentation
- API endpoint specifications
- Security architecture details
- Performance characteristics
- Scalability strategies

Please refer to the [Complete Architecture Guide (Chinese)](../zh/ARCHITECTURE.md).

## Additional Resources

- [Development Guide](./DEVELOPMENT.md) - Development setup and guidelines
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [API Documentation](./API.md) - API reference
- [Security Guide](./SECURITY.md) - Security considerations

---

**Last updated**: 2024
