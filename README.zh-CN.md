# ca-pdf 中文使用指南

ca-pdf 是一套自托管的 PDF 电子签章平台，内置证书管理、时间戳和合规审计能力，帮助组织快速搭建可信的数字签章基础设施。仓库同时提供 FastAPI 后端、Vite + React 前端以及经过编排的容器化部署方案。

---

## 1. 项目简介

功能概览：

- **根 CA 自建**：支持生成/导出自签根证书，完整掌控密钥材料。
- **证书生命周期管理**：签发、导入（PKCS#12）、吊销和下载用户证书，自动生成 CRL。
- **PDF 签章**：单文档或批量签署，可见/不可见签章、印章叠加、签章理由/地点/联系方式、可选 TSA 时间戳与 LTV 嵌入。
- **TSA 与 LTV**：可连接外部 RFC3161 TSA，完成长效验证材料封装。
- **签章验真**：提供前端验签工作台与 API，输出每个签名的有效性、信任链、时间戳状态。
- **审计与安全**：所有关键操作（签章、吊销、登录等）写入审计日志，支持 IP 与 User-Agent 记录。
- **用户与权限**：JWT + Refresh Token 认证机制，按角色控制访问（普通用户 / 管理员）。

---

## 2. 快速开始

### 2.1 依赖要求

- Docker Engine 23+ 与 Docker Compose V2
- 一个可解析到宿主机/服务器的域名（默认使用 `*.localtest.me`）
- Bash shell（用于执行 `deploy.sh`）

### 2.2 准备环境变量

复制示例文件，并根据环境修改：

```bash
cp .env.example .env
cp .env.docker.example .env.docker
```

关键变量说明：

| 变量 | 说明 |
| --- | --- |
| `SECRET_KEY` | JWT 签发密钥，使用 `openssl rand -base64 32` 生成。 |
| `ENCRYPTED_STORAGE_MASTER_KEY` 或 `ENCRYPTED_STORAGE_MASTER_KEY_PATH` | 加密私钥与印章的主密钥，务必保密并做好备份。支持 Fernet 或 AES-GCM。 |
| `DATABASE_URL` | Async SQLAlchemy 连接串，例如 `postgresql+asyncpg://app_user:app_password@db:5432/app_db`。 |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Compose 内置 PostgreSQL 服务的数据库名称、用户名、密码。 |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | 首次启动时自动创建的管理员账号。 |
| `BACKEND_DOMAIN` / `FRONTEND_DOMAIN` | 通过 Traefik 暴露的域名，用于 API 与前端站点。 |
| `TRAEFIK_ACME_EMAIL` | 申请 Let’s Encrypt 证书的 ACME 邮箱，生产环境请填写真实邮箱。 |
| `TRAEFIK_HTTP_PORT` / `TRAEFIK_HTTPS_PORT` | （可选）变更默认的 80 / 443 映射，处理端口冲突。 |
| `TSA_URL` / `TSA_USERNAME` / `TSA_PASSWORD` | （可选）RFC3161 时间戳服务配置。 |
| `PDF_MAX_BYTES` / `PDF_BATCH_MAX_COUNT` | PDF 文件大小与批量签章的限制。 |
| `SEAL_IMAGE_ALLOWED_CONTENT_TYPES` / `SEAL_IMAGE_MAX_BYTES` | 企业印章允许上传的图片类型与大小限制。 |

> **安全提示**：`ENCRYPTED_STORAGE_MASTER_KEY` 是解密私钥/印章的唯一凭据，请离线备份并限制访问权限。

### 2.3 一键部署（支持 amd64 / arm64）

仓库提供 `deploy.sh` 脚本自动完成构建与启动，脚本根据宿主机架构（x86_64/arm64）设置 `DOCKER_DEFAULT_PLATFORM`，因此同时支持 Intel/AMD 与 ARM 服务器。

```bash
./deploy.sh up
```

- 首次执行会自动构建前后端镜像并启动 Traefik、PostgreSQL、后端、前端。
- 有需要时可通过 `TARGET_PLATFORMS=linux/amd64,linux/arm64 ./deploy.sh up` 强制构建多架构镜像。
- `TRAEFIK_ACME_EMAIL` 设置为真实邮箱后，Traefik 会向 Let’s Encrypt 申请正式证书；如需长期测试，可保持默认的 Staging CA。
- 若您倾向使用 Caddy，可在 `docker-compose.yml` 中替换反向代理（默认提供 Traefik 配置，Caddy 仅作替代参考）。

