# ca-pdf 中文 README

> **简体中文**

ca-pdf 是一个自托管的 PDF 电子签章平台，内置完整的证书颁发机构（CA）系统、时间戳服务支持和企业级审计能力。为组织提供可信的数字签章基础设施，支持本地部署和云端运行。

## 📌 项目介绍

### 核心价值主张

ca-pdf 让您能够快速搭建一套独立的 PDF 数字签章系统，完全掌控证书体系和签署流程。无需依赖第三方服务商，数据和密钥材料完全托管在自己的基础设施中，适合需要高度定制化和隐私保护的企业场景。

### 核心功能特性

| 功能 | 说明 |
|-----|------|
| **根CA自建** | 自签根证书、完全掌控密钥、支持RSA-4096/EC-P256算法 |
| **证书生命周期** | 签发/导入/吊销/续期、PKCS#12格式、自动CRL生成 |
| **PDF电子签章** | 单份/批量签署、可见/不可见签章、企业印章应用 |
| **时间戳和LTV** | RFC3161 TSA集成、长效验证材料嵌入、Acrobat兼容 |
| **签章验真** | 多签名解析、信任链验证、时间戳有效性检查 |
| **审计安全** | 完整操作日志、IP和User-Agent追踪、不可篡改记录 |
| **用户权限管理** | JWT + Refresh Token认证、RBAC角色控制、多用户支持 |
| **企业印章管理** | PNG/SVG印章上传、加密存储、版本管理、复用应用 |

### 适用场景

- 🏢 **企业合同签署**：内部流程文件、供应商协议、员工文档等
- 📋 **行政审批**：报批表单、审批流程、认可文件等
- 🏥 **医疗卫生**：处方单、诊断报告、医嘱等
- ⚖️ **法律合规**：合同存档、证据保存、法律合规等
- 📦 **物流单据**：单据签署、收货确认、交接单等

---

## 🚀 快速开始

### 环境要求

- **Docker Engine** 23+ 与 **Docker Compose** V2
- **Python** 3.11+ （用于本地开发）
- **Node.js** 16+ （用于前端开发）
- **PostgreSQL** 12+ （生产推荐，本地开发可用SQLite）
- 一个可解析到宿主机的**域名**（开发用 `*.localtest.me` 或 `localhost`）

### 本地开发安装

#### 1. 克隆仓库并进入项目目录

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
```

#### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env
cp .env.docker.example .env.docker

# 编辑 .env 填写必要变量
# 生成安全密钥
openssl rand -base64 32  # 用于 SECRET_KEY
openssl rand -base64 32  # 用于 ENCRYPTED_STORAGE_MASTER_KEY
```

关键环境变量说明：

| 变量 | 说明 | 示例 |
|-----|------|------|
| `SECRET_KEY` | JWT签发密钥 | `openssl rand -base64 32` 生成 |
| `ENCRYPTED_STORAGE_MASTER_KEY` | 加密私钥的主密钥（必填，需妥善保管） | 32字节Fernet密钥 |
| `DATABASE_URL` | 异步SQLAlchemy连接串 | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | 首次启动自动创建的管理员 | `admin@example.com` / `SecurePass123` |
| `BACKEND_DOMAIN` | API服务域名（Traefik暴露） | `api.localtest.me` |
| `FRONTEND_DOMAIN` | 前端域名（Traefik暴露） | `app.localtest.me` |

#### 3. 本地运行（Docker Compose）

```bash
# 一键启动全栈（包含PostgreSQL、后端、前端、Traefik）
./deploy.sh up

# 查看服务状态
./deploy.sh ps

# 查看日志
./deploy.sh logs -f backend
```

或者本地开发模式（需要手动启动PostgreSQL）：

```bash
# 安装依赖
make install

# 启动后端API（热更新）
make dev-backend

# 在另一个终端启动前端（Vite dev server）
make dev-frontend
```

#### 4. 首次访问和登录

- **前端应用**：https://app.localtest.me （或 http://localhost:3000）
- **API文档**：https://api.localtest.me/docs （或 http://localhost:8000/docs）
- **默认账号**：.env 中的 `ADMIN_EMAIL` / `ADMIN_PASSWORD`

首次登录后，前往"证书管理"生成根CA，然后可以开始签章流程。

---

## 📊 功能概览

### 认证与授权

