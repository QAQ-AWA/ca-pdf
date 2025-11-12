# ca-pdf 开发指南

> **📖 文档导航** | [README](README.md) | [架构文档](ARCHITECTURE.md) | [API文档](API.md) | [贡献指南](CONTRIBUTING.md)
> 
> **👥 适用人群**: 开发者、贡献者  
> **⏱️ 阅读时间**: 约 15 分钟

---

本文档为 ca-pdf 项目的贡献者和开发人员提供完整的开发指南，包括环境设置、项目结构、代码规范、开发流程和调试技巧。

**项目地址**: https://github.com/QAQ-AWA/ca-pdf  
**联系邮箱**: 7780102@qq.com

## 目录

- [开发环境设置](#开发环境设置)
- [项目结构详解](#项目结构详解)
- [代码规范](#代码规范)
- [后端开发](#后端开发)
- [前端开发](#前端开发)
- [常见开发场景](#常见开发场景)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [常见问题](#常见问题)

---

## 开发环境设置

### 系统要求

- **操作系统**：Linux (Ubuntu 20.04+)、macOS (Big Sur+) 或 Windows (WSL2)
- **Python**：3.11+ (后端)
- **Node.js**：18.0.0+ 和 npm 9.0.0+ (前端)
- **Git**：2.30+
- **Docker**（可选，用于本地数据库）：23.0+

### IDE 推荐

#### VSCode 推荐扩展

```json
{
  "extensions": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-pyright.pyright",
    "charliermarsh.ruff",
    "GitHub.copilot",
    "ms-vscode.makefile-tools",
    "ES7+React/Redux/React-Native snippets",
    "TSLint",
    "Prettier - Code formatter",
    "Error Lens"
  ]
}
```

#### VSCode Settings

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": ["--strict"]
}
```

### 必需工具安装

#### 1. 克隆仓库

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
```

#### 2. 后端环境配置

```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 进入后端目录
cd backend

# 安装依赖（会自动创建虚拟环境）
poetry install

# 激活虚拟环境
poetry shell

# 返回项目根目录
cd ..
```

#### 3. 前端环境配置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 返回项目根目录
cd ..
```

#### 4. 数据库配置

**方案 A：使用 Docker Compose（推荐）**

```bash
docker-compose up -d postgres
```

**方案 B：本地 PostgreSQL**

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# 启动服务
sudo systemctl start postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE USER app_user WITH PASSWORD 'secure_password';
CREATE DATABASE app_db OWNER app_user;
ALTER ROLE app_user SET client_encoding TO 'utf8';
ALTER ROLE app_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE app_user SET default_transaction_deferrable TO on;
ALTER ROLE app_user SET default_transaction_read_committed TO on;
```

#### 5. 环境变量配置

```bash
# 复制环境变量文件
cp .env.example .env

# 生成安全密钥
openssl rand -base64 32  # SECRET_KEY
openssl rand -base64 32  # ENCRYPTED_STORAGE_MASTER_KEY

# 编辑 .env 文件，填入以下内容
cat > .env << EOF
APP_NAME=ca-pdf
SECRET_KEY=<生成的32字节密钥>
ENCRYPTED_STORAGE_MASTER_KEY=<生成的32字节Fernet密钥>
DATABASE_URL=postgresql+asyncpg://app_user:secure_password@localhost:5432/app_db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=AdminPass123!
BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
EOF
```

---

## 项目结构详解

```
ca-pdf/
├── backend/
│   ├── app/
│   │   ├── api/                    # REST API 路由
│   │   │   ├── endpoints/          # 端点实现
│   │   │   │   ├── auth.py         # 认证端点
│   │   │   │   ├── users.py        # 用户管理
│   │   │   │   ├── ca.py           # 证书颁发机构
│   │   │   │   ├── pdf_signing.py  # PDF 签章
│   │   │   │   ├── seals.py        # 企业印章
│   │   │   │   └── audit.py        # 审计日志
│   │   │   ├── dependencies.py     # 依赖注入（认证、权限）
│   │   │   └── routes.py           # 路由聚合
│   │   ├── models/                 # SQLAlchemy ORM 模型
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── certificate.py      # 证书模型
│   │   │   ├── pdf_signature.py    # 签章记录
│   │   │   ├── audit_log.py        # 审计日志
│   │   │   └── base.py             # 基础模型
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── crud/                   # 数据库 CRUD 操作
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── ca_service.py       # CA 证书业务逻辑
│   │   │   ├── pdf_service.py      # PDF 签章业务逻辑
│   │   │   ├── seal_service.py     # 企业印章业务逻辑
│   │   │   └── audit_service.py    # 审计日志业务逻辑
│   │   ├── core/
│   │   │   ├── config.py           # 环境变量配置
│   │   │   ├── security.py         # 认证、密码处理
│   │   │   ├── encryption.py       # 加密/解密工具
│   │   │   ├── errors.py           # 自定义异常
│   │   │   └── constants.py        # 常量定义
│   │   ├── db/
│   │   │   ├── session.py          # 数据库会话工厂
│   │   │   ├── base.py             # SQLAlchemy 基础配置
│   │   │   └── init_db.py          # 数据库初始化
│   │   └── main.py                 # FastAPI 应用入口
│   ├── migrations/                 # Alembic 数据库迁移
│   ├── tests/                      # 后端测试
│   │   ├── conftest.py             # pytest 配置和公共 fixture
│   │   ├── test_auth.py            # 认证测试
│   │   ├── test_certificate_authority.py  # CA 测试
│   │   ├── test_pdf_signing.py     # PDF 签章测试
│   │   ├── test_seals_api.py       # 企业印章测试
│   │   └── ...
│   ├── pyproject.toml              # Poetry 依赖管理
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # 页面组件
│   │   │   ├── LoginPage.tsx
│   │   │   ├── LogoutPage.tsx
│   │   │   ├── NotFoundPage.tsx
│   │   │   └── dashboard/          # 仪表板页面
│   │   ├── components/             # 可复用 UI 组件
│   │   │   ├── ui/                 # 基础 UI 组件
│   │   │   ├── Navigation.tsx      # 导航栏
│   │   │   ├── ProtectedRoute.tsx  # 路由保护
│   │   │   └── ...
│   │   ├── contexts/               # React Context
│   │   │   └── AuthContext.tsx     # 认证上下文
│   │   ├── lib/                    # 工具和 API 客户端
│   │   │   ├── httpClient.ts       # HTTP 请求封装
│   │   │   ├── apiFetch.ts         # API 调用封装
│   │   │   ├── caApi.ts            # CA 相关 API
│   │   │   ├── signingApi.ts       # 签章相关 API
│   │   │   ├── sealApi.ts          # 企业印章 API
│   │   │   └── env.ts              # 环境变量
│   │   ├── types/                  # TypeScript 类型定义
│   │   ├── hooks/                  # 自定义 Hooks
│   │   ├── App.tsx                 # 应用入口
│   │   ├── main.tsx                # 渲染入口
│   │   └── styles.css              # 全局样式
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docker-compose.yml              # 完整栈编排
├── Makefile                        # 快捷命令
├── deploy.sh                       # 一键部署
├── .env.example                    # 环境变量示例
└── README.md
```

---

## 代码规范

### Python 代码规范

#### 1. 使用 PEP 8 (通过 Black 强制)

```python
# ✓ 正确
def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> Awaitable[User | None]:
    """Authenticate user with email and password."""
    pass


# ✗ 错误
def authenticate_user(session: AsyncSession, email: str, password: str) -> Awaitable[User | None]:
    pass
```

#### 2. 导入排序 (使用 isort)

```python
# 标准库
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 第三方库
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 本地模块
from app.api.dependencies import get_current_user
from app.crud import user as user_crud
from app.models import User
```

#### 3. 类型提示 (严格模式)

```python
from typing import Awaitable

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

# ✓ 正确 - 所有参数和返回值都有类型注解
async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Authenticate user with email and password."""
    pass

# ✗ 错误 - 缺少返回类型
async def authenticate_user(session: AsyncSession, email: str, password: str):
    pass
```

#### 4. 命名约定

```python
# 函数和变量：snake_case
def create_access_token(user_id: int) -> str:
    pass

# 类：PascalCase
class UserSchema(BaseModel):
    pass

# 常量：UPPER_SNAKE_CASE
MAX_FILE_SIZE = 52_428_800  # 50 MB
DEFAULT_TIMEOUT = 30
```

### TypeScript/React 代码规范

#### 1. 严格模式配置

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true
  }
}
```

#### 2. 函数式组件 + Hooks

```typescript
// ✓ 正确 - 函数式组件
interface LoginFormProps {
  onSubmit: (credentials: LoginCredentials) => Promise<void>;
  isLoading?: boolean;
}

export const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ email, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form content */}
    </form>
  );
};