常用命令：

```bash
./deploy.sh ps          # 查看容器状态
./deploy.sh logs        # 跟踪全部服务日志
./deploy.sh logs backend
./deploy.sh restart     # 重启前后端容器
./deploy.sh down        # 停止服务（保留数据卷）
./deploy.sh destroy     # 停止并清空 PostgreSQL / Traefik 数据卷
```

### 2.4 首次登录与管理员初始化

1. 浏览器访问 `https://<FRONTEND_DOMAIN>`，会自动跳转到登录页；API Swagger 文档位于 `https://<BACKEND_DOMAIN>/docs`。
2. 使用 `.env` 中的 `ADMIN_EMAIL` / `ADMIN_PASSWORD` 登录，系统会自动为该账号赋予 `admin` 角色。
3. 首次进入控制台后，请前往“证书管理”生成根 CA 并签发业务证书。

---

## 3. 控制台与 API 使用指南

前端导航包含「概览」「签章工作台」「验签中心」「审计日志」（管理员）等模块，以下对核心流程进行说明。

### 3.1 证书生命周期管理

1. **生成根 CA**（管理员权限）：
   - 控制台：进入“证书管理”页，点击“生成根 CA”，选择算法（RSA-4096 / EC-P256）、填写主体信息，提交后即可生成。
   - API：
     ```bash
     curl -X POST "https://<BACKEND_DOMAIN>/api/v1/ca/root" \
       -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{
         "common_name": "Example Root CA",
         "organization": "Example Corp",
         "algorithm": "rsa-4096",
         "validity_days": 3650
       }'
     ```
   - 生成成功后可在同页下载 PEM 根证书（`GET /api/v1/ca/root/certificate`）。请妥善存储生成的证书与私钥（私钥加密存储于数据库，受 master key 保护）。

2. **签发用户证书**：
   - 控制台：“签发证书”表单填写通用名、组织、有效期与（可选）PKCS#12 密码。
   - API：
     ```bash
     curl -X POST "https://<BACKEND_DOMAIN>/api/v1/ca/certificates/issue" \
       -H "Authorization: Bearer <ACCESS_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{
         "common_name": "alice@example.com",
         "organization": "Example Corp",
         "algorithm": "rsa-2048",
         "validity_days": 365,
         "p12_passphrase": "S3cret!"
       }'
     ```
   - 响应中的 `p12_bundle` 字段为一次性返回的 base64 编码 PKCS#12，请立即保存至安全位置（例如 `base64 -d > alice.p12`）。

3. **导入外部证书**：
   - 将 PKCS#12 文件 base64 编码后提交。
     ```bash
     base64 -w0 external.p12 > external.b64

     curl -X POST "https://<BACKEND_DOMAIN>/api/v1/ca/certificates/import" \
       -H "Authorization: Bearer <ACCESS_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{
         "p12_bundle": "$(cat external.b64)",
         "passphrase": "optional-pass"
       }'
     ```

4. **吊销证书与 CRL**：
   - 管理员可通过 UI 或 API 吊销：`POST /api/v1/ca/certificates/{certificate_id}/revoke`。
   - 生成 CRL：`POST /api/v1/ca/crl`，响应包含最新 `crl_pem`，同时会存档至 `GET /api/v1/ca/crl` 列表中供下载。

5. **查看证书列表**：`GET /api/v1/ca/certificates` 返回当前用户持有的证书状态、序列号和有效期。

### 3.2 企业印章管理

- 印章上传入口位于“签章工作台”右侧边栏（`SealUploadManager`）。支持 PNG / SVG，默认大小不得超过 1 MiB。
- **推荐规范**：
  - 背景透明的 PNG，分辨率 300×300 px 以上；或矢量 SVG 以保证缩放质量。
  - 印章边缘留出 10% 以上空白，避免缩放裁切。
  - 若图像包含文字，请使用深色以确保在浅色 PDF 背景上清晰可见。
- 后端会将源文件进行加密存储，删除印章时建议同步审查相关签章模板。

