# User Guide

> **Status**: Step-by-step usage instructions
> **Target Audience**: Business users and end users
> **Last Updated**: 2024

Welcome to the ca-pdf User Guide. This guide will walk you through common tasks and workflows for managing certificates and signing PDF documents.

## Getting Started

### First Login

1. Open your browser and navigate to the ca-pdf dashboard
2. Enter your username and password (provided by your administrator)
3. Click "Login"

### Dashboard Overview

The main dashboard shows:
- **Certificates**: Your available digital certificates
- **Documents**: Signed and unsigned documents
- **Quick Actions**: Common tasks and shortcuts
- **Recent Activity**: Your recent operations

## Certificate Management

### Viewing Certificates

1. Click **"Certificates"** in the main menu
2. Browse the list of available certificates
3. Click a certificate to view details

Certificate details include:
- Certificate Subject (CN)
- Issuer information
- Valid From and Valid To dates
- Serial number
- Signature algorithm

### Requesting a Certificate

To request a new certificate:

1. Click **"Request Certificate"** button
2. Fill in the certificate details:
   - **Common Name (CN)**: Your name or identifier
   - **Email**: Your email address
   - **Organization**: Organization name (optional)
   - **Department**: Department name (optional)
3. Click **"Submit Request"**
4. Wait for administrator approval

### Certificate Status

Certificates have the following statuses:

- **Pending**: Waiting for approval
- **Active**: Ready to use for signing
- **Expired**: No longer valid
- **Revoked**: Disabled and cannot be used

## Document Signing

### Uploading a Document

1. Click **"Documents"** in the main menu
2. Click **"Upload Document"** button
3. Select a PDF file from your computer
4. Click **"Open"** or **"Upload"**

### Signing a Document

1. From the Documents list, click a document to select it
2. Click **"Sign Document"** button
3. Choose your certificate from the dropdown
4. (Optional) Add signature reason and location
5. Click **"Preview Signature"** to see where it will appear
6. Click **"Sign"** to complete
7. The signed document will be generated

### Batch Signing

To sign multiple documents:

1. Click **"Batch Sign"** from the Documents menu
2. Select multiple documents using checkboxes
3. Choose your certificate
4. Set signature options
5. Click **"Sign All"**

Progress will be displayed for each document.

## Document Management

### Viewing Document Details

Click on any document to see:
- Upload date and time
- File size
- Current status
- Signature details (if signed)
- Verification status

### Downloading Documents

1. Click the document in the list
2. Click **"Download"** button
3. The file will be saved to your computer

### Verifying Signatures

1. Click a signed document
2. Click **"Verify Signature"** tab
3. Signature validity will be displayed:
   - ✓ Valid
   - ✗ Invalid
   - ⚠ Untrusted Certificate

### Deleting Documents

1. Select document(s) using checkboxes
2. Click **"Delete"** button
3. Confirm deletion

## Account Management

### Viewing Profile

Click your **username** in the top-right corner and select **"Profile"** to:
- View your account information
- See assigned roles and permissions
- View last login time

### Changing Password

1. Click your **username** in the top-right corner
2. Select **"Change Password"**
3. Enter your current password
4. Enter your new password (twice for confirmation)
5. Click **"Update"**

Password requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one number
- At least one special character

### Session Management

You can view and manage your active sessions:

1. Go to **Profile** → **Sessions**
2. See list of active sessions with timestamps
3. Click **"Logout"** next to any session to end it

## Common Tasks

### Task: Sign and Send a Document

1. **Upload**: Click "Upload Document" and select your PDF
2. **Prepare**: Review the document to identify signature area
3. **Sign**: Click "Sign Document", select your certificate
4. **Download**: Click "Download" to get the signed PDF
5. **Send**: Use your preferred method to send the signed document

### Task: Verify a Received Signature

1. **Upload**: Click "Upload Document" and select the signed PDF
2. **Verify**: Click "Verify Signature" tab
3. **Review**: Check signature validity and signer information
4. **Trust**: If from trusted source, the verification shows green checkmark

### Task: Revoke Certificate Access

1. Go to **Certificates**
2. Find the certificate you want to stop using
3. Click the **menu** (...) button
4. Select **"Revoke"**
5. Confirm the action

The certificate will be marked as revoked and cannot be used for new signatures.

## Troubleshooting

### I Can't Log In

- Verify your username is correct
- Check CAPS LOCK is off
- Reset your password: Click "Forgot Password" link
- Contact your administrator

### My Certificate is Expired

- Request a new certificate through "Request Certificate"
- Wait for administrator approval
- Once approved, you can use it for signing

### Document Upload Failed

- Check file is a valid PDF
- Verify file size is under the limit (typically 50 MB)
- Ensure your internet connection is stable
- Try uploading again

### Signature Verification Failed

- Verify the PDF has not been modified after signing
- Check the certificate is still valid
- Ensure the trusted roots are configured correctly

## Security Tips

1. **Protect Your Password**
   - Never share your password with others
   - Use a strong, unique password
   - Change password regularly

2. **Secure Your Certificate**
   - Only sign trusted documents
   - Review before signing
   - Do not share your private key

3. **Verify Recipients**
   - Always verify you're sending to the right person
   - Use secure channels for sending signed documents
   - Keep audit trails of important signings

4. **Keep Session Secure**
   - Log out when finished
   - Close browser completely before leaving computer
   - Don't use on shared computers

## Advanced Features

### Signature Fields

Some documents may have pre-defined signature fields:

1. When signing, signature fields will be highlighted
2. You can choose which fields to sign
3. Multiple signatures are supported (for multi-party approval)

### Certificate Chain Verification

The system automatically verifies:
- Certificate validity dates
- Issuer trust status
- Certificate revocation status
- Signature algorithm strength

### Audit Trail

All your signing actions are logged:

1. Click **"Activity Log"** in the main menu
2. View all your operations with timestamps
3. Export logs for compliance purposes

## Getting Help

- 📖 **Documentation**: See the full documentation at [https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
- 💬 **Support**: Contact your system administrator
- ✉️ **Email**: [7780102@qq.com](mailto:7780102@qq.com)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + U` | Upload Document |
| `Ctrl/Cmd + S` | Sign Document |
| `Ctrl/Cmd + D` | Download Document |
| `Esc` | Close Dialog |
| `?` | Help (on many pages) |

## For More Information

- [API Documentation](./API.md) - For developers integrating with ca-pdf
- [Deployment Guide](./DEPLOYMENT.md) - System administrators
- [Troubleshooting](./TROUBLESHOOTING.md) - Solutions to common problems
- [Development Guide](./DEVELOPMENT.md) - Technical details

---

**Last updated**: 2024