// ✗ 错误 - 类组件（不推荐）
class LoginForm extends React.Component {
  // ...
}
```

#### 3. 文件和文件夹命名

```
components/
  ├── LoginForm.tsx           # PascalCase
  ├── ui/
  │   ├── Button.tsx
  │   ├── Input.tsx
  │   └── Card.tsx
  └── dashboard/
      ├── CertificateList.tsx
      └── StatisticsPanel.tsx

hooks/
  ├── useAuth.ts             # useXXX 格式
  ├── useForm.ts
  └── usePDF.ts

lib/
  ├── httpClient.ts          # camelCase
  ├── apiFetch.ts
  └── validators.ts
```

### 提交消息规范 (Conventional Commits)

```bash
# ✓ 正确格式
git commit -m "feat(auth): add JWT token refresh endpoint"
git commit -m "fix(pdf): resolve signature verification issue"
git commit -m "docs(development): update API documentation"
git commit -m "test(ca): add certificate generation tests"
git commit -m "refactor(core): simplify encryption module"
git commit -m "chore(deps): upgrade FastAPI to 0.110.0"

# 提交消息结构
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>

# Types: feat, fix, docs, style, refactor, test, chore, ci, perf
# Scopes: auth, users, ca, pdf, seals, audit, core, db, api, frontend, etc.
```

### 分支命名规范

```bash
# 功能分支
git checkout -b feature/add-jwt-refresh