### 3.3 PDF 签章

1. **单文档签章**：
   - 上传 PDF 后可在预览画布中添加一个或多个签章框，设置可见性（Visible/Invisible）、印章、理由、地点与联系方式。
   - 勾选 “使用 TSA” 时，系统会调用在 `.env` 中配置的 `TSA_URL`；若未配置则忽略。
   - “嵌入 LTV” 会在签章中写入额外验证材料，建议搭配可信 TSA 使用。
   - 提交后返回新的 PDF 文件，文件名格式 `signed_<UUID>.pdf`。

2. **批量签章**：
   - 批量上传多个 PDF，统一使用同一套签章参数。默认最多 10 个，可通过 `PDF_BATCH_MAX_COUNT` 调整。
   - 成功与失败的文档会在结果列表中分别标记，可在审计日志中查看详细原因。

3. **API 调用示例**：
   ```bash
   curl -X POST "https://<BACKEND_DOMAIN>/api/v1/pdf/sign" \
     -H "Authorization: Bearer <ACCESS_TOKEN>" \
     -F "pdf_file=@/path/to/document.pdf" \
     -F "certificate_id=<certificate-uuid>" \
     -F "seal_id=<seal-uuid>" \
     -F "visibility=visible" \
     -F "page=1" \
     -F "x=120" -F "y=180" -F "width=180" -F "height=120" \
     -F "reason=Approved" -F "location=Shenzhen" \
     -F "contact_info=ops@example.com" \
     -F "use_tsa=true" -F "embed_ltv=true" \
     -o signed.pdf
   ```

### 3.4 LTV 策略

- LTV 依赖在签名时嵌入 OCSP/CRL 与时间戳信息。开启 `embed_ltv` 选项后，系统会在签章过程中下载所需验证材料。
- 建议同时提供可访问的 TSA（`TSA_URL`），以确保时间戳可信并提升 Acrobat 验证结果可信度。

### 3.5 验签中心

- 上传任意已签名 PDF，系统会解析所有签章并展示：
  - 有效性（Valid / Invalid）
  - 信任状态（Trusted / Untrusted）
  - 修改级别（DocMDP）
  - 签名者序列号、Common Name、时间戳详情
- API：
  ```bash
  curl -X POST "https://<BACKEND_DOMAIN>/api/v1/pdf/verify" \
    -H "Authorization: Bearer <ACCESS_TOKEN>" \
    -F "pdf_file=@signed.pdf"
  ```

### 3.6 审计日志

- 管理员可在“审计日志”页面按执行人、事件类型、日期区间筛选日志，并查看详细的元数据（例如签章所用证书、文件大小、IP 地址等）。
- 对应 API：`GET /api/v1/audit/logs?limit=100&event_type=pdf.signature.applied`。

---

## 4. 信任配置

为确保终端正确信任签章结果，请将根 CA 证书导入到客户端系统：

### 4.1 操作系统证书存储

- **Windows**：
  1. 运行 `certmgr.msc`
  2. 选择「受信任的根证书颁发机构 → 证书」，右键导入
  3. 选择根证书 PEM/CRT 文件，按向导完成

- **macOS**：
  1. 打开“钥匙串访问”
  2. 选择「系统 → 证书」
  3. 导入根证书后，在详情中设置信任为「始终信任」

- **Linux（Debian/Ubuntu）**：
  ```bash
  sudo cp root-ca.pem /usr/local/share/ca-certificates/ca-pdf-root.crt
  sudo update-ca-certificates
  ```

### 4.2 Adobe Acrobat Reader

1. Preferences → Trust Manager → Trusted Certificates → Import
2. 选择根 CA 证书，勾选“使用此证书来标识签署者”和“用于文档签名”
3. 保存后重新打开签名文档，状态应显示绿色勾选

---

## 5. 运维指南

### 5.1 数据备份与恢复

- **数据库**：
  ```bash
  ./deploy.sh up        # 确保服务运行
  docker compose exec db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql
  ```
  恢复时使用 `psql` 将备份导入。

- **密钥材料**：
  - `.env` / `.env.docker`
  - `ENCRYPTED_STORAGE_MASTER_KEY`（或对应文件）
  - Traefik 的 `traefik_letsencrypt` 数据卷（Let’s Encrypt 证书）

