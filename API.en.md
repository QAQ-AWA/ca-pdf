# ca-pdf API Documentation

> 📖 **Documentation Navigation**: [README](./README.en.md) · [Documentation Index](./DOCUMENTATION.md) · [Development Guide](./DEVELOPMENT.en.md) · [Troubleshooting](./TROUBLESHOOTING.md)
> 🎯 **Target Audience**: Backend / Integration Developers
> ⏱️ **Estimated Reading Time**: 45 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This document provides all REST API parameters, examples, and error codes for the ca-pdf platform. We recommend first reading [README.en.md](./README.en.md) for overall background, and preparing your development environment with [DEVELOPMENT.en.md](./DEVELOPMENT.en.md). For API troubleshooting, refer to [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

Complete API reference guide for the self-hosted PDF digital signature platform.

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication Module](#authentication-module)
3. [Certificate Management Module](#certificate-management-module)
4. [PDF Signing Module](#pdf-signing-module)
5. [User Management Module](#user-management-module)
6. [Audit Logging Module](#audit-logging-module)
7. [System Module](#system-module)
8. [Common Scenario Examples](#common-scenario-examples)
9. [Error Code Reference](#error-code-reference)

---

## API Overview

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication Method

All protected API endpoints require a JWT Token in the request header:

```
Authorization: Bearer <your_jwt_token>
```

### Request/Response Format

- All requests and responses use JSON format
- Error responses follow a standard error format (see [Error Handling](#standard-error-format))

### Standard Error Format

All API error responses follow this unified format:

```json
{
  "code": "ERROR_CODE",
  "message": "User-friendly error message",
  "detail": "Technical details (optional)",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/auth/login",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Authentication Module

### 1. POST /auth/login

User login to obtain access_token and refresh_token.

**Authentication Required**: None (public endpoint)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string(email) | ✓ | User email |
| password | string | ✓ | User password |

**Request Examples**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "securepassword123"
    }
)
print(response.json())
```

```typescript
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123'
  })
});
const data = await response.json();
console.log(data);
```

**Success Response (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401 Unauthorized)**

```json
{
  "code": "UNAUTHORIZED",
  "message": "Invalid credentials",
  "detail": null,
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/auth/login",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Common Errors**

- 401: Incorrect email or password
- 422: Invalid email format or empty password

---

### 2. POST /auth/logout

Logout and revoke the current Token.

**Authentication Required**: Bearer Token (required)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | ✓ | Refresh token obtained at login |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

**Success Response (200 OK)**

```json
{
  "detail": "Successfully logged out"
}
```

---

### 3. POST /auth/refresh

Token rotation: obtain a new access_token using refresh_token.

**Authentication Required**: None

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | ✓ | Refresh token obtained at login |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

**Success Response (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 4. GET /auth/me

Get current authenticated user's personal information.

**Authentication Required**: Bearer Token (required)

**Request Example**

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**Success Response (200 OK)**

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### 5. GET /auth/admin/ping

Admin verification endpoint (admin access only).

**Authentication Required**: Bearer Token (required, Admin role)

**Request Example**

```bash
curl -X GET http://localhost:8000/api/v1/auth/admin/ping \
  -H "Authorization: Bearer <admin_access_token>"
```

**Success Response (200 OK)**

```json
{
  "detail": "admin-ok"
}
```

**Error Response (403 Forbidden)**

```json
{
  "code": "FORBIDDEN",
  "message": "Insufficient permissions",
  "detail": null,
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/auth/admin/ping",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Certificate Management Module

### 1. POST /ca/root

Generate a root Certificate Authority (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| algorithm | string | ✓ | Encryption algorithm (rsa_2048/rsa_4096/ec_p256/ec_p384) |
| common_name | string | ✓ | Certificate subject name |
| organization | string | ✓ | Organization name |
| validity_days | integer | ✓ | Validity period (days) |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/ca/root \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "rsa_2048",
    "common_name": "ca-pdf Root CA",
    "organization": "Example Corp",
    "validity_days": 3650
  }'
```

**Success Response (201 Created)**

```json
{
  "artifact_id": "550e8400-e29b-41d4-a716-446655440000",
  "algorithm": "rsa_2048",
  "serial_number": "A1B2C3D4E5F6",
  "subject": "CN=ca-pdf Root CA,O=Example Corp",
  "fingerprint_sha256": "3A5B7C9D1E2F4A6B8C0D1E2F3A4B5C6D",
  "issued_at": "2024-01-15T10:30:00Z",
  "expires_at": "2034-01-15T10:30:00Z"
}
```

---

### 2. GET /ca/root/certificate

Export root CA certificate (PEM format).

**Authentication Required**: None

**Request Example**

```bash
curl -X GET http://localhost:8000/api/v1/ca/root/certificate
```

**Success Response (200 OK)**

```json
{
  "certificate_pem": "-----BEGIN CERTIFICATE-----\nMIIBkTCB+wIJAKHHCgw51JMeMA0GCSqGSIb3DQEBBQUAMBMxETAPBgNVBAMMCENB\n...\n-----END CERTIFICATE-----"
}
```

---

### 3. POST /ca/certificates/issue

Issue a certificate for the current user.

**Authentication Required**: Bearer Token (required)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| common_name | string | ✓ | Certificate subject name |
| organization | string | ✓ | Organization name |
| algorithm | string | ✓ | Encryption algorithm |
| validity_days | integer | ✓ | Validity period (days) |
| p12_passphrase | string | ✓ | PKCS#12 key password |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/ca/certificates/issue \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "common_name": "user@example.com",
    "organization": "Example Corp",
    "algorithm": "rsa_2048",
    "validity_days": 365,
    "p12_passphrase": "passphrase123"
  }'
```

**Success Response (200 OK)**

```json
{
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "serial_number": 123456789,
  "status": "active",
  "issued_at": "2024-01-15T10:30:00Z",
  "expires_at": "2025-01-15T10:30:00Z",
  "certificate_pem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "p12_bundle": "MIIFKTCCBhG..."
}
```

---

### 4. POST /ca/certificates/import

Import external PKCS#12 certificate bundle.

**Authentication Required**: Bearer Token (required)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| p12_bundle | string | ✓ | Base64-encoded PKCS#12 file |
| passphrase | string | ✓ | PKCS#12 password |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/ca/certificates/import \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "p12_bundle": "MIIFKTCCBhG...",
    "passphrase": "cert_password"
  }'
```

**Success Response (200 OK)**

```json
{
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "serial_number": 987654321,
  "status": "active",
  "issued_at": "2023-01-15T10:30:00Z",
  "expires_at": "2026-01-15T10:30:00Z",
  "certificate_pem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "p12_bundle": null
}
```

---

### 5. GET /ca/certificates

List all certificates for the current user.

**Authentication Required**: Bearer Token (required)

**Request Example**

```bash
curl -X GET http://localhost:8000/api/v1/ca/certificates \
  -H "Authorization: Bearer <access_token>"
```

**Success Response (200 OK)**

```json
{
  "certificates": [
    {
      "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
      "serial_number": 123456789,
      "status": "active",
      "issued_at": "2024-01-15T10:30:00Z",
      "expires_at": "2025-01-15T10:30:00Z",
      "subject_common_name": "user@example.com"
    }
  ]
}
```

---

### 6. POST /ca/certificates/{certificate_id}/revoke

Revoke specified certificate (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| certificate_id | UUID | Certificate UUID |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/ca/certificates/550e8400-e29b-41d4-a716-446655440000/revoke \
  -H "Authorization: Bearer <admin_token>"
```

**Success Response (200 OK)**

```json
{
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked",
  "revoked_at": "2024-01-15T10:30:00Z"
}
```

---

## PDF Signing Module

### 1. POST /pdf/sign

Sign a single PDF document.

**Authentication Required**: Bearer Token (required)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pdf_file | file | ✓ | PDF document to sign |
| certificate_id | UUID | ✓ | Certificate UUID to use |
| visible | boolean | ✓ | Visible or invisible signature |
| page | integer | ✓ | Page number (1-indexed) |
| x | integer | ✓ | X coordinate (points) |
| y | integer | ✓ | Y coordinate (points) |
| width | integer | ✓ | Signature box width (points) |
| height | integer | ✓ | Signature box height (points) |
| seal_id | UUID | - | Corporate seal ID (optional) |
| reason | string | - | Signing reason (optional) |
| location | string | - | Signing location (optional) |
| use_tsa | boolean | - | Use timestamp service (optional) |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/pdf/sign \
  -H "Authorization: Bearer <access_token>" \
  -F "pdf_file=@document.pdf" \
  -F "certificate_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "visible=true" \
  -F "page=1" \
  -F "x=50" \
  -F "y=50" \
  -F "width=200" \
  -F "height=100" \
  -F "reason=Approved" \
  -F "use_tsa=true"
```

**Success Response (200 OK)**

Returns signed PDF file as binary stream.

---

### 2. POST /pdf/sign-batch

Sign multiple PDF documents in batch.

**Authentication Required**: Bearer Token (required)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pdf_files | file[] | ✓ | Array of PDF documents (max 10) |
| certificate_id | UUID | ✓ | Certificate UUID to use |
| visible | boolean | ✓ | Visible or invisible signature |
| page | integer | ✓ | Page number for all files |
| x | integer | ✓ | X coordinate for all files |
| y | integer | ✓ | Y coordinate for all files |
| width | integer | ✓ | Signature box width |
| height | integer | ✓ | Signature box height |
| seal_id | UUID | - | Corporate seal ID (optional) |
| reason | string | - | Signing reason (optional) |
| use_tsa | boolean | - | Use timestamp service (optional) |

**Success Response (200 OK)**

```json
{
  "results": [
    {
      "filename": "document1.pdf",
      "status": "success",
      "signed_file": "document1_signed.pdf",
      "size_bytes": 245678
    },
    {
      "filename": "document2.pdf",
      "status": "failed",
      "error": "Certificate expired"
    }
  ]
}
```

---

### 3. POST /pdf/verify

Verify signatures in a PDF document.

**Authentication Required**: Bearer Token (required)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pdf_file | file | ✓ | PDF document to verify |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/pdf/verify \
  -H "Authorization: Bearer <access_token>" \
  -F "pdf_file=@document.pdf"
```

**Success Response (200 OK)**

```json
{
  "filename": "document.pdf",
  "total_signatures": 2,
  "valid_count": 2,
  "trusted_count": 2,
  "signatures": [
    {
      "signature_id": "sig-001",
      "signer_name": "John Doe",
      "validity": "valid",
      "trust_status": "trusted",
      "signed_at": "2024-01-15T10:30:00Z",
      "timestamp_server": "https://freetsa.org/tsr",
      "modification_level": "no_changes_allowed"
    }
  ]
}
```

---

## User Management Module

### 1. GET /users

List all users (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Request Example**

```bash
curl -X GET "http://localhost:8000/api/v1/users?skip=0&limit=10" \
  -H "Authorization: Bearer <admin_token>"
```

**Success Response (200 OK)**

```json
{
  "users": [
    {
      "id": 1,
      "email": "admin@example.com",
      "username": "admin",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-01-10T08:00:00Z"
    },
    {
      "id": 2,
      "email": "user@example.com",
      "username": "john_doe",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-12T10:00:00Z"
    }
  ],
  "total": 2
}
```

---

### 2. POST /users

Create a new user (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string(email) | ✓ | User email |
| password | string | ✓ | User password |
| username | string | ✓ | User name |
| role | string | ✓ | User role (admin/user) |

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123",
    "username": "newuser",
    "role": "user"
  }'
```

**Success Response (201 Created)**

```json
{
  "id": 3,
  "email": "newuser@example.com",
  "username": "newuser",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### 3. POST /users/{user_id}/disable

Disable a user account (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Request Example**

```bash
curl -X POST http://localhost:8000/api/v1/users/2/disable \
  -H "Authorization: Bearer <admin_token>"
```

**Success Response (200 OK)**

```json
{
  "id": 2,
  "email": "user@example.com",
  "is_active": false
}
```

---

## Audit Logging Module

### 1. GET /audit/logs

Retrieve audit logs (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Query Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| user_id | UUID | Filter by user (optional) |
| event_type | string | Filter by event type (optional) |
| start_date | string | Start date in ISO format (optional) |
| end_date | string | End date in ISO format (optional) |
| skip | integer | Pagination offset (default: 0) |
| limit | integer | Pagination limit (default: 50, max: 500) |

**Request Example**

```bash
curl -X GET "http://localhost:8000/api/v1/audit/logs?event_type=pdf.signed&skip=0&limit=20" \
  -H "Authorization: Bearer <admin_token>"
```

**Success Response (200 OK)**

```json
{
  "logs": [
    {
      "log_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": 1,
      "event_type": "pdf.signed",
      "description": "PDF document signed",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "resource_id": "pdf-001",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150
}
```

---

### 2. POST /audit/logs/export

Export audit logs to CSV (admin only).

**Authentication Required**: Bearer Token (Admin role)

**Query Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date in ISO format (optional) |
| end_date | string | End date in ISO format (optional) |
| format | string | Export format: csv or json (default: csv) |

**Request Example**

```bash
curl -X POST "http://localhost:8000/api/v1/audit/logs/export?format=csv" \
  -H "Authorization: Bearer <admin_token>" \
  -o audit_logs.csv
```

**Success Response (200 OK)**

Returns CSV file as attachment.

---

## System Module

### 1. GET /health

Health check endpoint (no authentication required).

**Request Example**

```bash
curl -X GET http://localhost:8000/api/v1/health
```

**Success Response (200 OK)**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "services": {
    "ca": "operational",
    "pdf": "operational",
    "storage": "operational"
  }
}
```

---

## Common Scenario Examples

### Scenario 1: Complete Signing Workflow

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
# Response: {"access_token": "...", "refresh_token": "..."}

# 2. Get certificates
curl -X GET http://localhost:8000/api/v1/ca/certificates \
  -H "Authorization: Bearer <access_token>"

# 3. Sign PDF
curl -X POST http://localhost:8000/api/v1/pdf/sign \
  -H "Authorization: Bearer <access_token>" \
  -F "pdf_file=@contract.pdf" \
  -F "certificate_id=<cert_id>" \
  -F "visible=true" \
  -F "page=1" \
  -F "x=50" \
  -F "y=50" \
  -F "width=200" \
  -F "height=100" \
  -o contract_signed.pdf
```

---

## Error Code Reference

| Code | HTTP Status | Description |
|------|------------|-------------|
| UNAUTHORIZED | 401 | Authentication failed (missing/invalid token) |
| FORBIDDEN | 403 | Insufficient permissions for operation |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 422 | Invalid request parameters |
| CONFLICT | 409 | Resource conflict (e.g., certificate already exists) |
| INTERNAL_ERROR | 500 | Server error |
| CERTIFICATE_NOT_FOUND | 404 | Certificate not found |
| CERTIFICATE_EXPIRED | 400 | Certificate has expired |
| CERTIFICATE_REVOKED | 400 | Certificate has been revoked |
| PDF_INVALID | 400 | PDF file is invalid or corrupted |
| PDF_TOO_LARGE | 413 | PDF file exceeds size limit |
| ROOT_CA_NOT_INITIALIZED | 400 | Root CA not yet generated |
| SIGNATURE_VERIFICATION_FAILED | 400 | PDF signature verification failed |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests, please try again later |

---

**Last Updated**: 2024
**Version**: 1.0