# Bug 修复
git checkout -b bugfix/signature-verification

# 文档更新
git checkout -b docs/development-guide

# 发布分支
git checkout -b release/v0.2.0

# 热修复
git checkout -b hotfix/security-patch
```

---

## 后端开发

### 添加新的 API 端点

#### 步骤 1：定义 Pydantic Schema

创建 `backend/app/schemas/certificate.py`：

```python
from pydantic import BaseModel, Field

class CertificateRequest(BaseModel):
    """Request model for certificate creation."""
    subject_cn: str = Field(..., min_length=1)
    validity_days: int = Field(default=365, gt=0)

class CertificateResponse(BaseModel):
    """Response model for certificate."""
    id: int
    subject_cn: str
    valid_from: datetime
    valid_to: datetime

    class Config:
        from_attributes = True
```

#### 步骤 2：创建 CRUD 操作

创建 `backend/app/crud/certificate.py`：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Certificate

async def create_certificate(
    session: AsyncSession,
    user_id: int,
    subject_cn: str,
) -> Certificate:
    """Create a new certificate."""
    cert = Certificate(
        user_id=user_id,
        subject_cn=subject_cn,
    )
    session.add(cert)
    await session.commit()
    await session.refresh(cert)
    return cert

async def get_certificate(
    session: AsyncSession,
    cert_id: int,
) -> Certificate | None:
    """Retrieve a certificate by ID."""
    return await session.get(Certificate, cert_id)
```

#### 步骤 3：实现 API 端点