- 建议定期打包以下 Docker 卷：`postgres_data`、`traefik_letsencrypt`。

### 5.2 日志与审计

- 运行日志：`./deploy.sh logs backend`、`./deploy.sh logs frontend` 等。
- Traefik 自带访问日志，可在 `docker-compose.yml` 中开启更详细的记录。
- 审计日志通过 UI 或 API 查询，记录不可直接编辑。若需归档，可定期导出数据库中的 `audit_logs` 表。

### 5.3 Prometheus 监控

- FastAPI 提供 `/health` 端点用于存活检查。
- 如需暴露 Prometheus 指标，可在 `docker-compose.yml` 的 Traefik 服务添加：
  ```yaml
  command:
    - --metrics.prometheus=true
    - --metrics.prometheus.buckets=0.1,0.3,1.2,5
  ```
  并在 Compose 中开放对应端口（例如 8082）。同时可以使用 [`prometheus-fastapi-instrumentator`](https://github.com/trallnag/prometheus-fastapi-instrumentator) 为后端添加 `/metrics` 端点（需要在自定义镜像中安装并在 `app/main.py` 中初始化）。

### 5.4 升级与回滚

1. 拉取最新代码或镜像。
2. 执行 `./deploy.sh down`，再运行 `./deploy.sh up --build` 以获取最新镜像。
3. 若出现回滚需求，可切换回旧版本后再次执行 `./deploy.sh up`。数据库迁移会由 Alembic 管理（如有新增迁移，启动时自动应用）。
4. 镜像 Dockerfile 支持 `linux/amd64` 与 `linux/arm64`，便于在多架构服务器上滚动升级。

---

## 6. 开发者指南

### 6.1 目录结构

```
.
├── backend/          # FastAPI + SQLAlchemy 应用（Poetry 管理）
├── frontend/         # Vite + React + TypeScript 前端
├── config/           # 共享的 lint / format 配置
├── scripts/          # 本地开发辅助脚本
├── docker-compose.yml
├── deploy.sh
└── README.zh-CN.md
```

### 6.2 本地开发

```bash
# 安装依赖
make install

# 启动后端 (FastAPI + Uvicorn)
make dev-backend

# 启动前端 (Vite dev server)
make dev-frontend
```

后端使用 Alembic 管理迁移，可通过 `poetry run alembic revision --autogenerate -m "message"` 创建新迁移。测试命令：

```bash
make lint       # 统一 lint
make format     # 统一格式化
make test       # 后端 pytest + 前端 Vitest
make typecheck  # mypy + TypeScript
```

### 6.3 CI/CD

`.github/workflows` 下提供三条工作流：
- `backend-ci.yml`：运行 Python lint/测试/类型检查。
- `frontend-ci.yml`：运行 ESLint、Vitest、tsc。
- `docker-build.yml`：构建并可选推送多架构镜像。

---

## 7. 常见问题 (FAQ)

| 问题 | 排查建议 |
| --- | --- |
| 证书被标记为“不受信任” | 确认客户端已正确导入根 CA，并重启应用；如使用 Adobe，请在 Trust Manager 中启用对该根的信任。 |
| 签章提示 TSA 失败 | 检查 `TSA_URL` 是否可访问，凭据是否正确；网络需允许访问外部 80/443 端口，可通过 `curl -I $TSA_URL` 预检。 |
| 构建镜像失败 | 确认 Docker 版本 ≥ 23，磁盘空间充足；执行 `docker system prune` 清理缓存后重试 `./deploy.sh up`。 |
| 端口冲突（80/443/5432） | 修改 `.env.docker` 中的 `TRAEFIK_HTTP_PORT`、`TRAEFIK_HTTPS_PORT`、`POSTGRES_HOST_PORT`，然后重新运行 `./deploy.sh up`。 |
| 登录或签章报错 “master key missing” | 请确认 `.env` 中提供了 `ENCRYPTED_STORAGE_MASTER_KEY` 或对应文件路径，并确保其在容器内可读。 |

---

如需进一步定制（接入外部 PKI、扩展审批流程等），建议基于现有 FastAPI 服务编写扩展模块，并保持 `app/services` 中的加密存储接口一致，以符合现有审计与安全约束。
