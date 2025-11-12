# 安全指南 (SECURITY)
> 📖 **文档导航**：[README](./index.md) · [文档索引](./DOCUMENTATION.md) · [部署手册](./DEPLOYMENT.md) · [贡献指南](./CONTRIBUTING.md) · [系统架构](./ARCHITECTURE.md)
> 🎯 **适用人群**：安全负责人 / 管理员
> ⏱️ **预计阅读时间**：40 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本指南涵盖密钥管理、访问控制和合规要求。部署前请结合 [DEPLOYMENT.md](./DEPLOYMENT.md)，架构风险评估见 [ARCHITECTURE.md](./ARCHITECTURE.md)，安全变更流程参阅 [CONTRIBUTING.md](./CONTRIBUTING.md)。项目概览可回到 [README.md](./index.md)。

---

本文档提供 ca-pdf 项目的安全最佳实践和指南，旨在帮助用户和开发者安全地部署、运行和维护 ca-pdf 系统。

## 🔒 安全政策

### 责任披露

如果您发现 ca-pdf 中的安全漏洞，**请勿公开披露**，而应通过以下方式报告：

1. **发送 Email**：security@example.com（待确定实际邮箱地址）
2. **通过 GitHub**：创建私密安全 advisory（使用 GitHub 的安全功能）
3. **描述漏洞**：详细描述漏洞的性质、影响和复现步骤

### 报告内容

安全漏洞报告应包含：

- 漏洞类型（如 SQL 注入、XSS、认证绕过等）
- 漏洞位置（文件、函数、代码行）
- 漏洞描述和影响范围
- 复现步骤
- 建议的修复方案（可选）
- 您的联系方式

### 响应时间承诺

我们承诺：

- **初始响应**：24 小时内确认收到报告
- **评估**：72 小时内评估漏洞的严重性
- **修复**：
  - 严重漏洞：7 天内发布补丁
  - 中等漏洞：14 天内发布补丁
  - 低级漏洞：30 天内发布补丁
- **协调**：与报告者协调修复和披露时间

### 不公开漏洞

在以下情况下，我们会要求报告者不公开漏洞：

- 漏洞还未被修复
- 用户还未有时间进行更新
- 尚在进行安全协调

我们致力于在安全和透明之间找到平衡点，保护用户的同时也尊重报告者的权利。

---

## 🔑 密钥和凭证管理

### 2.1 ENCRYPTED_STORAGE_MASTER_KEY

**作用**：加密存储私钥、企业印章等敏感数据

**生成方式**：

```bash
openssl rand -hex 32
```

这会生成一个 64 字符（32 字节）的十六进制字符串，例如：
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**存储位置**：

- 开发环境：`.env` 文件（已在 `.gitignore` 中）
- 生产环境：**不提交到版本控制**，使用环境变量或密钥管理服务
  - Docker 密钥：`docker secret`
  - Kubernetes：`Secret` 资源
  - AWS：Secrets Manager
  - HashiCorp Vault：密钥管理系统

**轮换策略**：

1. **定期轮换**：建议每 90 天轮换一次
2. **轮换步骤**：
   - 生成新密钥
   - 使用新密钥重新加密所有敏感数据
   - 更新环境变量
   - 验证所有功能正常
   - 销毁旧密钥

**备份**：

- 安全备份密钥到加密存储介质
- 与根证书一起备份
- 防止单点故障
- 备份应物理隔离存储

### 2.2 JWT_SECRET_KEY

**作用**：JWT Token 签名密钥，用于签发和验证访问令牌

**生成方式**：

```bash
openssl rand -hex 32
```

**安全性要求**：

- 强随机值，不易猜测
- 至少 32 字节（256 位）
- 不使用默认值或弱密钥
- 不在代码中硬编码

**轮换考虑**：

- Token 过期后无需立即轮换密钥
- 可以维护多个密钥版本（用于验证旧 Token）
- 建议定期更换，但不影响有效期内的 Token
- 使用 Token 的 `kid`（Key ID）字段指定密钥版本

### 2.3 数据库密码

**强密码要求**：