编辑 `backend/app/api/endpoints/ca.py`：

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.crud import certificate as cert_crud
from app.db.session import get_db
from app.models import User
from app.schemas.certificate import CertificateRequest, CertificateResponse
from app.services.audit_service import record_audit_log

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post("", response_model=CertificateResponse, status_code=201)
async def create_certificate(
    payload: CertificateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CertificateResponse:
    """Create a new certificate."""
    cert = await cert_crud.create_certificate(
        session=session,
        user_id=current_user.id,
        subject_cn=payload.subject_cn,
    )
    
    await record_audit_log(
        session=session,
        user_id=current_user.id,
        action="create_certificate",
        resource_id=str(cert.id),
        details={"subject_cn": payload.subject_cn},
    )
    
    return CertificateResponse.model_validate(cert)


@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate(
    cert_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CertificateResponse:
    """Retrieve a certificate by ID."""
    cert = await cert_crud.get_certificate(session=session, cert_id=cert_id)
    
    if cert is None or cert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return CertificateResponse.model_validate(cert)
```

#### 步骤 4：注册路由

确保路由在 `backend/app/api/routes.py` 中注册：

```python
from app.api.endpoints import ca

api_router.include_router(ca.router, prefix="/ca")
```

#### 步骤 5：添加单元测试

创建 `backend/tests/test_certificate_api.py`：

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_certificate(
    client: AsyncClient,
    user_token: str,
) -> None:
    """Test certificate creation."""
    response = await client.post(
        "/api/v1/ca/certificates",
        json={"subject_cn": "example.com", "validity_days": 365},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["subject_cn"] == "example.com"
```

### 数据库迁移 (Alembic)

#### 创建迁移脚本

```bash
cd backend

# 1. 修改模型文件
# 编辑 app/models/certificate.py

# 2. 生成迁移脚本
poetry run alembic revision --autogenerate -m "add_certificate_table"

# 3. 检查生成的脚本
# 查看 migrations/versions/*.py

# 4. 测试升级迁移
poetry run alembic upgrade head

# 5. 测试回滚迁移
poetry run alembic downgrade -1

# 6. 再次升级确认
poetry run alembic upgrade head
```

#### 迁移脚本示例

```python
"""Add certificate table

Revision ID: 0003_add_certificates
Revises: 0002_add_audit_logs
Create Date: 2024-01-15 10:30:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# 修订号需要 ≤ 32 字符
revision = "0003_add_certificates"
down_revision = "0002_add_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certificate",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("subject_cn", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_certificate_user_id", "certificate", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_certificate_user_id", table_name="certificate")
    op.drop_table("certificate")
```

#### 迁移命名规范

**重要**：迁移修订号必须 ≤ 32 字符，因为数据库中存储有限制。

```python
# ✓ 正确 (≤32 字符)
revision = "0001_initial"           # 8 字符
revision = "0002_add_audit_logs"    # 17 字符
revision = "0003_rename_cols"       # 17 字符

# ✗ 错误 (>32 字符)
revision = "0002_rename_audit_logs_metadata_to_meta"  # 45 字符 - 会被截断！
```

### 服务层开发

组织业务逻辑到服务层：

```python
# backend/app/services/certificate_service.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import certificate as cert_crud
from app.core.errors import BadRequestError
from app.models import Certificate

class CertificateService:
    """Certificate business logic service."""

    @staticmethod
    async def issue_certificate(
        session: AsyncSession,
        user_id: int,
        subject_cn: str,
        validity_days: int = 365,
    ) -> Certificate:
        """Issue a new certificate."""
        if validity_days > 3650:
            raise BadRequestError("Validity period cannot exceed 10 years")
        
        cert = await cert_crud.create_certificate(
            session=session,
            user_id=user_id,
            subject_cn=subject_cn,
        )
        return cert

    @staticmethod
    async def revoke_certificate(
        session: AsyncSession,
        cert_id: int,
    ) -> None:
        """Revoke a certificate."""
        cert = await cert_crud.get_certificate(session, cert_id)
        if cert is None:
            raise BadRequestError("Certificate not found")
        
        cert.is_revoked = True
        await session.commit()
```

### 异常处理

使用统一的异常处理：

```python
from app.core.errors import (
    APIException,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
)

# 在端点中
if not user.is_active:
    raise UnauthorizedError("User account is inactive")

if user.role != UserRole.ADMIN:
    raise ForbiddenError("Admin access required")

if cert is None:
    raise NotFoundError("Certificate not found")
```

---

## 前端开发

### 页面开发

#### 创建新页面

创建 `frontend/src/pages/CertificatePage.tsx`：

```typescript
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { fetchCertificates } from "../lib/caApi";
import { useAuth } from "../contexts/AuthContext";
import { CertificateList } from "../components/CertificateList";

interface Certificate {
  id: number;
  subject_cn: string;
  valid_from: string;
  valid_to: string;
}

export const CertificatePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login", { replace: true });
      return;
    }

    const loadCertificates = async () => {
      try {
        setIsLoading(true);
        const data = await fetchCertificates();
        setCertificates(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load certificates");
      } finally {
        setIsLoading(false);
      }
    };

    loadCertificates();
  }, [isAuthenticated, navigate]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Certificates</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <CertificateList certificates={certificates} />
    </div>
  );
};
```

#### 在路由中注册页面

编辑 `frontend/src/routes/index.tsx`：

```typescript
import { createBrowserRouter } from "react-router-dom";
import { CertificatePage } from "../pages/CertificatePage";

export const router = createBrowserRouter([
  {
    path: "/certificates",
    element: <CertificatePage />,
  },
  // ... 其他路由
]);
```

### 组件开发

#### 创建可复用组件

创建 `frontend/src/components/CertificateCard.tsx`：

```typescript
import React from "react";

interface CertificateCardProps {
  id: number;
  subject_cn: string;
  valid_from: string;
  valid_to: string;
  onView?: (id: number) => void;
  onRevoke?: (id: number) => void;
}

export const CertificateCard: React.FC<CertificateCardProps> = ({
  id,
  subject_cn,
  valid_from,
  valid_to,
  onView,
  onRevoke,
}) => {
  return (
    <div style={{ border: "1px solid #ccc", padding: "16px", borderRadius: "8px" }}>
      <h3>{subject_cn}</h3>
      <p>From: {new Date(valid_from).toLocaleDateString()}</p>
      <p>To: {new Date(valid_to).toLocaleDateString()}</p>
      <button onClick={() => onView?.(id)}>View</button>
      <button onClick={() => onRevoke?.(id)} style={{ marginLeft: "8px" }}>
        Revoke
      </button>
    </div>
  );
};
```

### API 集成

#### 创建 API 客户端

创建 `frontend/src/lib/certificateApi.ts`：

```typescript
import { httpClient } from "./httpClient";

export interface Certificate {
  id: number;
  subject_cn: string;
  valid_from: string;
  valid_to: string;
}

export const fetchCertificates = async (): Promise<Certificate[]> => {
  const response = await httpClient.get<Certificate[]>("/ca/certificates");
  return response.data;
};

export const fetchCertificate = async (id: number): Promise<Certificate> => {
  const response = await httpClient.get<Certificate>(`/ca/certificates/${id}`);
  return response.data;
};

export const createCertificate = async (payload: {
  subject_cn: string;
  validity_days?: number;
}): Promise<Certificate> => {
  const response = await httpClient.post<Certificate>("/ca/certificates", payload);
  return response.data;
};

export const revokeCertificate = async (id: number): Promise<void> => {
  await httpClient.post(`/ca/certificates/${id}/revoke`, {});
};
```

#### HTTP 客户端封装

```typescript
// frontend/src/lib/httpClient.ts
import axios, { AxiosInstance, AxiosError } from "axios";
import { getAuthToken, removeAuthToken } from "./auth";
import { API_BASE_URL } from "./env";

const httpClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// 请求拦截器
httpClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器
httpClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeAuthToken();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export { httpClient };
```

---

## 常见开发场景

### 场景 1：添加一个新的 API 端点

**目标**：为用户创建一个"更改密码"端点

**步骤**：

1. **定义 Schema** (`backend/app/schemas/auth.py`)

```python
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
```

2. **创建 CRUD** (`backend/app/crud/user.py`)

```python
async def update_password(
    session: AsyncSession,
    user_id: int,
    hashed_password: str,
) -> None:
    user = await session.get(User, user_id)
    if user:
        user.hashed_password = hashed_password
        await session.commit()
```

3. **添加端点** (`backend/app/api/endpoints/auth.py`)

```python
@router.post("/change-password", tags=["auth"])
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Change user password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")
    
    new_hashed = hash_password(payload.new_password)
    await user_crud.update_password(session, current_user.id, new_hashed)
    
    await record_audit_log(
        session=session,
        user_id=current_user.id,
        action="change_password",
    )
    
    return {"detail": "Password updated successfully"}
```

4. **添加测试** (`backend/tests/test_auth.py`)

```python
async def test_change_password(
    client: AsyncClient,
    user_token: str,
) -> None:
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "AdminPass123!", "new_password": "NewPass123!"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
```

### 场景 2：添加一个新的前端页面

**目标**：创建"设置"页面

**步骤**：

1. **创建页面组件** (`frontend/src/pages/SettingsPage.tsx`)

```typescript
export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  
  return (
    <div>
      <h1>Settings</h1>
      <section>
        <h2>Profile</h2>
        <p>Email: {user?.email}</p>
      </section>
    </div>
  );
};
```

2. **添加路由** (`frontend/src/routes/index.tsx`)

```typescript
import { SettingsPage } from "../pages/SettingsPage";

export const router = createBrowserRouter([
  {
    path: "/settings",
    element: <ProtectedRoute element={<SettingsPage />} />,
  },
]);
```

3. **添加导航链接** (`frontend/src/components/Navigation.tsx`)

```typescript
<Link to="/settings">Settings</Link>
```

### 场景 3：修改数据库字段

**目标**：为 User 模型添加 phone_number 字段

**步骤**：

1. **更新模型** (`backend/app/models/user.py`)

```python
class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # ... 其他字段
```

2. **生成迁移**

```bash
cd backend
poetry run alembic revision --autogenerate -m "add_phone_number_to_user"
poetry run alembic upgrade head
```

3. **更新 Schema** (`backend/app/schemas/user.py`)

```python
class UserUpdate(BaseModel):
    phone_number: str | None = Field(None, max_length=20)
```

---

## 测试指南

### 后端测试

#### 运行测试

```bash
cd backend

# 运行所有测试
poetry run pytest

# 运行特定测试文件
poetry run pytest tests/test_auth.py -v

# 运行特定测试函数
poetry run pytest tests/test_auth.py::test_login -v

# 查看覆盖率
poetry run pytest --cov=app --cov-report=html

# 运行测试并显示打印输出
poetry run pytest -s
```

#### 编写异步测试

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

#### 使用 Mock 和 Fixture

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_pdf_service() -> AsyncMock:
    """Provide a mocked PDF service."""
    return AsyncMock()

@pytest.mark.asyncio
async def test_sign_pdf_with_mock(
    client: AsyncClient,
    user_token: str,
    mock_pdf_service: AsyncMock,
) -> None:
    """Test PDF signing with mocked service."""
    mock_pdf_service.sign_pdf.return_value = b"signed_pdf_content"
    
    with patch("app.services.pdf_service", mock_pdf_service):
        response = await client.post(
            "/api/v1/pdf/sign",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
```

### 前端测试

#### 运行测试

```bash
cd frontend

# 运行所有测试
npm test

# 监视模式
npm run test:watch

# 查看覆盖率
npm run test:coverage
```

#### 编写组件测试

```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("should render login form", () => {
    const handleSubmit = vi.fn();
    render(<LoginForm onSubmit={handleSubmit} />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("should call onSubmit with credentials", async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={handleSubmit} />);
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
    
    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
    });
  });
});
```

---

## 调试技巧

### 后端调试

#### 1. VSCode 调试配置

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### 2. 使用 Swagger API 文档测试

访问 `http://localhost:8000/docs`，使用 Swagger UI 测试端点。