- **JWT认证**：Access Token（15分钟）+ Refresh Token（3天）
- **RBAC权限**：Admin（管理员）/ User（普通用户）两级角色
- **Token轮换**：刷新令牌时自动轮换，提升安全性
- **速率限制**：登录端点限制（默认5次/60秒防暴力破解）

### 证书管理

| 操作 | 说明 |
|-----|------|
| 生成根CA | 自签根证书，支持RSA-4096/EC-P256，有效期可自定义 |
| 签发证书 | 基于根CA签发用户证书，返回PKCS#12捆绑包 |
| 导入证书 | 导入外部PKCS#12格式证书到系统 |
| 查看列表 | 列出当前用户/全部证书（管理员），显示状态和有效期 |
| 吊销证书 | 立即吊销证书，自动生成CRL清单 |
| 下载CRL | 获取最新证书吊销列表，供客户端验证使用 |

### PDF电子签章

| 类型 | 说明 |
|-----|------|
| 单个签章 | 上传PDF，选择位置和签章样式，一键签署 |
| 批量签章 | 同时签署多个PDF（默认最多10个），相同参数统一应用 |
| 可见签章 | 在PDF指定位置显示签名框（包含时间戳和证书信息） |
| 不可见签章 | 嵌入数字签名但不改变PDF视觉效果 |
| 企业印章 | 上传公司logo/印章，应用到签章框上 |
| 签章元数据 | 支持记录签章原因、地点、联系方式等信息 |
| TSA时间戳 | 集成RFC3161兼容的时间戳服务，提供法律依据 |
| LTV嵌入 | 在签名中嵌入验证材料（OCSP/CRL），实现长期有效 |

### 签章验真

- **多签名检验**：一次上传可验证文件中的所有数字签名
- **有效性判断**：Valid（有效）/ Invalid（无效）/ Unsigned（无签名）
- **信任链验证**：Trusted（受信任）/ Untrusted（不受信任）
- **时间戳检查**：显示签名时间、时间戳提供方、有效性
- **修改检测**：DocMDP级别判断文件签署后是否被修改

### 审计日志

- **完整操作记录**：证书生成、签章、吊销、登录、访问等所有关键操作
- **元数据记录**：执行人、IP地址、User-Agent、操作时间、资源标识
- **日志查询**：支持按用户、事件类型、日期范围等多维度筛选
- **导出功能**：支持导出为CSV/JSON格式用于外部审计

### 用户与权限

- **多用户支持**：组织内多个用户可同时使用系统
- **权限控制**：基于角色的访问控制（RBAC）
- **用户管理**：管理员可创建/启用/禁用用户账户
- **密码策略**：支持密码复杂度检查和过期管理

### 企业印章

- **上传管理**：支持PNG（推荐透明背景）和SVG矢量格式
- **大小限制**：默认不超过1 MiB，可通过环境变量调整
- **加密存储**：印章文件使用主密钥加密，安全存储
- **版本管理**：支持更新印章，旧版本可被查询但不再使用
- **批量应用**：在批量签章时一次应用同一印章到多份文档

---

## 🛠️ 技术栈

### 后端

| 组件 | 版本 | 用途 |
|-----|------|------|
| **FastAPI** | ^0.110.0 | 高性能异步Web框架 |
| **SQLAlchemy** | ^2.0.29 | ORM + 数据库抽象层 |
| **Alembic** | ^1.13.2 | 数据库迁移管理 |
| **asyncpg** | ^0.29.0 | PostgreSQL异步驱动 |
| **aiosqlite** | ^0.20.0 | SQLite异步驱动（测试用） |
| **pyHanko** | ^0.25.0 | PDF签章库（支持签名和验证） |
| **cryptography** | ^42.0.8 | 密码学库（加密/解密） |
| **python-jose** | ^3.3.0 | JWT令牌管理 |
| **Passlib + bcrypt** | - | 密码哈希和验证 |

### 前端

| 组件 | 版本 | 用途 |
|-----|------|------|
| **React** | ^18.3.1 | UI框架 |
| **TypeScript** | ^5.4.0 | 类型安全的JavaScript |
| **Vite** | ^5.2.0 | 快速构建工具 |
| **React Router** | ^6.26.2 | 客户端路由 |
| **Axios** | ^1.7.7 | HTTP客户端 |
| **pdfjs-dist** | ^5.4.296 | PDF渲染和查看 |

### 部署

| 组件 | 版本 | 用途 |
|-----|------|------|
| **Docker** | 23+ | 容器化运行环境 |
| **Docker Compose** | V2 | 服务编排 |
| **Traefik** | 3.x | 反向代理和SSL/TLS |
| **PostgreSQL** | 12+ | 生产数据库 |
| **Nginx** | latest | 前端服务器 |

