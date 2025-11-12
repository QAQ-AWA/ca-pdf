# Troubleshooting (Preview)

> **Hint:** This quick-reference table covers the most common production questions. The Chinese document includes extended explanations and remediation steps.

## Quick Diagnosis Matrix

| Issue | Probable Cause | Immediate Action |
|-------|----------------|------------------|
| Login attempts blocked | Rate limiting triggered or incorrect credentials. | Wait 60 seconds, reset password via admin, verify CAPTCHA/IP restrictions. |
| Root CA unavailable | Root certificate not created after deployment. | Log in as admin and generate the root CA before issuing certificates. |
| Signed PDF shows as untrusted | Root CA not imported in PDF reader trust store. | Distribute root certificate and configure trust settings. |
| Timestamp errors | TSA credentials invalid or network blocked. | Revalidate TSA credentials, check outbound connectivity, retry. |
| Seal upload fails | File exceeds 1 MiB or unsupported format. | Resize to ≤ 1 MiB and use PNG/SVG. |
| PDF signing timeout | Large files or heavy concurrency. | Increase worker resources, enable background job queue for bulk signing. |
| Database migration failure | Missing environment variables or incompatible schema. | Ensure `DATABASE_URL` and `ENCRYPTED_STORAGE_MASTER_KEY` are set; run migrations sequentially. |

## Log Collection

- **Backend logs:** `docker logs backend` or `./deploy.sh logs backend`.
- **Frontend logs:** Browser console + `docker logs frontend`.
- **Traefik logs:** Enable debug mode and inspect routing errors.
- **Audit logs:** Use `/audit/logs` endpoint for user activity traces.

## Support Escalation

1. Gather relevant logs and timestamps.
2. Capture the API response (status code, payload) if applicable.
3. File an issue at <https://github.com/QAQ-AWA/ca-pdf/issues> with reproduction steps.
4. For sensitive cases, email [7780102@qq.com](mailto:7780102@qq.com).

Consult the Chinese documentation for additional runbooks, incident response templates, and escalation policies.