#### 3. 使用 curl 调试

```bash
# 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"AdminPass123!"}' \
  | jq -r '.access_token')

# 获取证书列表
curl -X GET http://localhost:8000/api/v1/ca/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

#### 4. 日志调试

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/debug")
async def debug_endpoint() -> dict[str, str]:
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    return {"status": "logged"}
```

### 前端调试

#### 1. React DevTools

安装 React DevTools 浏览器扩展，检查组件树、Props 和状态。

#### 2. 浏览器 DevTools

- **Network**：监控 API 请求和响应
- **Console**：查看 JavaScript 错误和日志
- **Storage**：查看 localStorage 和 sessionStorage

#### 3. 控制台日志

```typescript
console.log("User data:", user);
console.error("Error:", error);
console.table(certificates);
```

### 数据库调试

#### 使用 psql 查询 PostgreSQL

```bash
# 连接到数据库
psql -U app_user -d app_db -h localhost

# 查询用户表
SELECT * FROM "user";

# 查询审计日志
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 10;

# 查询证书
SELECT * FROM certificate;
```

---

## 代码检查和格式化

### 后端

```bash
cd backend

# Black 格式化
poetry run black app tests

# isort 排序导入
poetry run isort app tests

# mypy 类型检查
poetry run mypy app

# 组合检查
poetry run black --check app tests
poetry run isort --check-only app tests
poetry run mypy app
```