- 最小长度：16 字符
- 包含大小写字母：A-Z 和 a-z
- 包含数字：0-9
- 包含特殊字符：!@#$%^&*
- 避免字典词汇、常见模式、个人信息

**示例安全密码**：
```
P@ssw0rd#Secure$2024
```

生成强密码：
```bash
openssl rand -base64 16 | tr -d "/"
```

**最佳实践**：

- 不使用默认密码（postgres/postgres）
- 为不同用户设置不同密码
- 应用用户密码只授予必需权限
- 定期更新数据库密码（建议 90 天）
- 使用密钥管理系统（Vault、Secrets Manager 等）

### 2.4 SSL/TLS 证书

**HTTPS 必需**：

生产环境**必须**使用 HTTPS，所有通信应加密。

**使用可信证书**：

推荐使用 Let's Encrypt 的免费证书：

```bash
# 使用 certbot 获取证书
sudo certbot certonly --standalone -d yourdomain.com

# 或使用 Docker 和 Traefik 自动管理
# （见 docker-compose.yml 配置）
```

**证书过期监控**：

- 设置证书过期提醒（提前 30 天）
- 使用 Let's Encrypt 的自动更新功能
- 监控日志中的 SSL/TLS 错误

**定期更新**：

- 及时更新 HTTPS 配置
- 使用现代 TLS 版本（1.2+）
- 定期审查密码套件配置

---

## 🔐 认证和授权安全

### 3.1 密码安全

**密码哈希**：

ca-pdf 使用 bcrypt 进行密码哈希：

```python
from app.core.security import get_password_hash, verify_password

# 生成密码哈希
hashed_password = get_password_hash("user_password")

# 验证密码
is_valid = verify_password("user_password", hashed_password)
```

bcrypt 特点：
- 自动加盐
- 计算成本随时间增加
- 防止彩虹表攻击

**密码强度要求**：

- 最小长度：8 字符
- 推荐长度：12+ 字符
- 应包含大小写字母、数字、特殊字符

在应用程序中强制密码强度：

```python
import re

def validate_password(password: str) -> bool:
    """验证密码是否满足强度要求"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*]', password):
        return False
    return True
```

**密码历史**：

- 防止重复使用最近的 5 个密码
- 记录密码变更历史
- 定期提醒用户更新密码

**密码过期**：

- 建议每 90 天强制更新密码
- 为长期未活动的账户强制重置
- 提供密码重置发现流程

### 3.2 Token 安全

**Token 有效期**：

```python
# 推荐配置
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 分钟
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 天
```

理由：
- Access Token 有效期短，降低泄露风险
- Refresh Token 用于获取新 Access Token
- 用户可在 Token 过期前刷新

**Token 吊销机制**：

实现 Token 黑名单防止已撤销 Token 的使用：

```python
# 在 Redis 或数据库中维护黑名单
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id: int = Column(Integer, primary_key=True)
    jti: str = Column(String, unique=True, index=True)  # JWT ID
    token_type: str = Column(String)
    user_id: int = Column(Integer, ForeignKey("user.id"))
    blacklisted_at: datetime = Column(DateTime, default=datetime.utcnow)
    expires_at: datetime = Column(DateTime)
```

**Token 传输**：

- **HTTPS Only**：始终通过 HTTPS 传输 Token
- **Authorization Header**：使用 `Authorization: Bearer <token>` 头
- 避免在 URL 参数中传递 Token

**Token 存储**：

前端存储建议：

- **HttpOnly Cookie**（推荐）：
  - 防止 XSS 攻击
  - 自动在请求中包含
  - 配置 `Secure` 和 `SameSite`

```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=True,  # HTTPS only
    samesite="strict"
)
```

- **localStorage**（次选）：
  - 可能被 XSS 脚本访问
  - 需要在 JavaScript 中手动发送

### 3.3 权限控制

**最小权限原则**：

- 每个用户和角色只有完成任务所必需的权限
- 定期审查和调整权限
- 移除不需要的权限

**RBAC 模型**：

ca-pdf 实现了简单的 RBAC：

```python
class UserRole(str, Enum):
    ADMIN = "admin"      # 管理员
    USER = "user"        # 普通用户
```

