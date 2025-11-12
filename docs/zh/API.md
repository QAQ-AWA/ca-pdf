# ca-pdf API 文档
> 📖 **文档导航**：[README](./index.md) · [文档索引](./DOCUMENTATION.md) · [开发指南](./DEVELOPMENT.md) · [故障排查](./TROUBLESHOOTING.md)
> 🎯 **适用人群**：后端 / 集成开发者
> ⏱️ **预计阅读时间**：45 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本文提供 ca-pdf 平台全部 REST API 的参数、示例与错误码。建议先阅读 [README.md](./index.md) 了解整体背景，并结合 [DEVELOPMENT.md](./DEVELOPMENT.md) 准备开发环境。接口故障排查可参阅 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。

---

自托管的 PDF 电子签章平台完整 API 参考指南。

## 目录

1. [API 概览](#api-概览)
2. [认证模块](#认证模块)
3. [证书管理模块](#证书管理模块)
4. [PDF签章模块](#pdf签章模块)
5. [用户管理模块](#用户管理模块)
6. [审计日志模块](#审计日志模块)
7. [系统模块](#系统模块)
8. [常见场景示例](#常见场景示例)
9. [错误码参考](#错误码参考)

---

## API 概览

### 基础 URL

```
http://localhost:8000/api/v1
```

### 认证方式

所有受保护的 API 端点均需在请求头中携带 JWT Token：

```
Authorization: Bearer <your_jwt_token>
```

### 请求/响应格式

- 所有请求和响应均采用 JSON 格式
- 错误响应采用标准错误格式（详见 [错误处理](#错误处理标准格式)）

### 错误处理标准格式

所有 API 错误响应遵循以下统一格式：

```json
{
  "code": "ERROR_CODE",
  "message": "用户友好的错误消息",
  "detail": "技术细节（可选）",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/auth/login",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 认证模块

### 1. POST /auth/login

用户登录，获取 access_token 和 refresh_token。

**认证要求**: 无（公开端点）

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| email | string(email) | ✓ | 用户邮箱 |
| password | string | ✓ | 用户密码 |

**请求示例**

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

**成功响应 (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应 (401 Unauthorized)**

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

**常见错误**

- 401：邮箱或密码不正确
- 422：邮箱格式无效或密码为空

---

### 2. POST /auth/logout

登出并撤销当前的 Token。

**认证要求**: Bearer Token（必需）

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| refresh_token | string | ✓ | 登录时获得的 refresh token |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

**成功响应 (200 OK)**

```json
{
  "detail": "Successfully logged out"
}
```

---

### 3. POST /auth/refresh

Token 轮换，使用 refresh_token 获取新的 access_token。

**认证要求**: 无

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| refresh_token | string | ✓ | 登录时获得的 refresh token |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

**成功响应 (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 4. GET /auth/me

获取当前认证用户的个人信息。

**认证要求**: Bearer Token（必需）

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**成功响应 (200 OK)**

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

管理员验证端点（仅限管理员访问）。

**认证要求**: Bearer Token（必需，Admin 角色）

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/auth/admin/ping \
  -H "Authorization: Bearer <admin_access_token>"
```

**成功响应 (200 OK)**

```json
{
  "detail": "admin-ok"
}
```

**错误响应 (403 Forbidden)**

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

## 证书管理模块

### 1. POST /ca/root

生成根证书颁发机构（仅限管理员）。

**认证要求**: Bearer Token（Admin 角色）

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| algorithm | string | ✓ | 加密算法（rsa_2048/rsa_4096/ec_p256/ec_p384） |
| common_name | string | ✓ | 证书主体名称 |
| organization | string | ✓ | 组织名称 |
| validity_days | integer | ✓ | 有效期（天数） |

**请求示例**

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

**成功响应 (201 Created)**

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

导出根 CA 证书（PEM 格式）。

**认证要求**: 无

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/ca/root/certificate
```

**成功响应 (200 OK)**

```json
{
  "certificate_pem": "-----BEGIN CERTIFICATE-----\nMIIBkTCB+wIJAKHHCgw51JMeMA0GCSqGSIb3DQEBBQUAMBMxETAPBgNVBAMMCENB\n...\n-----END CERTIFICATE-----"
}
```

---

### 3. POST /ca/certificates/issue

为当前用户签发证书。

**认证要求**: Bearer Token（必需）

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| common_name | string | ✓ | 证书主体名称 |
| organization | string | ✓ | 组织名称 |
| algorithm | string | ✓ | 加密算法 |
| validity_days | integer | ✓ | 有效期（天数） |
| p12_passphrase | string | ✓ | PKCS#12 密钥密码 |

**请求示例**

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

**成功响应 (200 OK)**

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

导入外部 PKCS#12 证书包。

**认证要求**: Bearer Token（必需）

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| p12_bundle | string | ✓ | Base64 编码的 PKCS#12 文件 |
| passphrase | string | ✓ | PKCS#12 密码 |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/ca/certificates/import \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "p12_bundle": "MIIFKTCCBhG...",
    "passphrase": "cert_password"
  }'
```

**成功响应 (200 OK)**

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

列出当前用户的所有证书。

**认证要求**: Bearer Token（必需）

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/ca/certificates \
  -H "Authorization: Bearer <access_token>"
```

**成功响应 (200 OK)**

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

吊销指定的证书（仅限管理员）。

**认证要求**: Bearer Token（Admin 角色）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| certificate_id | UUID | 证书 UUID |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/ca/certificates/550e8400-e29b-41d4-a716-446655440000/revoke \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200 OK)**

```json
{
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked",
  "revoked_at": "2024-01-15T10:30:00Z"
}
```

---

### 7. POST /ca/crl

生成新的证书撤销列表 (CRL)。

**认证要求**: Bearer Token（Admin 角色）

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/ca/crl \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200 OK)**

```json
{
  "artifact_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "CRL-2024-01-15",
  "created_at": "2024-01-15T10:30:00Z",
  "crl_pem": "-----BEGIN X509 CRL-----\n...\n-----END X509 CRL-----",
  "revoked_serials": [123456789, 987654321]
}
```

---

### 8. GET /ca/crl

列出已生成的证书撤销列表。

**认证要求**: 无

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/ca/crl
```

**成功响应 (200 OK)**

```json
{
  "crls": [
    {
      "artifact_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "CRL-2024-01-15",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 9. GET /ca/crl/{artifact_id}

下载指定的 CRL 文件。

**认证要求**: 无

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| artifact_id | UUID | CRL 工件 UUID |

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/ca/crl/550e8400-e29b-41d4-a716-446655440001 \
  -o ca-pdf.crl
```

**成功响应 (200 OK)**

返回 CRL 文件内容（Content-Type: application/pkix-crl）

---

## PDF签章模块

### 1. POST /pdf/sign

对单个 PDF 文档进行数字签章。

**认证要求**: Bearer Token（必需）

**请求参数（Form Data）**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| pdf_file | file | ✓ | PDF 文件 |
| certificate_id | string | ✓ | 证书 UUID |
| seal_id | string | ✗ | 印章 UUID（可选） |
| visibility | string | ✗ | 签章可见性（visible/invisible，默认：invisible） |
| page | integer | ✗ | 页码（可见签章必需） |
| x | float | ✗ | X 坐标（可见签章必需） |
| y | float | ✗ | Y 坐标（可见签章必需） |
| width | float | ✗ | 宽度（可见签章必需） |
| height | float | ✗ | 高度（可见签章必需） |
| reason | string | ✗ | 签章原因 |
| location | string | ✗ | 签章地点 |
| contact_info | string | ✗ | 联系方式 |
| use_tsa | boolean | ✗ | 是否包含时间戳（默认：false） |
| embed_ltv | boolean | ✗ | 是否嵌入 LTV 验证材料（默认：false） |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/pdf/sign \
  -H "Authorization: Bearer <access_token>" \
  -F "pdf_file=@document.pdf" \
  -F "certificate_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "seal_id=550e8400-e29b-41d4-a716-446655440002" \
  -F "visibility=visible" \
  -F "page=1" \
  -F "x=100" \
  -F "y=100" \
  -F "width=100" \
  -F "height=50" \
  -F "reason=批准" \
  -F "location=北京" \
  -F "use_tsa=true"
```

**成功响应 (200 OK)**

返回已签章的 PDF 文件（Content-Type: application/pdf）

响应头信息：
- `X-Document-ID`: 文档 ID
- `X-Certificate-ID`: 证书 ID
- `X-Seal-Id`: 印章 ID（如果使用）
- `X-TSA-Used`: 是否使用时间戳
- `X-LTV-Embedded`: 是否嵌入 LTV

---

### 2. POST /pdf/sign/batch

批量对多个 PDF 文档进行数字签章。

**认证要求**: Bearer Token（必需）

**请求参数（Form Data）**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| pdf_files | file[] | ✓ | PDF 文件列表 |
| certificate_id | string | ✓ | 证书 UUID |
| seal_id | string | ✗ | 印章 UUID（可选） |
| visibility | string | ✗ | 签章可见性 |
| page | integer | ✗ | 页码 |
| x | float | ✗ | X 坐标 |
| y | float | ✗ | Y 坐标 |
| width | float | ✗ | 宽度 |
| height | float | ✗ | 高度 |
| reason | string | ✗ | 签章原因 |
| location | string | ✗ | 签章地点 |
| contact_info | string | ✗ | 联系方式 |
| use_tsa | boolean | ✗ | 是否包含时间戳 |
| embed_ltv | boolean | ✗ | 是否嵌入 LTV |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/pdf/sign/batch \
  -H "Authorization: Bearer <access_token>" \
  -F "pdf_files=@document1.pdf" \
  -F "pdf_files=@document2.pdf" \
  -F "pdf_files=@document3.pdf" \
  -F "certificate_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "visibility=invisible"
```

**成功响应 (200 OK)**

```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "document1.pdf",
      "success": true,
      "document_id": "doc-001",
      "signed_at": "2024-01-15T10:30:00Z",
      "file_size": 102400,
      "error": null
    }
  ],
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "seal_id": null,
  "visibility": "invisible",
  "tsa_used": false,
  "ltv_embedded": false
}
```

---

### 3. POST /pdf/verify

验证 PDF 文档中的数字签章。

**认证要求**: Bearer Token（必需）

**请求参数（Form Data）**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| pdf_file | file | ✓ | 已签章的 PDF 文件 |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/pdf/verify \
  -H "Authorization: Bearer <access_token>" \
  -F "pdf_file=@signed-document.pdf"
```

**成功响应 (200 OK)**

```json
{
  "total_signatures": 2,
  "valid_signatures": 2,
  "trusted_signatures": 2,
  "all_signatures_valid": true,
  "all_signatures_trusted": true,
  "signatures": [
    {
      "field_name": "Signature1",
      "valid": true,
      "trusted": true,
      "docmdp_ok": true,
      "modification_level": "ALLOW_FORM_FILLING",
      "signing_time": "2024-01-15T10:30:00Z",
      "signer_common_name": "user@example.com",
      "signer_serial_number": "123456789",
      "summary": "Signature is valid",
      "timestamp_trusted": true,
      "timestamp_time": "2024-01-15T10:30:01Z",
      "timestamp_summary": "Timestamp is valid",
      "error": null
    }
  ]
}
```

---

### 4. POST /pdf/seals

上传企业数字印章。

**认证要求**: Bearer Token（必需）

**请求参数（Form Data）**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| name | string | ✓ | 印章名称（1-120 字符） |
| description | string | ✗ | 印章描述 |
| file | file | ✓ | 印章图片（PNG/SVG，≤5MB） |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/pdf/seals \
  -H "Authorization: Bearer <access_token>" \
  -F "name=公司印章" \
  -F "description=企业法人章" \
  -F "file=@company-seal.png"
```

**成功响应 (201 Created)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "name": "公司印章",
  "description": "企业法人章",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### 5. GET /pdf/seals

列出当前用户的所有企业印章。

**认证要求**: Bearer Token（必需）

**查询参数**

| 参数名 | 类型 | 默认 | 说明 |
|--------|------|------|------|
| skip | integer | 0 | 跳过的项数 |
| limit | integer | 10 | 返回的最大项数（1-100） |

**请求示例**

```bash
curl -X GET 'http://localhost:8000/api/v1/pdf/seals?skip=0&limit=10' \
  -H "Authorization: Bearer <access_token>"
```

**成功响应 (200 OK)**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "公司印章",
      "description": "企业法人章",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

---

### 6. DELETE /pdf/seals/{seal_id}

删除指定的企业印章。

**认证要求**: Bearer Token（必需）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| seal_id | UUID | 印章 UUID |

**请求示例**

```bash
curl -X DELETE http://localhost:8000/api/v1/pdf/seals/550e8400-e29b-41d4-a716-446655440003 \
  -H "Authorization: Bearer <access_token>"
```

**成功响应 (204 No Content)**

---

### 7. GET /pdf/seals/{seal_id}/image

下载企业印章的图片文件。

**认证要求**: Bearer Token（必需）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| seal_id | UUID | 印章 UUID |

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/pdf/seals/550e8400-e29b-41d4-a716-446655440003/image \
  -H "Authorization: Bearer <access_token>" \
  -o seal.png
```

**成功响应 (200 OK)**

返回图片文件（Content-Type: image/png 或 image/svg+xml）

---

## 用户管理模块

### 1. GET /users

列出所有用户（分页）。

**认证要求**: Bearer Token（Admin 角色）

**查询参数**

| 参数名 | 类型 | 默认 | 说明 |
|--------|------|------|------|
| skip | integer | 0 | 跳过的项数 |
| limit | integer | 10 | 返回的最大项数（1-100） |
| search | string | "" | 搜索关键词（用户名或邮箱） |
| role | string | null | 按角色过滤（user/admin） |
| is_active | boolean | null | 按活跃状态过滤 |

**请求示例**

```bash
curl -X GET 'http://localhost:8000/api/v1/users?skip=0&limit=20&is_active=true' \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200 OK)**

```json
{
  "items": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1,
  "skip": 0,
  "limit": 20
}
```

---

### 2. POST /users

创建新用户。

**认证要求**: Bearer Token（Admin 角色）

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| username | string | ✓ | 用户名（唯一） |
| email | string(email) | ✓ | 邮箱（唯一） |
| password | string | ✓ | 密码 |
| role | string | ✗ | 角色（user/admin，默认：user） |
| is_active | boolean | ✗ | 是否激活（默认：true） |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_doe",
    "email": "jane@example.com",
    "password": "securepassword123",
    "role": "user",
    "is_active": true
  }'
```

**成功响应 (201 Created)**

```json
{
  "id": 2,
  "username": "jane_doe",
  "email": "jane@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### 3. GET /users/{user_id}

获取指定用户的详细信息。

**认证要求**: Bearer Token（必需）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户 ID |

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/users/1 \
  -H "Authorization: Bearer <access_token>"
```

**成功响应 (200 OK)**

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

### 4. PATCH /users/{user_id}

编辑用户信息。

**认证要求**: Bearer Token（必需）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户 ID |

**请求参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| email | string(email) | 新邮箱（可选） |
| role | string | 新角色（仅限管理员修改） |
| is_active | boolean | 新状态（仅限管理员修改） |

**请求示例**

```bash
curl -X PATCH http://localhost:8000/api/v1/users/1 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }'
```

**成功响应 (200 OK)**

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "newemail@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

### 5. DELETE /users/{user_id}

删除指定的用户。

**认证要求**: Bearer Token（Admin 角色）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户 ID |

**请求示例**

```bash
curl -X DELETE http://localhost:8000/api/v1/users/2 \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (204 No Content)**

---

### 6. POST /users/{user_id}/reset-password

重置用户密码。

**认证要求**: Bearer Token（必需）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户 ID |

**请求参数**

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| new_password | string | ✓ | 新密码 |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/users/1/reset-password \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "newsecurepassword123"
  }'
```

**成功响应 (200 OK)**

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

### 7. POST /users/{user_id}/toggle-active

切换用户的活跃状态。

**认证要求**: Bearer Token（Admin 角色）

**路径参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| user_id | integer | 用户 ID |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/users/1/toggle-active \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200 OK)**

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "is_active": false,
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

## 审计日志模块

### 1. GET /audit/logs

查询审计日志。

**认证要求**: Bearer Token（Admin 角色）

**查询参数**

| 参数名 | 类型 | 默认 | 说明 |
|--------|------|------|------|
| limit | integer | 50 | 返回条数（1-200） |
| offset | integer | 0 | 跳过的条数 |
| event_type | string | null | 按事件类型过滤 |
| resource | string | null | 按资源类型过滤 |
| actor_id | integer | null | 按操作者 ID 过滤 |

**请求示例**

```bash
curl -X GET 'http://localhost:8000/api/v1/audit/logs?limit=50&event_type=user_created' \
  -H "Authorization: Bearer <admin_token>"
```

**成功响应 (200 OK)**

```json
{
  "total": 100,
  "limit": 50,
  "offset": 0,
  "logs": [
    {
      "id": 1,
      "actor_id": 1,
      "event_type": "user_created",
      "resource": "user",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "meta": {
        "user_id": 2,
        "username": "jane_doe"
      },
      "message": "User jane_doe created",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## 系统模块

### 1. GET /health

系统健康检查端点。

**认证要求**: 无

**请求示例**

```bash
curl -X GET http://localhost:8000/health
```

**成功响应 (200 OK)**

```json
{
  "status": "ok",
  "service": "ca-pdf"
}
```

---

## 常见场景示例

### 场景 1：完整的认证流程

```python
import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api/v1"

# 1. 用户登录
login_response = requests.post(f"{API_BASE}/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
tokens = login_response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 2. 使用 Token 调用受保护的 API
headers = {"Authorization": f"Bearer {access_token}"}
me_response = requests.get(f"{API_BASE}/auth/me", headers=headers)
print(me_response.json())

# 3. Token 轮换（获取新的 token 对）
refresh_response = requests.post(f"{API_BASE}/auth/refresh", json={
    "refresh_token": refresh_token
})
new_tokens = refresh_response.json()
access_token = new_tokens["access_token"]

# 4. 用户登出
logout_response = requests.post(f"{API_BASE}/auth/logout", 
    headers=headers,
    json={"refresh_token": refresh_token}
)
print(logout_response.json())
```

### 场景 2：生成根 CA 并签发证书

```python
import requests
import base64

API_BASE = "http://localhost:8000/api/v1"
admin_token = "your_admin_token"
headers = {"Authorization": f"Bearer {admin_token}"}

# 1. 生成根 CA
root_ca_response = requests.post(f"{API_BASE}/ca/root", headers=headers, json={
    "algorithm": "rsa_2048",
    "common_name": "ca-pdf Root CA",
    "organization": "Your Organization",
    "validity_days": 3650
})
print("Root CA generated:", root_ca_response.json())

# 2. 为用户签发证书
user_token = "user_access_token"
user_headers = {"Authorization": f"Bearer {user_token}"}
cert_response = requests.post(f"{API_BASE}/ca/certificates/issue",
    headers=user_headers,
    json={
        "common_name": "user@example.com",
        "organization": "Your Organization",
        "algorithm": "rsa_2048",
        "validity_days": 365,
        "p12_passphrase": "cert_password123"
    }
)
certificate = cert_response.json()
cert_id = certificate["certificate_id"]
print("Certificate issued:", cert_id)
```

### 场景 3：PDF 签章与验签

```python
import requests

API_BASE = "http://localhost:8000/api/v1"
user_token = "user_access_token"
headers = {"Authorization": f"Bearer {user_token}"}

# 1. 上传企业印章
with open("company_seal.png", "rb") as f:
    seal_response = requests.post(f"{API_BASE}/pdf/seals",
        headers=headers,
        files={"file": f},
        data={"name": "公司章", "description": "企业法人章"}
    )
seal_id = seal_response.json()["id"]
print("Seal uploaded:", seal_id)

# 2. 对 PDF 进行签章
with open("document.pdf", "rb") as f:
    sign_response = requests.post(f"{API_BASE}/pdf/sign",
        headers=headers,
        files={"pdf_file": f},
        data={
            "certificate_id": "cert_uuid_here",
            "seal_id": seal_id,
            "visibility": "visible",
            "page": 1,
            "x": 100,
            "y": 100,
            "width": 100,
            "height": 50,
            "reason": "批准",
            "use_tsa": True
        }
    )
# 返回已签章的 PDF 文件
signed_pdf = sign_response.content
with open("document-signed.pdf", "wb") as f:
    f.write(signed_pdf)

# 3. 验证签章
with open("document-signed.pdf", "rb") as f:
    verify_response = requests.post(f"{API_BASE}/pdf/verify",
        headers=headers,
        files={"pdf_file": f}
    )
verification_result = verify_response.json()
print("Verification result:", verification_result)
```

### 场景 4：批量签章

```python
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"
user_token = "user_access_token"
headers = {"Authorization": f"Bearer {user_token}"}

# 收集要签章的 PDF 文件
pdf_files = []
for pdf_path in Path(".").glob("*.pdf"):
    pdf_files.append(("pdf_files", open(pdf_path, "rb")))

# 批量签章
batch_response = requests.post(f"{API_BASE}/pdf/sign/batch",
    headers=headers,
    files=pdf_files,
    data={
        "certificate_id": "cert_uuid_here",
        "visibility": "invisible",
        "use_tsa": False
    }
)

result = batch_response.json()
print(f"Signed: {result['successful']}/{result['total']} files")
for item in result["results"]:
    if item["success"]:
        print(f"✓ {item['filename']}")
    else:
        print(f"✗ {item['filename']}: {item['error']}")
```

---

## 错误码参考

### 常见 HTTP 状态码

| 状态码 | 错误码 | 说明 | 常见原因 |
|--------|--------|------|----------|
| 400 | INVALID_INPUT | 请求数据验证失败 | 缺少必需字段、字段类型错误、值不合法 |
| 401 | UNAUTHORIZED | 认证失败 | 缺少 Token、Token 过期、凭证错误 |
| 403 | FORBIDDEN | 权限不足 | 角色权限不足、无权访问资源 |
| 404 | NOT_FOUND | 资源不存在 | 找不到指定的用户、证书、文件等 |
| 409 | ALREADY_EXISTS | 资源已存在 | 用户名/邮箱重复、Root CA 已存在 |
| 422 | INVALID_INPUT | 数据验证错误 | Pydantic 字段验证失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 | 未预期的异常 |

### 常见错误码

| 错误码 | 消息 | 说明 |
|--------|------|------|
| UNAUTHORIZED | Invalid credentials | 邮箱或密码不正确 |
| UNAUTHORIZED | Token has been revoked | Token 已被撤销 |
| UNAUTHORIZED | Invalid subject claim | Token 中的用户 ID 无效 |
| UNAUTHORIZED | User is not authorized | 用户未激活或不存在 |
| FORBIDDEN | Insufficient permissions | 用户角色权限不足 |
| FORBIDDEN | You do not have permission to... | 无权执行此操作 |
| FORBIDDEN | You cannot delete your own account | 不能删除自己的账户 |
| NOT_FOUND | Resource not found | 找不到请求的资源 |
| ALREADY_EXISTS | Resource already exists | 资源已存在（如用户、Root CA） |
| INVALID_INPUT | Invalid file format | 上传的文件格式无效 |
| INVALID_INPUT | File size exceeds maximum | 文件大小超过限制 |
| INVALID_INPUT | Invalid UUID format | UUID 格式不正确 |
| OPERATION_FAILED | Failed to generate root CA | 生成根 CA 失败 |
| OPERATION_FAILED | Failed to issue certificate | 签发证书失败 |
| OPERATION_FAILED | Failed to revoke certificate | 吊销证书失败 |
| OPERATION_FAILED | PDF signing operation failed | PDF 签章失败 |
| INVALID_STATE | Cannot delete the last active administrator | 不能删除最后一个活跃的管理员 |

### 错误响应示例

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

---

## 认证说明

### JWT Token 获取方式

通过 `POST /auth/login` 端点提交邮箱和密码获取 Token 对：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 在请求中使用 Token

在 HTTP 请求头中添加：

```
Authorization: Bearer <your_access_token>
```

### Token 刷新机制

- **Access Token**: 用于访问受保护的 API，有效期较短
- **Refresh Token**: 用于更新 Token 对，有效期较长
- 当 Access Token 过期时，使用 Refresh Token 调用 `POST /auth/refresh` 获取新的 Token 对
- Token 被撤销后无法继续使用

### 权限级别

| 角色 | 权限 | 说明 |
|------|------|------|
| user | 普通用户权限 | 可以签发自己的证书、上传印章、进行 PDF 签章 |
| admin | 管理员权限 | 可以管理所有用户、生成 Root CA、吊销证书、查看审计日志 |

---

**最后更新**: 2025-01-15  
**API 版本**: v1  
**总计端点数**: 30+
---

🔗 **相关文档**
- [README](./index.md)
- [开发指南](./DEVELOPMENT.md)
- [集成案例](./USER_GUIDE.md)
- [安全指南](./SECURITY.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