### 前端

```bash
cd frontend

# ESLint 检查
npm run lint

# Prettier 格式化
npm run format

# 检查格式
npm run format:check

# TypeScript 类型检查
npm run typecheck
```

---

## 常见问题

### Q: 如何处理"端口已被占用"错误？

**A**: 使用以下命令找到占用端口的进程并终止：

```bash
# 查找占用 8000 端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或者使用不同的端口启动
poetry run uvicorn app.main:app --port 8001
```

### Q: 数据库迁移失败怎么办？

**A**: 按照以下步骤排查：

```bash
# 1. 检查当前迁移版本
poetry run alembic current

# 2. 查看迁移历史
poetry run alembic history --verbose

# 3. 回滚到上一个版本
poetry run alembic downgrade -1

# 4. 检查迁移脚本是否有语法错误
# 编辑 migrations/versions/*.py

# 5. 重新运行迁移
poetry run alembic upgrade head
```

### Q: 环境变量配置错误？

**A**: 检查以下内容：

```bash
# 1. 确保 .env 文件存在
ls -la .env

# 2. 验证必需的环境变量
grep "SECRET_KEY\|DATABASE_URL\|ENCRYPTED_STORAGE_MASTER_KEY" .env

# 3. 检查 BACKEND_CORS_ORIGINS 格式（必须是 JSON）
# ✓ 正确：BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
# ✗ 错误：BACKEND_CORS_ORIGINS=http://localhost:3000
```