---

## 📁 项目结构

```
ca-pdf/
├── backend/
│   ├── app/
│   │   ├── api/                    # REST API路由（v1版本）
│   │   │   ├── endpoints/          # 端点实现（证书、签章、验签等）
│   │   │   └── dependencies.py     # 依赖注入（认证、权限等）
│   │   ├── models/                 # SQLAlchemy ORM模型
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── certificate.py      # 证书模型
│   │   │   ├── pdf_signature.py    # 签章记录
│   │   │   └── audit_log.py        # 审计日志
│   │   ├── schemas/                # Pydantic请求/响应schema
│   │   ├── crud/                   # 数据库增删改查操作
│   │   ├── services/               # 业务逻辑
│   │   │   ├── ca_service.py       # CA证书管理
│   │   │   ├── pdf_service.py      # PDF签章和验证
│   │   │   ├── audit_service.py    # 审计日志
│   │   │   └── seal_service.py     # 企业印章管理
│   │   ├── core/                   # 核心配置
│   │   │   ├── config.py           # 环境变量配置
│   │   │   ├── security.py         # 认证和密码处理
│   │   │   └── encryption.py       # 密钥加密存储
│   │   ├── db/                     # 数据库连接
│   │   └── main.py                 # FastAPI应用入口
│   ├── migrations/                 # Alembic数据库迁移
│   ├── tests/                      # 后端单元和集成测试
│   ├── Dockerfile                  # 后端容器镜像
│   └── pyproject.toml              # Poetry依赖管理
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # 页面组件
│   │   │   ├── LoginPage.tsx       # 登录页面
│   │   │   ├── DashboardPage.tsx   # 仪表盘
│   │   │   ├── CertificatePage.tsx # 证书管理
│   │   │   ├── SignaturePage.tsx   # 签章工作台
│   │   │   ├── VerifyPage.tsx      # 验签中心
│   │   │   └── AuditPage.tsx       # 审计日志（管理员）
│   │   ├── components/             # 可复用UI组件
│   │   │   ├── Navigation.tsx
│   │   │   ├── CertificateList.tsx
│   │   │   ├── PDFViewer.tsx
│   │   │   └── SealUploadManager.tsx
│   │   ├── lib/                    # 工具函数和API客户端
│   │   │   ├── api.ts             # API调用封装
│   │   │   ├── auth.ts            # 认证逻辑
│   │   │   └── types.ts           # TypeScript类型定义
│   │   └── main.tsx                # React应用入口
│   ├── Dockerfile                  # 前端容器镜像
│   ├── nginx.conf                  # Nginx配置（生产）
│   ├── package.json                # npm依赖管理
│   └── tsconfig.json               # TypeScript配置
│
├── config/                         # 共享配置
│   ├── .eslintrc.json              # ESLint规则
│   └── prettier.config.js          # Prettier格式化配置
│
├── scripts/                        # 开发辅助脚本
│   ├── setup-db.sh                 # 数据库初始化
│   └── generate-keys.sh            # 生成加密密钥
│
├── docker-compose.yml              # 完整栈编排配置
├── Makefile                        # 开发命令快捷方式
├── deploy.sh                       # 一键部署脚本
├── .env.example                    # 环境变量示例
├── .env.docker.example             # Docker环境变量示例
└── README.md                       # 本文件

```

---

## 🐳 部署选项

### 本地开发（Docker Compose）

最快速的启动方式，一个命令即可启动完整的开发栈：

```bash
# 一键启动
./deploy.sh up

# 初次启动会自动：
# 1. 构建前后端镜像
# 2. 启动 Traefik（反向代理）
# 3. 启动 PostgreSQL（数据库）
# 4. 启动后端 API（FastAPI）
# 5. 启动前端应用（React）
# 6. 运行数据库迁移（Alembic）
# 7. 创建默认管理员账号

# 停止服务
./deploy.sh down

# 重新启动
./deploy.sh restart

# 完全清理（包括数据卷）
./deploy.sh destroy
```

### 生产部署概览

生产环境部署请参考 **[DEPLOYMENT.md](./docs/DEPLOYMENT.md)** 文档，包含以下内容：