权限示例：

| 权限 | 管理员 | 普通用户 |
|-----|-------|--------|
| 管理用户 | ✓ | ✗ |
| 管理证书 | ✓ | ✗ |
| 签署 PDF | ✓ | ✓ |
| 验证签名 | ✓ | ✓ |
| 查看审计日志 | ✓ | ✗ |

**审计管理员操作**：

记录所有管理员操作以便审计：

```python
class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("user.id"))
    action: str = Column(String)  # 操作类型
    resource: str = Column(String)  # 资源类型
    resource_id: int = Column(Integer)  # 资源 ID
    changes: dict = Column(JSON)  # 改动内容
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)
    ip_address: str = Column(String)
    user_agent: str = Column(String)
```

**定期权限审查**：

- 每季度审查用户权限
- 移除离职员工的权限
- 评估过度授权的用户
- 记录权限变更

---

## 🔌 API 安全

### 4.1 输入验证

**Pydantic 模型验证**：

使用 Pydantic 进行所有输入验证：

```python
from pydantic import BaseModel, EmailStr, Field, validator

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('name')
    def name_alphanumeric(cls, v):
        if not v.replace(' ', '').isalnum():
            raise ValueError('Name must be alphanumeric')
        return v
```

**类型检查**：

- 所有输入必须指定类型
- 使用严格的类型定义
- 启用 mypy 严格模式

**长度限制**：

- 字符串：设置 `max_length`
- 文件上传：限制文件大小
- 列表：限制数组大小

```python
class PDFUpload(BaseModel):
    file_content: bytes = Field(..., max_length=104857600)  # 100MB
    filename: str = Field(..., max_length=255)
```

**格式检查**：

- Email：使用 `EmailStr`
- URL：使用 `HttpUrl`
- 日期时间：使用 `datetime`
- 枚举：使用 `Enum`

**SQL 注入防护**：

使用 SQLAlchemy ORM（自动参数化）：

```python
# ✓ 安全
user = db.query(User).filter(User.email == user_email).first()

# ✗ 不安全（不要使用原始 SQL）
user = db.execute(f"SELECT * FROM user WHERE email = '{user_email}'")
```

**XSS 防护**：

- 对输出内容进行转义
- 在前端使用现代框架（自动转义）
- 避免 `innerHTML` 使用

### 4.2 速率限制

**认证端点速率限制**：

防止暴力破解和 DDoS：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # 每分钟最多 5 次
async def login(credentials: LoginRequest):
    # ...
```

推荐限制：

- `/auth/login`：5 次/分钟
- `/auth/register`：3 次/小时
- 通用 API：100 次/小时
- 文件上传：10 次/小时

**基于 IP 和用户的限制**：

```python
@app.post("/api/pdf/sign")
@limiter.limit("100/hour;10/minute")  # 每小时 100 次，每分钟 10 次
async def sign_pdf(request: Request):
    # 基于 IP 地址的限制
    # 也可以对认证用户实施基于用户 ID 的限制
```

### 4.3 CORS 配置

**明确指定允许的源**：

```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://api.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 不使用通配符 "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**不使用通配符**：

```python
# ✗ 不安全
allow_origins=["*"]

# ✓ 安全
allow_origins=["https://trusted.com", "https://app.example.com"]
```

**配置正确的 HTTP 方法**：

- GET：用于查询
- POST：用于创建
- PUT/PATCH：用于更新
- DELETE：用于删除
- 不需要的方法应禁用

**Preflight 请求**：

CORS preflight 请求自动处理，无需特殊配置。

---

## 🛡️ 数据安全

### 5.1 加密存储

**敏感数据**：

- 私钥（Root CA、中间 CA、用户证书）
- 企业印章图片
- 用户敏感信息

**加密算法**：

使用 AES-256 加密：

```python
from cryptography.fernet import Fernet

# 从 ENCRYPTED_STORAGE_MASTER_KEY 生成加密密钥
key = os.getenv("ENCRYPTED_STORAGE_MASTER_KEY").encode()
cipher = Fernet(key)

# 加密
encrypted_data = cipher.encrypt(sensitive_data)

# 解密
decrypted_data = cipher.decrypt(encrypted_data)
```