### Q: 如何重置数据库？

**A**: 使用以下命令：

```bash
# 1. 降级所有迁移
poetry run alembic downgrade base

# 2. 升级到最新版本
poetry run alembic upgrade head

# 3. 或者直接删除数据库文件（SQLite）
rm test_app.db
```

### Q: 前端无法连接到后端？

**A**: 检查以下内容：

```typescript
// 1. 检查 API 基础 URL
console.log("API Base URL:", process.env.REACT_APP_API_URL);

// 2. 检查 CORS 配置
// 后端 .env 中的 BACKEND_CORS_ORIGINS 必须包含前端域名

// 3. 检查网络请求
// 打开浏览器 DevTools 的 Network 标签

// 4. 查看浏览器控制台错误信息
console.error(error);
```

---

## 快速命令参考

```bash
# 安装依赖
make install

# 启动开发服务
make dev-backend
make dev-frontend

# 代码检查
make lint

# 代码格式化
make format

# 类型检查
make typecheck

# 运行测试
make test

# 快速重启
make restart
```

---

## 🔗 相关文档

- **[README](README.md)** - 项目介绍和快速开始
- **[架构文档](ARCHITECTURE.md)** - 系统设计和技术架构
- **[API文档](API.md)** - REST API参考
- **[贡献指南](CONTRIBUTING.md)** - 代码贡献流程
- **[安全指南](SECURITY.md)** - 安全开发实践
- **[故障排除](TROUBLESHOOTING.md)** - 开发环境问题排查

## ❓ 需要帮助？

- 查看 **[故障排除文档](TROUBLESHOOTING.md)** 获取开发环境问题解决方案
- 阅读 **[贡献指南](CONTRIBUTING.md)** 了解代码贡献流程
- 在 **[GitHub Issues](https://github.com/QAQ-AWA/ca-pdf/issues)** 提问

---

**ca-pdf 开发指南**

**项目地址**: https://github.com/QAQ-AWA/ca-pdf  
**联系邮箱**: 7780102@qq.com  
**更新日期**: 2025年1月15日