- 🔒 **SSL/TLS配置**：Let's Encrypt证书自动续期
- 🔑 **密钥管理**：主密钥离线备份和恢复
- 📊 **高可用**：负载均衡和故障转移
- 📈 **监控告警**：Prometheus + Grafana集成
- 🔄 **备份恢复**：数据库和关键数据的备份策略

### 环境变量配置

#### 关键生产变量

```bash
# 安全相关
SECRET_KEY=<使用 openssl rand -base64 32 生成>
ENCRYPTED_STORAGE_MASTER_KEY=<Fernet 32字节密钥，需妥善保管>

# 数据库
DATABASE_URL=postgresql+asyncpg://app_user:password@db:5432/app_db
POSTGRES_DB=app_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=<强密码>

# 应用配置
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=<强密码>
APP_NAME=ca-pdf

# 域名和反向代理
BACKEND_DOMAIN=api.company.com
FRONTEND_DOMAIN=sign.company.com
TRAEFIK_ACME_EMAIL=admin@company.com

# TSA时间戳（可选）
TSA_URL=https://freetsa.org/tsr
TSA_USERNAME=optional
TSA_PASSWORD=optional

# 文件限制
PDF_MAX_BYTES=52428800          # 50MB
PDF_BATCH_MAX_COUNT=10
SEAL_IMAGE_MAX_BYTES=1048576    # 1MB
```

---

## 📚 文档导航

完整文档组织如下：

| 文档 | 内容 | 适用人群 |
|-----|------|--------|
| **[API.md](./docs/API.md)** | REST API详细文档、请求/响应示例、错误码 | 开发者 |
| **[DEPLOYMENT.md](./docs/DEPLOYMENT.md)** | 生产部署、监控、备份恢复、性能优化 | 运维 |
| **[USER_GUIDE.md](./docs/USER_GUIDE.md)** | 功能使用指南、常见操作、最佳实践 | 最终用户 |
| **[DEVELOPMENT.md](./docs/DEVELOPMENT.md)** | 本地开发设置、编码规范、测试覆盖 | 贡献者 |
| **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** | 系统设计、数据流、安全架构 | 架构师 |
| **[TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** | 常见问题、排查步骤、解决方案 | 所有人 |
| **[SECURITY.md](./docs/SECURITY.md)** | 安全建议、密钥管理、合规指导 | 安全团队 |

快速链接：
- 🏃 [快速开始](#快速开始) - 5分钟启动项目
- 🎨 [功能概览](#功能概览) - 功能特性总览
- 🔧 [技术栈](#技术栈) - 使用的技术组件

---

## 📄 许可证和联系

### 开源许可

ca-pdf 采用 **MIT License** 开源协议。详见 [LICENSE](./LICENSE) 文件。

您可以自由地在商业和非商业项目中使用本软件，但请保留原始许可声明。

### 贡献方式

我们欢迎社区贡献！贡献步骤：

1. **Fork** 本仓库
2. 创建**特性分支**（`git checkout -b feature/amazing-feature`）
3. **提交更改**（`git commit -m 'Add amazing feature'`）
4. **推送分支**（`git push origin feature/amazing-feature`）
5. 创建 **Pull Request**

请确保：
- 代码通过所有测试（`make test`）
- 代码质量检查通过（`make lint`）
- 提交信息清晰明了
- 涉及新功能时请添加文档和测试

### 问题反馈

遇到问题或有建议？

- 🐛 **Bug报告**：[GitHub Issues](https://github.com/yourusername/ca-pdf/issues)
- 💡 **功能建议**：[GitHub Discussions](https://github.com/yourusername/ca-pdf/discussions)
- 📧 **联系我们**：dev@ca-pdf.io

---

## 🎯 快速命令参考

### 开发命令

```bash
# 完整安装
make install

# 启动开发服务
make dev-backend      # 启动后端（8000端口）
make dev-frontend     # 启动前端（3000端口）

# 代码检查
make lint             # 代码规范检查
make format           # 代码格式化
make typecheck        # 类型检查（mypy + tsc）

# 测试
make test             # 后端pytest + 前端vitest
make test-backend     # 仅后端测试
make test-frontend    # 仅前端测试
```

### 部署命令

```bash
# 启动全栈
./deploy.sh up

# 查看状态
./deploy.sh ps

# 查看日志
./deploy.sh logs backend
./deploy.sh logs frontend

# 重启服务
./deploy.sh restart

# 停止服务
./deploy.sh down

# 清理资源
./deploy.sh destroy
```

---

**ca-pdf** - 🔐 自托管的PDF电子签章平台

Made with ❤️ for secure document signing