**密钥导出**：

使用 PBKDF2 导出密钥：

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
key = kdf.derive(password)
```

**数据完整性校验**：

使用 HMAC 验证数据完整性：

```python
import hmac
import hashlib

def compute_hmac(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def verify_hmac(data: bytes, signature: str, key: bytes) -> bool:
    expected = compute_hmac(data, key)
    return hmac.compare_digest(expected, signature)
```

### 5.2 数据库安全

**最小化权限**：

为应用创建专用数据库用户，只授予必需的权限：

```sql
-- 创建应用用户
CREATE USER ca_pdf_app WITH PASSWORD 'secure_password';

-- 授予必需权限
GRANT CONNECT ON DATABASE ca_pdf TO ca_pdf_app;
GRANT USAGE ON SCHEMA public TO ca_pdf_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ca_pdf_app;

-- 不授予创建表、索引等权限
```

**连接 SSL/TLS**：

在 PostgreSQL 连接字符串中启用 SSL：

```python
# 在 .env 中
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db?ssl=require"
```

**备份加密**：

```bash
# 加密备份
pg_dump ca_pdf | openssl enc -aes-256-cbc -e > backup.sql.enc

# 解密备份
openssl enc -aes-256-cbc -d < backup.sql.enc | psql ca_pdf
```

**访问控制**：

- 防火墙：限制数据库连接源
- IP 白名单：仅允许应用服务器 IP
- VPN：通过 VPN 访问生产数据库
- 网络隔离：在私有网络中运行数据库

### 5.3 文件安全

**上传文件验证**：

```python
from fastapi import File, UploadFile
from pathlib import Path

ALLOWED_TYPES = {"image/png", "image/svg+xml", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload(file: UploadFile) -> bool:
    # 检查文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError(f"File type {file.content_type} not allowed")
    
    # 检查文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds limit")
    
    # 扫描恶意内容（可选，使用 ClamAV 等）
    # ...
    
    return True
```

**安全存储位置**：

- 在 `ENCRYPTED_STORAGE_MASTER_KEY` 控制的位置存储敏感文件
- 不在 Web 根目录存储
- 为不同文件类型使用不同目录

**访问权限控制**：

```python
# 只有文件所有者可以访问
@app.get("/api/files/{file_id}")
async def get_file(file_id: int, current_user: User):
    file = db.query(File).filter(File.id == file_id).first()
    if file.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    # ...
```

**防止目录遍历**：

```python
import os
from pathlib import Path

def secure_file_path(base_dir: str, filename: str) -> str:
    """防止目录遍历攻击"""
    base = Path(base_dir).resolve()
    file_path = (base / filename).resolve()
    
    if not str(file_path).startswith(str(base)):
        raise ValueError("Access denied")
    
    return str(file_path)
```

### 5.4 审计日志

**记录敏感操作**：

```python
async def log_audit(
    user_id: int,
    action: str,
    resource: str,
    resource_id: int,
    changes: dict,
    request: Request
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        changes=changes,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    await db.commit()
```

**日志包含信息**：

- 用户 ID
- 操作类型（创建、修改、删除等）
- 资源类型和 ID
- 修改的具体内容
- 时间戳
- IP 地址
- User-Agent

**日志不可篡改**：

- 将日志写入只读存储
- 定期备份日志
- 使用数字签名防止篡改

**定期备份**：

```bash
# 每周备份审计日志
0 0 * * 0 pg_dump ca_pdf | gzip > /backup/audit_$(date +%Y%m%d).sql.gz
```

---

## 📡 通信安全

### 6.1 HTTPS/TLS

**生产环境必须使用 HTTPS**：

所有生产部署必须使用 HTTPS，生产环境不应允许 HTTP。

**TLS 版本**：

配置 TLS 1.2 或更高：

```python
# 在 Traefik 或反向代理中配置
# 禁用 TLS 1.0 和 1.1
```

**强密码套件**：

```
# 推荐的密码套件
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
```

**HSTS 头配置**：

```python
from fastapi import Response

@app.middleware("http")
async def add_hsts(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Strict-Transport-Security"] = \
        "max-age=31536000; includeSubDomains; preload"
    return response
```

### 6.2 API 通信

**敏感操作使用 POST/PATCH/DELETE**：

- 不使用 GET 进行修改操作
- 敏感数据不在 URL 中传递

```python
# ✗ 不安全
GET /api/users/delete?id=123

# ✓ 安全
DELETE /api/users/123
```

**Content-Type 验证**：

```python
from fastapi import Header

@app.post("/api/data")
async def create_data(
    request_body: DataModel,
    content_type: str = Header(...)
):
    if "application/json" not in content_type:
        raise HTTPException(status_code=400, detail="Invalid content type")
```

**请求签名**（高安全场景）：

对于高度敏感的操作，可使用请求签名：

```python
import hmac
import hashlib

def verify_signature(request_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## 📦 依赖和更新

### 7.1 依赖管理

**使用 Lock 文件**：

- `poetry.lock`：Python 依赖
- `package-lock.json`：Node.js 依赖
- 所有 lock 文件提交到版本控制

**定期检查漏洞**：

```bash
# Python 依赖漏洞检查
safety check

# Node.js 依赖漏洞检查
npm audit

# Docker 镜像漏洞检查
trivy image myimage:latest
```

**及时更新依赖**：

```bash
# 检查过时依赖
poetry show --outdated

# 更新依赖
poetry update

# Node.js
npm outdated
npm update
```

**审查大版本更新**：

- 更新前阅读 CHANGELOG
- 检查破坏性变更
- 在测试环境验证
- 运行完整测试套件

### 7.2 安全更新

**订阅安全公告**：

- GitHub 安全警报
- CVE 数据库（nvd.nist.gov）
- 项目安全邮件列表

**优先级更新安全补丁**：

- 严重漏洞：立即更新
- 高优先级：24 小时内更新
- 中等优先级：7 天内更新

**测试兼容性**：

在更新后运行完整测试：

```bash
# 后端
poetry run pytest

# 前端
npm run test

# 集成测试
npm run test:integration
```

**快速部署安全更新**：

- 为安全更新建立快速通道
- 可能跳过正常审查流程
- 紧急部署到生产环境

---

## 🚀 部署安全

### 8.1 环境隔离

**开发/测试/生产分离**：

维护独立的环境，每个环境有独立配置：

```
开发环境 (development)
├── 数据库：SQLite 本地
├── 日志：详细日志
├── 凭证：演示凭证
└── 调试：启用

测试环境 (staging)
├── 数据库：PostgreSQL 隔离实例
├── 日志：标准日志
├── 凭证：测试凭证
└── 调试：禁用

生产环境 (production)
├── 数据库：PostgreSQL 主实例
├── 日志：精简日志
├── 凭证：生产凭证
└── 调试：禁用
```

**各环境独立配置**：

```python
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

# 根据环境加载配置
ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "production":
    DEBUG = False
    ALLOWED_HOSTS = ["api.example.com"]
    # ...
```

**生产凭证独立管理**：

- 不在代码中存储
- 不在容器镜像中
- 使用密钥管理服务
- 定期轮换

### 8.2 容器安全

**使用官方镜像**：

```dockerfile
# ✓ 安全
FROM python:3.11-slim-bullseye

# ✗ 避免
FROM ubuntu:latest
```

**定期更新镜像**：

```bash
# 更新基础镜像
docker pull python:3.11-slim-bullseye

# 重新构建应用镜像
docker build -t ca-pdf:latest .
```

**扫描镜像漏洞**：

```bash
# 使用 Trivy
trivy image ca-pdf:latest

# 使用 Snyk
snyk container test ca-pdf:latest
```

**最小化镜像大小**：

```dockerfile
FROM python:3.11-slim

# 删除不需要的包
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 使用多阶段构建
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

**不在容器中存储密钥**：

```dockerfile
# ✗ 不安全
ENV SECRET_KEY="my-secret-key"

# ✓ 安全（使用运行时环境变量）
# 在 docker-compose.yml 或 Kubernetes 中设置
```

### 8.3 网络安全

**防火墙配置**：

```bash
# 只允许必要的端口
# 允许 HTTPS (443)
ufw allow 443/tcp

# 允许 HTTP (80) 用于 HTTP->HTTPS 重定向
ufw allow 80/tcp

# 禁止其他流量
ufw default deny incoming
```

**IP 白名单**：

```python
# 在 Nginx 或 Traefik 中配置
# 仅允许特定 IP 访问管理接口
allow_ips = ["10.0.0.0/8", "192.168.0.0/16"]
```

**VPN 访问**：

为生产环境的管理接口使用 VPN。

**网络隔离**：

```
                ┌─────────────────┐
                │   互联网        │
                └────────┬────────┘
                         │
                    ┌────▼────┐
                    │ Traefik │ (reverse proxy)
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐      ┌──▼────┐      ┌──▼────┐
    │ 前端     │      │ 后端   │      │ 其他   │
    └─────────┘      └───┬───┘      └───────┘
                         │
                    ┌────▼────┐
                    │数据库   │ (内部网络)
                    └─────────┘
```

---

## 📊 监控和响应

### 9.1 安全监控

**异常登录检测**：

```python
# 记录登录尝试，检测异常行为
class LoginAttempt(Base):
    __tablename__ = "login_attempt"
    
    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("user.id"))
    ip_address: str = Column(String)
    user_agent: str = Column(String)
    success: bool = Column(Boolean)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)

# 检测异常登录
async def detect_abnormal_login(user_id: int, ip: str) -> bool:
    recent_logins = db.query(LoginAttempt).filter(
        LoginAttempt.user_id == user_id,
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    # 检测多个不同 IP 登录
    unique_ips = set(login.ip_address for login in recent_logins)
    if len(unique_ips) > 5:
        return True  # 异常行为
    
    return False
```

**暴力破解检测**：

```python
async def check_brute_force(username: str) -> bool:
    failed_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.username == username,
        LoginAttempt.success == False,
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=5)
    ).count()
    
    if failed_attempts >= 5:
        # 锁定账户或增加延迟
        return True
    return False
```

**SQL 注入尝试检测**：

```python
# 监控日志中的 SQL 错误
# 配置日志告警
```

**DDoS 防护**：

- 使用 CloudFlare、AWS Shield 等 DDoS 防护服务
- 配置速率限制
- 监控异常流量

**日志监控**：

```bash
# 监控关键日志事件
grep -i "error\|failed\|unauthorized" /var/log/app.log

# 使用 ELK Stack 或 Splunk 进行日志聚合分析
```

### 9.2 事件响应

**安全事件上报流程**：

1. **发现**：监控系统检测到异常
2. **确认**：验证是否为真正的安全事件
3. **隔离**：隔离受影响系统
4. **分析**：分析事件原因和影响范围
5. **恢复**：恢复系统到安全状态
6. **通知**：通知相关人员和用户
7. **后续**：总结经验和改进

**应急处理步骤**：

```
1. 激活应急响应计划
2. 组建应急小组
3. 隔离受影响系统
4. 保存日志和证据
5. 分析和遏制
6. 恢复系统
7. 进行事后分析
```

**数据泄露通知**：

- 及时通知受影响用户
- 提供具体建议（如修改密码）
- 记录通知内容和时间
- 向监管机构报告（如需要）

**恢复计划**：

- 备份策略：每天备份，异地存储
- 灾难恢复计划：定期演练
- 恢复时间目标（RTO）：2 小时
- 恢复点目标（RPO）：1 小时

---

## ✅ 安全最佳实践清单

确保您的部署符合以下实践：

- ✓ **HTTPS**：所有通信使用 HTTPS，不允许 HTTP
- ✓ **密钥轮换**：定期轮换加密密钥和密码
- ✓ **最小权限**：遵循最小权限原则
- ✓ **定期备份**：每天备份数据，异地存储
- ✓ **日志监控**：实时监控和分析日志
- ✓ **依赖更新**：定期检查和更新依赖
- ✓ **安全审计**：定期进行安全审计
- ✓ **员工培训**：定期安全培训

---

## ⚠️ 常见安全问题

| 问题 | 风险 | 解决方案 |
|-----|------|---------|
| 弱密码 | 账户被盗 | 强制使用强密码，定期更新 |
| 未加密传输 | 数据泄露 | 使用 HTTPS/TLS 1.2+ |
| 过度权限 | 权限滥用 | 遵循最小权限原则 |
| 依赖漏洞 | 系统被入侵 | 定期检查和更新依赖 |
| 配置错误 | 安全漏洞 | 使用标准配置，定期审查 |
| 日志不完整 | 无法追踪 | 启用详细日志，长期保留 |
| 备份不足 | 数据丢失 | 多地备份，定期测试恢复 |
| 缺乏监控 | 未能及时响应 | 部署监控和告警 |

---

## 📋 合规要求

### GDPR（通用数据保护条例）

- 用户数据保护：加密存储和传输
- 访问权利：提供数据导出功能
- 遗忘权：支持数据删除
- 隐私政策：清晰描述数据使用

### PCI-DSS（支付卡数据安全标准）

如果处理支付卡数据：

- 网络安全：防火墙和网络隔离
- 数据保护：强加密
- 访问控制：严格的权限管理
- 定期测试：安全漏洞扫描

### ISO 27001（信息安全管理系统）

- 信息安全政策：制定并实施
- 资产管理：记录和分类资产
- 访问控制：严格的访问控制
- 事件响应：应急响应计划

### 行业特定要求

根据您所在行业，可能有其他要求：

- **医疗健康**：HIPAA（美国）、DHHS（澳大利亚）
- **金融服务**：PCI-DSS、SOX（美国）
- **电子签署**：eIDAS（欧盟）、UETA（美国）

---

## 🔍 安全审计

### 定期安全审计

建议每 6 个月进行一次全面的安全审计：

**审计检查清单**：

- 代码审查：检查是否有安全漏洞
- 依赖审计：检查是否有已知漏洞
- 访问控制审查：检查是否有过度权限
- 密钥轮换：检查最后轮换时间
- 日志审查：检查是否有异常活动
- 备份测试：验证备份是否可恢复
- 漏洞扫描：使用自动化工具扫描
- 渗透测试：进行外部安全测试（建议）

### 安全漏洞扫描工具

**Python 依赖**：

```bash
# Safety
pip install safety
safety check

# Bandit
pip install bandit
bandit -r app/
```

**前端依赖**：

```bash
# npm audit
npm audit

# Snyk
npm install -g snyk
snyk test
```

**容器镜像**：

```bash
# Trivy
trivy image ca-pdf:latest

# Anchore
anchore-cli image add ca-pdf:latest
anchore-cli image wait ca-pdf:latest
anchore-cli image vuln ca-pdf:latest all
```

**静态代码分析**：

```bash
# SonarQube（本地部署）
# 集成到 CI/CD 流程

# Code scanning via GitHub Advanced Security
# 自动扫描 PR 中的安全问题
```

---

## 🛡️ 安全事件案例学习

### 案例 1：SQL 注入攻击

**问题**：使用字符串拼接构建 SQL 查询

```python
# ✗ 不安全
query = f"SELECT * FROM users WHERE email = '{email}'"
db.execute(query)

# ✓ 安全
query = select(User).where(User.email == email)
result = await db.execute(query)
```

**学习**：始终使用 ORM 或参数化查询

### 案例 2：敏感数据泄露

**问题**：在日志中记录敏感信息

```python
# ✗ 不安全
logger.info(f"User password: {password}")
logger.info(f"API key: {api_key}")

# ✓ 安全
logger.info(f"User login attempt")
logger.debug(f"User password: {'*' * len(password)}")
```

**学习**：永远不要在日志中记录密钥、密码或个人信息

### 案例 3：CORS 配置错误

**问题**：允许所有源访问 API

```python
# ✗ 不安全
allow_origins=["*"]
allow_credentials=True  # 与 "*" 不兼容

# ✓ 安全
allow_origins=[
    "https://app.example.com",
    "https://admin.example.com"
]
allow_credentials=True
```

**学习**：明确指定允许的源，避免通配符

### 案例 4：弱密码策略

**问题**：允许弱密码

```python
# ✗ 不安全
if len(password) >= 6:
    return True

# ✓ 安全
def is_strong_password(password: str) -> bool:
    return (
        len(password) >= 12 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*" for c in password)
    )
```

**学习**：执行强密码政策，定期更新

### 案例 5：过期依赖漏洞

**问题**：未及时更新依赖

```bash
# 定期检查
poetry show --outdated
npm outdated

# 及时更新
poetry update
npm update
```

**学习**：维护依赖的最新版本，订阅安全公告

---

## 📊 安全性能指标

建议跟踪以下指标以评估安全态势：

| 指标 | 目标 | 频率 |
|-----|------|------|
| 代码覆盖率 | >= 80% | 每个 PR |
| 已知漏洞数 | 0（严重/高），< 5（中等） | 每周 |
| 漏洞修复时间 | 严重：24h，高：72h | 追踪 |
| 安全审计时间 | 每 6 个月 | 计划 |
| 渗透测试时间 | 每 12 个月 | 计划 |
| 员工培训完成率 | 100% | 每年 |
| 备份成功率 | 100% | 每周 |
| 日志保留率 | 100% | 持续 |

---

## 👥 团队安全职责

不同角色在安全中的职责：

### 开发人员

- 编写安全的代码
- 遵循编码规范
- 进行自主测试
- 审查代码安全性
- 及时报告安全问题

### 安全工程师

- 进行安全审计
- 评估新技术的安全性
- 制定安全政策
- 进行渗透测试
- 处理安全事件

### 运维工程师

- 配置安全的基础设施
- 实施访问控制
- 监控安全告警
- 管理密钥和凭证
- 维护备份

### 项目经理

- 优先考虑安全需求
- 为安全活动分配资源
- 跟踪安全指标
- 沟通风险和问题

### 管理层

- 制定安全文化
- 分配适当的资源
- 支持安全培训
- 定期审查安全状况

---

## 📞 安全联系方式

报告安全漏洞：

- **Email**：security@example.com（待确定）
- **GitHub Security Advisory**：使用 GitHub 的私密安全 advisory 功能
- **Responsible Disclosure**：遵循负责任披露原则

---

## 📚 相关资源

**安全框架和标准**：

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST 网络安全框架](https://www.nist.gov/cyberframework)

**安全测试工具**：

- [OWASP ZAP](https://www.zaproxy.org/)
- [Burp Suite](https://portswigger.net/burp)
- [Bandit](https://bandit.readthedocs.io/)
- [Safety](https://safety.readthedocs.io/)

**安全通告**：

- [FBI 网络安全警告](https://www.fbi.gov/news/lists)
- [CISA 安全公告](https://www.cisa.gov/news-events)
- [NVD 漏洞数据库](https://nvd.nist.gov/)

**密码安全**：

- [Have I Been Pwned](https://haveibeenpwned.com/)
- [密码强度测试](https://www.kaspersky.com/password-checker)

**持续学习**：

- [OWASP 开发者指南](https://cheatsheetseries.owasp.org/)
- [OWASP 测试指南](https://owasp.org/www-project-web-security-testing-guide/)
- [安全编码实践](https://www.securecoding.cert.org/)

---

## 📋 版本历史

| 版本 | 日期 | 更改 |
|-----|------|------|
| 1.0 | 2025-01-01 | 初始版本 |

---

感谢您重视 ca-pdf 的安全。我们致力于维护一个安全的平台。如有任何安全疑虑或建议，欢迎通过上述方式联系我们。

**最后更新**：2025 年 1 月

---

## 重要提醒

- 安全是一个持续的过程，不是一次性的活动
- 定期审查和更新安全政策
- 建立安全文化，所有人都应参与
- 保持警觉，及时发现和应对威胁
- 学习最新的安全知识和最佳实践
---

🔗 **相关文档**
- [部署手册](./DEPLOYMENT.md)
- [系统架构](./ARCHITECTURE.md)
- [贡献指南](./CONTRIBUTING.md)
- [故障排查](./TROUBLESHOOTING.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

