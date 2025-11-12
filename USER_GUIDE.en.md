# ca-pdf User Manual

> 📖 **Documentation Navigation**: [README](./README.en.md) · [Documentation Index](./DOCUMENTATION.md) · [API Reference](./API.en.md) · [Troubleshooting](./TROUBLESHOOTING.md)
> 🎯 **Target Audience**: Business Users / Administrators
> ⏱️ **Estimated Reading Time**: 20 minutes

**Project Repository**: [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**Contact Email**: [7780102@qq.com](mailto:7780102@qq.com)

This manual guides end users through certificate management and PDF signing workflows. For system background, see [README.en.md](./README.en.md); for automation/integration, see [API.en.md](./API.en.md); for troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

## 1. Overview

This guide targets system administrators, business users, and operations teams to efficiently and securely use ca-pdf self-hosted digital signature platform.

### Audience
- **System Administrators**: Certificate systems, user permissions, audit tracking, security
- **Business Users**: Certificate requests, PDF signing, verification operations
- **Operations Teams**: Platform maintenance, data export, troubleshooting

### Use Cases

Enterprise contract approval, external agreement signing, internal document confirmation, compliance archiving, cross-departmental collaboration, any workflow requiring legally valid PDF signatures.

### Quick Navigation

| Module | Description |
|--------|-------------|
| [Account & Authentication](#2-account--authentication) | Login, logout, token refresh, password reset, role explanation |
| [Certificate Management](#3-certificate-management) | Generate root CA, issue/import certificates, list, revoke, CRL |
| [PDF Digital Signing](#4-pdf-digital-signing) | Upload, parameter configuration, seal management, single/batch signing, preview |
| [Signature Verification](#5-signature-verification) | Verification workflow, result interpretation, common issues |
| [Audit Logs](#6-audit-logs-admin) | Log structure, filtering, pagination, export |
| [User Management](#7-user-management-admin) | User lifecycle, permission control, batch import |
| [Data Export](#8-data-export) | Export channels for audit, certificates, signing records |
| [Common Scenarios](#9-common-scenario-tutorials) | 5 typical business process walkthroughs |
| [FAQ](#10-frequently-asked-questions-faq) | Hot topics for certificates, signing, verification |
| [Tips & Tricks](#11-shortcuts--tips) | Productivity methods, best practices |

---

## 2. Account & Authentication

### 2.1 Login

1. Open frontend address (example: `https://app.localtest.me`)
2. Enter registered email and password
3. Submit to enter dashboard
4. First login: immediately request password reset via admin

### 2.2 Logout

Click avatar in top-right → Select "Logout" to immediately clear access and refresh tokens.

### 2.3 Token Refresh

- **Mechanism**: Access Token + Refresh Token dual-token system
- **Access Token**: Default 15-minute expiration
- **Refresh Token**: Default 3-day expiration
- **Auto-Refresh**: Frontend automatically requests new token when access token expires; old refresh token immediately revoked

### 2.4 Password Reset

Regular users cannot self-modify passwords. If lost:
1. Contact admin in "User Management"
2. Select target account, click "Reset Password"
3. Enter and confirm new password
4. User logs in with temporary password, then request stronger password from admin

### 2.5 Permission Levels

| Role | Permissions |
|------|-------------|
| **User** | Issue/import personal certificates, perform signing, verification, view personal logs |
| **Admin** | Full user permissions + user management, certificate revocation, CRL generation, complete audit logs, seal management |

---

## 3. Certificate Management

### 3.1 Generate Root CA (Admin)

1. Access "Certificate Management" page
2. If no root CA, page shows generation wizard
3. Fill required fields: Common Name (CN), Organization (O), Country (C), validity (days)
4. Choose algorithm: RSA-4096 or EC-P256 (RSA best compatibility, EC better performance)
5. Click "Generate Root CA"
6. After completion, system prompts to download root cert and key backup
7. Recommend importing root CA certificate to enterprise PDF reader trusted list

### 3.2 Issue User Certificate

1. Fill "Issue Certificate" card: CN, O, Email, validity, algorithm
2. Submit; system generates PKCS#12 file (.p12 or .pfx)
3. Download file and record generated serial number for future signing

### 3.3 PKCS#12 Format Explanation

- Contains user certificate, private key, and root chain
- Protected by random password (displayed on page)
- Recommend storing in password manager with offline backup

### 3.4 Import External Certificate

1. Switch to "Import Certificate" card
2. Upload `.p12/.pfx` file
3. Enter original certificate password and submit
4. System verifies and shows "Import successful", list refreshes
5. Supported certificates must contain End-Entity cert and private key; expired marked "Expired"

### 3.5 View Certificate List

- **Fields**: Serial number, subject name, email, issue date, expiration, status (Active/Revoked/Expired/Pending)
- **Search**: Top search box supports serial number and subject keyword fuzzy search
- **Filter**: Top-right status filter and sort by expiration
- **Permissions**: Regular users see only own certificates; admins see all

### 3.6 Revoke Certificate

1. Locate target certificate in list, click "Revoke"
2. Enter revocation reason (example: certificate leaked, employee departed)
3. Confirm operation; status changes to "Revoked", revocation time logged

### 3.7 CRL Management

- Click "Generate CRL" anytime to refresh revocation list
- System auto-downloads latest CRL file
- Historical CRL shows name, generation time, serial count, can re-download

---

## 4. PDF Digital Signing

### 4.1 Signing Workbench Layout

- **File Queue**: Lists PDFs pending signature
- **Parameter Panel**: Configure certificate, seal, visibility, metadata, timestamp
- **PDF Preview**: Real-time drag positioning for signature, support zoom

### 4.2 Upload Files

- Support single or batch (≤10) PDFs
- Max 50 MiB per file
- Batch upload processes queue order, can remove anytime

### 4.3 Configure Signing Parameters

| Configuration | Description |
|---------------|-------------|
| Certificate ID | Required; enter certificate serial; copy from cert list to avoid error |
| Signature Visibility | Visible: signature box in PDF; Invisible: digital signature only, no visual change |
| Page/Position | Visible signature specifies page; preview drag or input coordinates, width/height (units: points) |
| Metadata | Optional: reason, location, contact info; written to PDF signature properties |
| Timestamp (TSA) | Check to send configured TSA request for trusted time |
| LTV Embedding | Write OCSP/CRL response to signature for long-term offline verification |

### 4.4 Corporate Seals

1. Admin uploads PNG/SVG image in "Seal Management" (≤1 MiB)
2. Auto-generates ID after upload, supports batch, enable/disable
3. Regular users select enterprise seal in signing panel for contract-style appearance

### 4.5 Single Signature Workflow

1. Upload PDF → Select certificate → Add signature layer
2. Set page and position → Choose seal, enter reason
3. Optional: check TSA and LTV
4. Click "Sign"; browser auto-downloads `<original>_signed.pdf`

### 4.6 Batch Signing

- Upload multiple files, configure parameters for first
- Apply to all; system signs each, progress bar shows status
- Single file failure doesn't block others

### 4.7 Signature Preview

Before final signing, preview shows proposed signature location and appearance; can adjust coordinates and dimensions.

---

## 5. Signature Verification

### 5.1 Verification Workflow

1. Go to "Verification Center"
2. Upload signed PDF (≤50 MiB)
3. System automatically analyzes all embedded signatures
4. Shows count, validity, trust status of each

### 5.2 Result Interpretation

**Validity Status**:
- **Valid**: Signature mathematically correct, hasn't been tampered
- **Invalid**: Signature corrupted or PDF modified after signing
- **Unsigned**: No signatures detected

**Trust Status**:
- **Trusted**: Signer certificate in trusted root chain
- **Untrusted**: Root CA not recognized by system

**Timestamp**:
- Shows signature time and timestamp server
- Check "timestamp valid" indicates reliable timestamp

**DocMDP Level**:
- **No Changes**: File locked after signing
- **Form Changes**: Only form fields modifiable
- **Annotations**: Signatures and annotations allowed

### 5.3 Common Issues

- **Certificate Expired**: Signature was valid at signing time but cert now expired
- **Root CA Mismatch**: Signer root CA differs from system root CA
- **Modification Detected**: PDF modified after signing (DocMDP violation)

---

## 6. Audit Logs (Admin)

### 6.1 Log Structure

- **User**: Who performed operation
- **Event Type**: Operation category (login, certificate issued, pdf signed, revoked)
- **IP Address**: Source of operation
- **Timestamp**: Operation time (UTC)
- **Resource**: Affected certificate/document ID

### 6.2 Log Queries

- **Date Range**: Filter from → to dates
- **User Filter**: By specific user
- **Event Type**: By operation category
- **Search**: Free-text search in description

### 6.3 Pagination

- Default 50 entries per page
- Adjustable page size
- Navigate between pages

### 6.4 Export

- **CSV Export**: For spreadsheet analysis
- **JSON Export**: For system integration
- Supports filtered or complete exports

---

## 7. User Management (Admin)

### 7.1 User List

- Shows all platform users
- Columns: email, role, created date, last login, status
- Search by email

### 7.2 Create User

1. Click "Create User"
2. Enter email, password, username, select role
3. Submit; system auto-sends initial password via email (optional)

### 7.3 Edit User

1. Select user from list
2. Click "Edit"
3. Modify role, status
4. Save changes

### 7.4 Disable User

1. Select user
2. Click "Disable"
3. User cannot login; existing tokens immediately revoked

### 7.5 Reset Password

1. Select user
2. Click "Reset Password"
3. Enter new password and confirm
4. System sends new credentials (optional notification)

---

## 8. Data Export

### 8.1 Audit Log Export

- Access: Admin only
- Format: CSV or JSON
- Includes: All operations with full metadata

### 8.2 Certificate List Export

- Access: Admin (all) / User (own only)
- Format: CSV
- Includes: Serial, subject, issuer, status, dates

### 8.3 Signing Record Export

- Access: Admin (all) / User (own only)
- Format: CSV
- Includes: Document name, signer, timestamp, status

---

## 9. Common Scenario Tutorials

### Scenario 1: First-Time Setup

1. **Admin**: Generate root CA (Algorithm: RSA-4096, Validity: 10 years)
2. **Admin**: Create user accounts for team
3. **Users**: Request certificates via "Issue Certificate"
4. **Admin**: Users download and store certificates securely
5. **System**: Ready for signing workflows

### Scenario 2: Contract Signing

1. **Preparer**: Upload contract PDF to signing workbench
2. **Signer**: Select own certificate from list
3. **Signer**: Set signature position on first page
4. **Signer**: Click "Sign", download signed PDF
5. **Verifier**: Upload to Verification Center to confirm validity

### Scenario 3: Batch Document Approval

1. **Preparer**: Upload 5 PDFs to signing workbench
2. **Approver**: Set certificate, visibility, seal
3. **Approver**: Click "Apply to All", check "Batch Sign"
4. **Approver**: System signs each, downloads zip or processes sequentially
5. **Verifier**: Sample-verify a few documents

### Scenario 4: Audit Compliance

1. **Admin**: Go to Audit Logs
2. **Admin**: Filter by date (last quarter) and event type (pdf.signed)
3. **Admin**: Export to CSV
4. **Analyst**: Analyze document count, users, timestamps for compliance reporting

### Scenario 5: Certificate Renewal

1. **User**: Request new certificate before current expires
2. **System**: Issues replacement (new serial, same owner)
3. **Admin**: Optionally revoke old certificate
4. **User**: Switches to new cert for signing
5. **System**: Old signatures still valid (timestamp embedded)

---

## 10. Frequently Asked Questions (FAQ)

### Q: Can I use the same certificate on multiple devices?

**A**: Yes, PKCS#12 files are portable. Backup securely and keep password safe.

### Q: What if I forget my certificate password?

**A**: Admin must issue a new certificate; old one cannot be recovered.

### Q: How long are signatures valid?

**A**: Indefinitely if root CA trusted and no revocation. Embedded timestamps provide cryptographic proof of signing time.

### Q: Can signatures be modified after signing?

**A**: No. Document-level integrity is protected. Any modification invalidates signature.

### Q: How do I verify signatures created on another platform?

**A**: Upload to Verification Center. If signer root CA in system, verification succeeds; otherwise "Untrusted".

### Q: Can I batch sign 100 documents?

**A**: Current limit is 10 per batch. Upload multiple batches sequentially.

### Q: What happens if I revoke a certificate?

**A**: Future signatures with that cert are flagged "Revoked". Past signatures remain valid (timestamp-based).

### Q: Who can see my certificates?

**A**: Admin users and yourself. Other users cannot access.

### Q: Is audit log searchable?

**A**: Yes. Filter by user, event type, date range. Export for detailed analysis.

### Q: Can I export signatures as PDF/A?

**A**: Future feature. Currently embedded as standard PDF signatures (Acrobat compatible).

---

## 11. Shortcuts & Tips

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` (Cmd+S) | Save/Submit form |
| `ESC` | Close modal/dialog |
| `Ctrl+Z` (Cmd+Z) | Undo (if supported) |

### Best Practices

1. **Security**: Store certificate passwords in secure password manager
2. **Backup**: Offline backup root CA and master key (admin only)
3. **Rotation**: Issue new certificates before expiration
4. **Verification**: Regularly verify important documents
5. **Audit**: Review audit logs monthly for anomalies
6. **Testing**: Batch test with non-critical docs first

### Performance Tips

- Use visible signatures sparingly (slower than invisible)
- Batch sign documents in groups of 5-10 for efficiency
- Schedule batch operations off-peak
- Archive old signing records after 1 year (per compliance)

### Troubleshooting Quick Links

- Can't login? → Check email/password or contact admin
- Certificate expired? → Issue new or renew before expiration
- Signature verification fails? → Check root CA trusted, timestamp validity
- Upload fails? → Verify PDF not corrupted, under 50MB, valid format

---

**Last Updated**: 2024
**Version**: 1.0
