# API Reference (Preview)

> **Translation status:** This page highlights the most frequently used endpoints. For exhaustive descriptions, consult the Chinese document while the English version is completed.

## Authentication

### `POST /auth/login`
- **Purpose:** Exchange credentials for an access token (15 minutes) and refresh token (3 days).
- **Request:** JSON body with `email` and `password`.
- **Response:** JWT tokens plus user profile summary.
- **Notes:** Rate limited (default 5 attempts per 60 seconds).

### `POST /auth/refresh`
- Use a valid refresh token to obtain a new access token. Refresh tokens rotate automatically.

### `POST /auth/logout`
- Invalidates the current refresh token. Use it to terminate sessions explicitly.

## Certificate Authority

### `POST /ca/root`
- Initialize or rotate the root CA certificate. Supports RSA-4096 and EC-P256.
- Requires admin privileges.

### `POST /ca/certificates`
- Issue end-entity certificates packaged as PKCS#12 bundles.
- Accepts subject metadata, validity period, and key parameters.

### `POST /ca/certificates/import`
- Import an external PKCS#12 certificate and register it in the platform.

### `POST /ca/certificates/{id}/revoke`
- Revoke a certificate and update the CRL immediately.

### `GET /ca/crl`
- Download the latest certificate revocation list in PEM format.

## PDF Signing

### `POST /pdf/sign`
- Upload a PDF and apply a visible or invisible signature.
- Supports seal artwork, reason/location metadata, and TSA timestamps.

### `POST /pdf/sign/bulk`
- Batch sign up to 10 PDFs using a unified configuration.

### `POST /pdf/verify`
- Validate uploaded PDFs. Returns signature integrity, trust chain status, and timestamp validity.

### `POST /pdf/seals`
- Manage organization seals (PNG/SVG, encrypted at rest).

## Audit & Logs

### `GET /audit/logs`
- List audit events with filters for actor, action type, and time range.
- Includes IP address, user agent, and resource identifiers for traceability.

## Users

- `POST /users/` — create users (admin only)
- `GET /users/me` — fetch the current profile
- `PATCH /users/{id}` — update role, status, or password
- `DELETE /users/{id}` — disable a user account

## Health Check

- `GET /health` — returns deployment metadata and version information. Useful for uptime probes.

## Error Handling

- Standardized error responses follow the structure `{ "detail": "..." }` with HTTP status codes.
- Token expiration uses 401 responses; permission issues return 403.
- Validation errors include a `loc` and `msg` field per FastAPI conventions.

> ✅ The Chinese edition contains request/response samples (cURL, Python, TypeScript) and detailed error scenarios. Use it until translations are finalized.
