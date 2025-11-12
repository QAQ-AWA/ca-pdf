# User Guide (Preview)

> **Coverage:** This English version highlights core workflows for issuing certificates, signing PDFs, and resolving common issues. Refer to the Chinese document for full screenshots and advanced scenarios.

## Getting Started

1. **Login** with the administrator credentials defined in `.env`.
2. **Generate the root CA** in the *Certificate Authority* section before inviting users.
3. **Invite operators** by creating user accounts and assigning roles.

## Certificate Lifecycle

### Generate Root CA
- Navigate to *Certificate Authority → Root CA*.
- Select algorithm (RSA-4096 or EC-P256) and validity period.
- Download the root certificate for distribution to clients.

### Issue Certificates
- Open *Certificate Authority → User Certificates*.
- Provide subject information (name, email) and validity term.
- Download the PKCS#12 bundle and deliver it securely to the user.

### Import External Certificates
- Use the *Import* tab to upload an existing PKCS#12 file.
- Assign it to a user account for signing or verification tasks.

### Revoke Certificates
- On the certificate list, choose **Revoke** to invalidate a credential.
- The CRL updates immediately; downstream systems should refresh it.

## PDF Signing

### Visible Signature
1. Upload the target PDF.
2. Choose the certificate and signature appearance.
3. Position the signature box on the page preview.
4. Add reason, location, and contact details if required.

### Invisible Signature
- Toggle *Invisible signature* to embed crypto metadata without altering visuals.

### Batch Signing
- Upload up to 10 PDFs at once.
- Configure shared parameters (seal, timestamp policy, metadata).
- Review the summary before confirming.

## Verification Workflow

- Upload one or more PDFs to *Verify*.
- The platform returns:
  - Signature validity (Valid / Invalid / Unsigned)
  - Trust chain status (Trusted / Untrusted)
  - Timestamp verification results
  - Modification detection indicators

## Troubleshooting Tips

| Symptom | Quick Check |
|---------|-------------|
| Signature reported as untrusted | Ensure the root CA is installed in the reader's trust store. |
| Timestamp failure | Verify TSA credentials and network connectivity. |
| Cannot upload seal | Check file size (≤ 1 MiB) and format (PNG/SVG). |
| Login blocked | Rate limit triggered – wait 60 seconds or reset the password. |

## Additional Resources

- [Troubleshooting](./TROUBLESHOOTING.md)
- [API Reference](./API.md)
- [Security Guide](./SECURITY.md)
