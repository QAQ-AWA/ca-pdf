# API Documentation

> **Status**: Comprehensive API reference for ca-pdf REST endpoints
> **Target Audience**: Developers and integration specialists
> **Last Updated**: 2024

For the complete English API documentation, please visit the **[Chinese version](../zh/API.md)** which contains detailed endpoint specifications, request/response examples, authentication details, and error handling guides.

## Quick Overview

ca-pdf provides a RESTful API for managing:

- **Authentication**: User login, token management
- **Certificates**: Certificate lifecycle management
- **PDF Operations**: Document upload and signing
- **Users**: User and role management
- **Audit**: Audit log access

## API Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except login) require JWT authentication:

```bash
Authorization: Bearer <JWT_TOKEN>
```

## Quick Examples

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### List Certificates

```bash
curl -X GET http://localhost:8000/api/v1/ca/certificates \
  -H "Authorization: Bearer <TOKEN>"
```

### Sign a PDF

```bash
curl -X POST http://localhost:8000/api/v1/pdf/sign \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@document.pdf" \
  -F "cert_id=1"
```

## Interactive API Documentation

Access the interactive Swagger UI at:

```
http://localhost:8000/docs
```

Or OpenAPI JSON schema at:

```
http://localhost:8000/openapi.json
```

## Main Endpoint Categories

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Get current user info
- `POST /auth/change-password` - Change password

### Certificate Endpoints
- `GET /ca/certificates` - List certificates
- `POST /ca/certificates` - Create certificate
- `GET /ca/certificates/{id}` - Get certificate details
- `PUT /ca/certificates/{id}` - Update certificate
- `DELETE /ca/certificates/{id}` - Delete certificate
- `POST /ca/certificates/{id}/export` - Export certificate
- `GET /ca/certificates/{id}/chain` - Get certificate chain

### PDF Signing Endpoints
- `POST /pdf/sign` - Sign PDF
- `GET /pdf/documents` - List documents
- `GET /pdf/documents/{id}` - Get document details
- `POST /pdf/verify` - Verify signature
- `GET /pdf/documents/{id}/download` - Download document

### User Management Endpoints
- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user
- `POST /users/{id}/change-role` - Change user role

### Audit Endpoints
- `GET /audit/logs` - Get audit logs

## Error Handling

All endpoints return JSON with standard HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error Response Format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

## Rate Limiting

The API implements rate limiting on public endpoints:

- Login endpoint: 5 requests per minute per IP
- Other endpoints: 100 requests per minute per user

## Pagination

List endpoints support pagination:

```bash
GET /api/v1/ca/certificates?page=1&limit=20
```

Query Parameters:
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

Response:

```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

## Content Types

- Request: `application/json` (or `multipart/form-data` for file uploads)
- Response: `application/json`

## API Versioning

Current API version: `v1`

The API uses URL versioning. Future versions will be available at `/api/v2`, etc.

## For More Details

For complete endpoint specifications with detailed request/response bodies, authentication flows, error scenarios, and integration examples, please refer to the [Chinese API documentation](../zh/API.md).

Alternatively, you can access the interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Last updated**: 2024
