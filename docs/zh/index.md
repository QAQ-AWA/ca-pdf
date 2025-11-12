# ca-pdf 中文 README

> 📖 **文档导航**：[文档索引](./DOCUMENTATION.md) · [用户指南](./USER_GUIDE.md) · [部署手册](./DEPLOYMENT.md) · [开发指南](./DEVELOPMENT.md) · [API 文档](./API.md)
> 🎯 **适用人群**：所有角色
> ⏱️ **预计阅读时间**：15 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本文是 ca-pdf 项目的文档入口，概述产品价值、快速开始和关键特性。专题内容请结合下方的“文档导航”选择对应文档。

---

ca-pdf 是一个自托管的 PDF 电子签章平台，内置完整的证书颁发机构（CA）系统、时间戳服务支持和企业级审计能力。为组织提供可信的数字签章基础设施，支持本地部署和云端运行。

## 📚 文档导航

README 是 ca-pdf 的入口文档。请根据角色选择合适的阅读顺序，并使用下表快速定位所需信息。

### 推荐阅读路径

- 🆕 **新用户**： [README](./index.md) → [USER_GUIDE](./USER_GUIDE.md) → [TROUBLESHOOTING](./TROUBLESHOOTING.md)
- 👩‍💻 **开发者**： [README](./index.md) → [DEVELOPMENT](./DEVELOPMENT.md) → [ARCHITECTURE](./ARCHITECTURE.md) → [API](./API.md)
- 🛡️ **管理员**： [README](./index.md) → [DEPLOYMENT](./DEPLOYMENT.md) → [SECURITY](./SECURITY.md) → [USER_GUIDE](./USER_GUIDE.md)
- 🤝 **贡献者**： [README](./index.md) → [CONTRIBUTING](./CONTRIBUTING.md) → [DEVELOPMENT](./DEVELOPMENT.md)

### 主要文档速览

| 文档 | 适用人群 | 一句话介绍 |
|-----|----------|------------|
| [DOCUMENTATION.md](./DOCUMENTATION.md) | 全体读者 | 完整的文档地图与主题入口 |
| [DOCS_USAGE_GUIDE.md](./DOCS_USAGE_GUIDE.md) | 首次阅读者 | 如何高效使用和维护文档的简明指南 |
| [README](./index.md) | 所有人 | 产品概览、快速开始、文档导航 |
| [USER_GUIDE.md](./USER_GUIDE.md) | 业务用户 | 证书管理与 PDF 签章的操作流程 |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 开发者 | 本地环境、代码规范与调试技巧 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构师 | 系统设计、技术栈与组件交互 |
| [API.md](./API.md) | 集成开发者 | REST API 端点参考与示例 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 运维 / 管理员 | 部署、环境变量与运维守则 |
| [SECURITY.md](./SECURITY.md) | 安全负责人 | 密钥管理、安全策略与合规建议 |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | 全体读者 | 常见问题与故障处理指南 |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | 贡献者 | 贡献流程、代码标准与审核要求 |
| [CHANGELOG.md](./CHANGELOG.md) | 维护者 | 版本变更记录与发布日期 |

> 📌 技术栈版本的详细列表仅保留在 [ARCHITECTURE.md](./ARCHITECTURE.md) 中；环境变量配置集中在 [DEPLOYMENT.md](./DEPLOYMENT.md)；快速开始命令以本 README 为准，其余文档直接引用。

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

## 🛠️ 技术栈概览

完整的技术栈版本矩阵仅保留在 [ARCHITECTURE.md](./ARCHITECTURE.md) 的“技术栈”章节。本节简要列出核心组件，帮助快速定位对应文档。

- **后端**：FastAPI、SQLAlchemy、Alembic、pyHanko
- **前端**：React、TypeScript、Vite、React Router
- **数据库与存储**：PostgreSQL、SQLite（测试）、Fernet 加密存储
- **基础设施**：Docker、Traefik、Nginx、Prometheus/Grafana
- **安全组件**：JWT、bcrypt、TLS、审计日志

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

生产环境部署请参考 **[DEPLOYMENT.md](./DEPLOYMENT.md)** 文档，包含以下内容：

- 🔒 **SSL/TLS配置**：Let's Encrypt证书自动续期
- 🔑 **密钥管理**：主密钥离线备份和恢复
- 📊 **高可用**：负载均衡和故障转移
- 📈 **监控告警**：Prometheus + Grafana集成
- 🔄 **备份恢复**：数据库和关键数据的备份策略

### 环境变量配置

完整的环境变量说明、默认值与安全注意事项请参阅 [DEPLOYMENT.md](./DEPLOYMENT.md) 中的“环境变量清单”章节。本 README 只保留快速启动所需的核心指引。

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

- 🐛 **Bug 报告**：[GitHub Issues](https://github.com/QAQ-AWA/ca-pdf/issues)
- 💡 **功能建议**：[GitHub Discussions](https://github.com/QAQ-AWA/ca-pdf/discussions)
- 📧 **联系我们**：[7780102@qq.com](mailto:7780102@qq.com)

## 📘 文档维护

我们承诺文档与代码保持同频更新，并在变更后的 **7 天内** 完成所有必要的文档同步，用户反馈将在 **3 个工作日内** 得到响应。

### 长期维护承诺
- 任何影响用户、部署、安全或运维的改动，必须在合并前同步更新对应文档并在 PR 中注明。
- 新功能合并后 1 周内完成 README / USER_GUIDE / API 文档等必要更新。
- 每次发布都会生成对应的文档版本记录，并保留历史版本以供追溯。

### 定期维护节奏
- **每周**：检查带有 `documentation` 标签的 GitHub Issues 与 PR 评论，收集并处理文档反馈。
- **每个功能合并时**：确认关联文档（API、用户指南、示例代码等）已更新，并在 [./MAINTENANCE_LOG.md](./MAINTENANCE_LOG.md) 中登记。
- **每个版本发布前**：执行发布前文档检查清单，更新 [CHANGELOG.md](./CHANGELOG.md) 与版本说明。
- **每季度**：开展一次全量文档审查，重点关注准确性、时效性和链接有效性。

### 发布前文档检查清单
- [ ] 所有新功能都在 [API.md](./API.md) 中有文档
- [ ] 所有 API 变更都在 [CHANGELOG.md](./CHANGELOG.md) 中记录
- [ ] 用户指南已更新新功能
- [ ] 架构设计文档与代码一致
- [ ] [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 中添加新的常见问题
- [ ] 全部文档链接已通过 `scripts/validate-docs.sh` 检查
- [ ] 文档中的代码示例已经验证可以运行

### 文档所有权
| 文档 | 主要负责人 | 备援团队 |
|------|------------|----------|
| README.md | 项目管理者 | 核心维护者 |
| API.md | 后端技术负责人 | 核心开发团队 |
| DEPLOYMENT.md | 运维负责人 | 运维与安全团队 |
| DEVELOPMENT.md | 开发团队 | 核心维护者 |
| USER_GUIDE.md | 产品 / 文档团队 | 技术支持团队 |
| ARCHITECTURE.md | 技术架构师 | 核心开发团队 |
| TROUBLESHOOTING.md | 技术支持团队 | 运维团队 |
| CONTRIBUTING.md | 项目负责人 | 核心维护者 |
| SECURITY.md | 安全负责人 | 运维与安全团队 |
| CHANGELOG.md | 项目管理者 | 发布经理 |

### 自动化守护
- PR 模板新增“文档检查清单”，在合并前逐项确认。
- [scripts/validate-docs.sh](./scripts/validate-docs.sh) 会校验内部链接、CHANGELOG 格式、API 文档一致性以及 Markdown 中的 Python 示例语法。
- `.github/workflows/documentation-guardrails.yml` 会在 PR 中强制检查：代码改动是否伴随文档更新、API 变更是否同步到 API.md、以及 CHANGELOG 是否更新。

### 文档版本管理与记录
- 发布版本时在 [CHANGELOG.md](./CHANGELOG.md) 中同步记录文档版本信息，并在必要时将旧版本移入 `docs/versions/`（待上线）。
- 所有文档维护活动必须登记在 [./MAINTENANCE_LOG.md](./MAINTENANCE_LOG.md)，便于追踪责任人和更新时间。
- 废弃或破坏性变更需在相关文档中标注弃用说明及迁移指南。

### 反馈渠道与质量指标
- 反馈渠道：`documentation` 标签的 GitHub Issues、PR 评论以及邮箱 [7780102@qq.com](mailto:7780102@qq.com)。
- 质量指标：记录文档更新频率、用户反馈数量、文档准确率（错误报告量）与覆盖率（受影响功能是否有文档）。
- 文档贡献指南与模板请参阅 [CONTRIBUTING.md](./CONTRIBUTING.md) 的“文档贡献”章节。

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

🔗 **相关文档**
- [文档索引](./DOCUMENTATION.md)
- [用户指南](./USER_GUIDE.md)
- [开发指南](./DEVELOPMENT.md)
- [部署手册](./DEPLOYMENT.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

**最后更新**：2025-01-15

**ca-pdf** - 🔐 自托管的PDF电子签章平台

Made with ❤️ for secure document signing
