# ca-pdf 部署指南
> 📖 **文档导航**：[README](./README.md) · [文档索引](./DOCUMENTATION.md) · [安全指南](./SECURITY.md) · [故障排查](./TROUBLESHOOTING.md)
> 🎯 **适用人群**：运维工程师 / 管理员
> ⏱️ **预计阅读时间**：40 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本文为部署与运维提供完整指南。基础项目概览请参阅 [README.md](./README.md)，安全加固策略详见 [SECURITY.md](./SECURITY.md)。部署过程中出现异常时请首先查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。

---

本文档为 ca-pdf 项目的完整部署指南，包含本地开发环境、Docker Compose 部署、生产环境配置等内容。

## 📋 部署概览

### 支持的部署方式

| 方式 | 适用场景 | 难度 | 数据持久化 |
|-----|---------|------|----------|
| **本地开发** | 本地开发调试 | ⭐ | SQLite 文件 |
| **Docker Compose** | 测试、演示、小规模部署 | ⭐⭐ | PostgreSQL 容器卷 |
| **生产环境** | 企业级部署 | ⭐⭐⭐ | 外部 PostgreSQL + 备份 |

### 系统需求

#### 最低配置
- **操作系统**：Linux (推荐 Ubuntu 22.04+) / macOS / Windows (WSL2)
- **CPU**：2核心及以上
- **内存**：4GB RAM（推荐 8GB+）
- **磁盘**：10GB 可用空间（生产环境建议 50GB+）
- **网络**：稳定互联网连接（用于拉取镜像和依赖）

#### 推荐配置（生产环境）
- **操作系统**：Ubuntu 22.04 LTS
- **CPU**：4核心及以上
- **内存**：16GB RAM
- **磁盘**：100GB SSD 存储
- **数据库**：PostgreSQL 12+ 单独服务器

### 网络要求

#### 需要开放的端口

| 端口 | 服务 | 说明 |
|-----|------|------|
| **80** | HTTP | 前端和后端的 HTTP 流量 |
| **443** | HTTPS | 前端和后端的 HTTPS 流量（推荐用于生产） |
| **5432** | PostgreSQL | 数据库访问（仅内部网络） |
| **8000** | Backend API | 后端开发调试（可选） |
| **3000** | Frontend Dev | 前端开发服务器（仅开发环境） |

#### 防火墙配置示例（Ubuntu）
```bash
# 允许 HTTP 和 HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 仅允许特定 IP 访问数据库（如有独立 DB 服务器）
sudo ufw allow from 10.0.0.0/24 to any port 5432 proto tcp
```

---

## 🖥️ 本地开发部署

### 前提条件

- **Python 3.11+** 和 Poetry
- **Node.js 16+** 和 npm
- **PostgreSQL 12+** 或使用 SQLite（开发推荐）
- **Docker** 和 **Docker Compose**（可选，用于快速启动 PostgreSQL）

### 完整步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/QAQ-AWA/ca-pdf.git
cd ca-pdf
```

#### 2. 安装依赖

```bash
# 完整安装（后端和前端）
make install

# 或分别安装
cd backend && poetry install
cd ../frontend && npm install
```

#### 3. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，配置必要的变量
# 生成安全密钥
openssl rand -base64 32  # 用于 SECRET_KEY
openssl rand -base64 32  # 用于 ENCRYPTED_STORAGE_MASTER_KEY
```

示例 .env 配置（本地开发）：
```bash
# 应用配置
APP_NAME=ca-pdf
API_V1_PREFIX=/api/v1
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# 数据库配置（本地开发推荐使用 SQLite）
DATABASE_URL=sqlite+aiosqlite:///./test.db

# 安全配置
SECRET_KEY=your-generated-secret-key-here
ENCRYPTED_STORAGE_MASTER_KEY=your-fernet-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=4320

# 跨域配置（JSON 格式）
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# 管理员配置
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SecurePassword123

# 文件限制
PDF_MAX_BYTES=52428800
PDF_BATCH_MAX_COUNT=10
SEAL_IMAGE_MAX_BYTES=1048576

# 前端配置
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=ca-pdf
```

#### 4. 初始化数据库

##### 使用 SQLite（推荐本地开发）

```bash
cd backend

# 创建数据库并运行迁移
poetry run alembic upgrade head

# 验证迁移状态
poetry run alembic current
```

##### 使用 PostgreSQL（本地）

首先启动 PostgreSQL：

```bash
# 使用 Docker 快速启动 PostgreSQL
docker run --name ca-pdf-db -e POSTGRES_DB=app_db \
  -e POSTGRES_USER=app_user -e POSTGRES_PASSWORD=app_password \
  -p 5432:5432 -d postgres:16

# 配置 .env 中的 DATABASE_URL
DATABASE_URL=postgresql+asyncpg://app_user:app_password@localhost:5432/app_db
```

然后运行迁移：

```bash
cd backend
poetry run alembic upgrade head
```

#### 5. 启动应用

在不同的终端窗口运行以下命令：

```bash
# 终端 1：启动后端 API（自动重载）
make dev-backend

# 终端 2：启动前端开发服务器（Vite）
make dev-frontend
```

#### 6. 首次访问

- **前端应用**：http://localhost:3000
- **后端 API 文档**：http://localhost:8000/docs
- **后端健康检查**：http://localhost:8000/health

使用 .env 中配置的 `ADMIN_EMAIL` 和 `ADMIN_PASSWORD` 登录。

#### 7. 默认账号配置

首次登录后：

1. 前往"证书管理"页面
2. 点击"生成根 CA"
3. 选择密钥算法（RSA-4096 或 EC-P256）和有效期
4. 点击"生成"完成根 CA 创建

之后可以开始签章和验签操作。

---

## 🐳 Docker Compose 部署

### 一行安装 & 菜单化运维

ca-pdf 提供 `scripts/install.sh` 安装器，可在全新主机上一条命令完成依赖准备与首次部署：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
```

安装器能力概览：

1. **自动检测环境**：校验 Bash 版本、Docker/Compose 是否可用，检测 80/443 端口、内存与磁盘空间是否满足要求。
2. **自动安装依赖**：识别 Ubuntu/Debian、CentOS/Alma/Rocky、Fedora、openSUSE、Arch 等主流发行版，自动安装 curl、git、jq、openssl、docker、docker compose v2 等包，必要时尝试使用 `sudo`。
3. **安全生成配置**：下载最新的 `.env.example`、`.env.docker.example`、`docker-compose.yml`、Traefik 配置模板，生成 `.env`/`.env.docker`，并使用 `openssl rand -hex 32` 创建强随机密钥。
4. **支持多模式证书**：生产模式默认使用 Let's Encrypt，自动配置 ACME；本地模式则生成 `localtest.me` 自签证书。
5. **幂等部署**：创建或更新 Docker Compose 栈，等待健康检查完成后自动执行 Alembic 迁移，日志记录在 `logs/installer-YYYYMMDD.log`。
6. **菜单化管理**：安装完成后在 `/usr/local/bin` 注册 `capdf` 命令，可随时进入交互式菜单执行安装、升级、备份、恢复、自更新等操作。

安装完成后可直接运行：

```bash
capdf menu
```

常用子命令如下：

```bash
capdf install      # 重新进入安装向导
capdf up           # 构建并启动（或升级）所有服务
capdf down         # 停止服务，保留数据卷
capdf down --clean # 停止并删除容器与数据卷
capdf logs -f      # 实时查看全部日志
capdf backup       # 导出数据库 + 配置备份
capdf restore      # 从备份恢复
capdf doctor       # 健康检查（端口、资源、数据库连接等）
capdf self-update  # 从远程仓库拉取最新脚本
```

> ℹ️ 离线或 CI 环境仍可在仓库根目录使用 `scripts/deploy.sh` / `./deploy.sh`，其子命令与 `capdf` 保持一致，但需手动满足依赖。

### 环境准备

1. **安装 Docker**（版本 23+）和 **Docker Compose**（V2）
2. **准备环境文件**

```bash
cp .env.example .env
cp .env.docker.example .env.docker
```

### 配置说明

#### docker-compose.yml 服务

| 服务 | 镜像 | 描述 |
|-----|------|------|
| **traefik** | traefik:v3.1 | 反向代理，处理 SSL/TLS 和路由 |
| **db** | postgres:16 | PostgreSQL 数据库 |
| **backend** | 自定义构建 | FastAPI 后端应用 |
| **frontend** | 自定义构建 | React 前端应用 |

### 快速启动

```bash
# 一键启动全栈（包含所有服务）
capdf up

# 查看容器状态
capdf status

# 查看实时日志
capdf logs -f

# 查看特定服务日志
capdf logs backend
capdf logs frontend
capdf logs db
```

### 构建镜像

```bash
# 首次启动时自动构建镜像
capdf up

# 重新构建镜像（不更新已启动的容器）
docker compose build

# 强制重新构建并重启
docker compose up -d --build
```

### 查看日志

```bash
# 实时查看所有日志
capdf logs -f

# 查看特定服务最后 100 行日志
capdf logs backend --tail 100

# 查看从特定时间开始的日志
docker compose logs --since 10m backend
```

### 停止和清理

```bash
# 停止所有容器（保留数据卷）
capdf down

# 停止并删除所有容器和数据卷（谨慎使用！）
capdf down --clean

# 重启应用（适合更新后）
capdf restart
```

### 数据备份

```bash
# 备份 PostgreSQL 数据
docker compose exec db pg_dump -U app_user -d app_db > backup-$(date +%Y%m%d).sql

# 备份 Traefik SSL 证书
docker compose exec traefik cat /letsencrypt/acme.json > acme-$(date +%Y%m%d).json

# 备份应用数据卷
docker run --rm -v ca-pdf_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-data-$(date +%Y%m%d).tar.gz -C /data .
```

---

## 🔐 环境变量配置

### 关键变量说明

| 变量 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| **DATABASE_URL** | String | 数据库连接字符串（PostgreSQL 或 SQLite） | `postgresql+asyncpg://user:pass@host:5432/db` |
| **ENCRYPTED_STORAGE_MASTER_KEY** | String | 加密存储主密钥（Fernet 格式，必填） | `openssl rand -base64 32` |
| **SECRET_KEY** | String | JWT 签发密钥 | `openssl rand -base64 32` |
| **ADMIN_EMAIL** | Email | 首次启动自动创建的管理员邮箱 | `admin@company.com` |
| **ADMIN_PASSWORD** | String | 首次启动自动创建的管理员密码 | `SecurePass123!` |
| **BACKEND_CORS_ORIGINS** | JSON | 跨域请求白名单（**必须是 JSON 格式**） | `["https://example.com"]` |
| **ACCESS_TOKEN_EXPIRE_MINUTES** | Int | Access Token 过期时间 | 15 |
| **REFRESH_TOKEN_EXPIRE_MINUTES** | Int | Refresh Token 过期时间（分钟） | 4320 |
| **PDF_MAX_BYTES** | Int | 最大 PDF 文件大小（字节，默认 50MB） | 52428800 |
| **SEAL_IMAGE_MAX_BYTES** | Int | 最大企业印章文件大小（默认 1MB） | 1048576 |
| **TSA_URL** | String | 时间戳服务地址（可选） | `https://freetsa.org/tsr` |
| **BACKEND_DOMAIN** | String | 后端 API 域名（Traefik 使用） | `api.company.com` |
| **FRONTEND_DOMAIN** | String | 前端应用域名（Traefik 使用） | `app.company.com` |
| **TRAEFIK_ACME_EMAIL** | Email | Let's Encrypt 证书邮箱 | `admin@company.com` |

### 生成加密密钥

```bash
# 生成 Fernet 密钥（推荐用于 ENCRYPTED_STORAGE_MASTER_KEY）
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 生成随机密钥（用于 SECRET_KEY）
openssl rand -base64 32

# Python 方法
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### .env 文件示例

```bash
# 基础配置
APP_NAME=ca-pdf
API_V1_PREFIX=/api/v1

# 数据库配置
DATABASE_URL=postgresql+asyncpg://app_user:secure_password@db:5432/app_db

# 安全配置
SECRET_KEY=your-secret-key-from-openssl-rand
ENCRYPTED_STORAGE_MASTER_KEY=your-fernet-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=4320

# 跨域配置（JSON 格式）
BACKEND_CORS_ORIGINS=["https://app.company.com"]

# 管理员配置
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=SecureAdminPassword123!

# 文件限制
PDF_MAX_BYTES=52428800
SEAL_IMAGE_MAX_BYTES=1048576

# Traefik 配置
BACKEND_DOMAIN=api.company.com
FRONTEND_DOMAIN=app.company.com
TRAEFIK_ACME_EMAIL=admin@company.com

# 前端配置
VITE_API_BASE_URL=https://api.company.com
VITE_APP_NAME=CA PDF Signature
```

---

## 💾 数据库配置

### PostgreSQL 初始化

#### 本地 PostgreSQL 安装（Ubuntu）

```bash
# 安装 PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql <<EOF
CREATE USER app_user WITH PASSWORD 'secure_password';
CREATE DATABASE app_db OWNER app_user;
GRANT ALL PRIVILEGES ON DATABASE app_db TO app_user;
EOF

# 验证连接
psql -h localhost -U app_user -d app_db -c "SELECT version();"
```

#### 云托管 PostgreSQL（推荐生产环境）

- **AWS RDS**：https://aws.amazon.com/rds/postgresql/
- **Azure Database**：https://azure.microsoft.com/services/postgresql/
- **Google Cloud SQL**：https://cloud.google.com/sql/docs/postgres
- **DigitalOcean Managed Database**：https://www.digitalocean.com/products/managed-databases/

### 运行 Alembic 迁移

> ♻️ **容器自动迁移**：从 2024 年 11 月起，后端容器启动会自动运行 `backend/scripts/prestart.sh`，按顺序执行以下操作：
> - 指数退避轮询数据库连接（初始 1 秒，最大 30 次重试）；
> - 最多 3 次重试执行 `alembic upgrade head`，避免偶发网络或锁冲突；
> - 迁移成功后才会启动 Gunicorn 服务，确保服务始终运行在最新 schema 上。
>
> 若自动迁移失败，容器会直接退出并在日志中给出详尽提示，可通过 `docker compose logs backend` 查看原因。

#### 手动执行（开发 / 调试）

本地开发或紧急排查时仍可手动执行迁移命令：

```bash
cd backend

# 升级到最新版本
poetry run alembic upgrade head

# 查看当前版本
poetry run alembic current

# 查看迁移历史
poetry run alembic history --verbose

# 降级到特定版本（谨慎使用）
poetry run alembic downgrade -1
```

### 数据备份策略

```bash
# 创建备份目录
mkdir -p /var/backups/ca-pdf

# 完整备份脚本
#!/bin/bash
BACKUP_DIR="/var/backups/ca-pdf"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="app_db"
DB_USER="app_user"

# 备份数据库
pg_dump -h localhost -U ${DB_USER} -d ${DB_NAME} | \
  gzip > ${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz

# 保留最近 30 天的备份
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
```

#### 定时备份（Cron）

```bash
# 每天凌晨 2 点执行备份
0 2 * * * /var/backups/ca-pdf/backup.sh

# 编辑 crontab
crontab -e
```

### 数据恢复步骤

```bash
# 停止应用
capdf down

# 恢复备份
gunzip -c /var/backups/ca-pdf/app_db_*.sql.gz | \
  psql -h localhost -U app_user -d app_db

# 验证恢复
psql -h localhost -U app_user -d app_db -c "SELECT COUNT(*) FROM users;"

# 重启应用
capdf up
```

---

## 🔄 反向代理配置（Traefik）

### Traefik 配置说明

在 `docker-compose.yml` 中，Traefik 服务通过命令行参数配置。主要配置项：

| 配置 | 说明 |
|-----|------|
| **providers.docker** | 启用 Docker 提供者 |
| **entrypoints** | HTTP/HTTPS 监听端口 |
| **certificatesresolvers** | 证书解析器（Let's Encrypt） |
| **log.level** | 日志级别 |

### 域名配置

#### 本地开发（localtest.me）

```bash
# .env 配置
BACKEND_DOMAIN=api.localtest.me
FRONTEND_DOMAIN=app.localtest.me

# 无需修改 /etc/hosts，localtest.me 自动解析到 127.0.0.1
```

#### 生产环境（自定义域名）

```bash
# .env 配置
BACKEND_DOMAIN=api.company.com
FRONTEND_DOMAIN=app.company.com

# 配置 DNS A 记录指向服务器 IP
api.company.com     A    192.0.2.1
app.company.com     A    192.0.2.1
```

### SSL/TLS 配置

#### 自动 SSL（Let's Encrypt）

```bash
# .env 配置（生产环境）
TRAEFIK_ACME_CA_SERVER=https://acme-v02.api.letsencrypt.org/directory
TRAEFIK_ACME_EMAIL=admin@company.com

# 本地开发（使用 Let's Encrypt 测试环境）
TRAEFIK_ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory
```

#### 验证 SSL 证书

```bash
# 检查证书有效期
openssl s_client -connect api.company.com:443 -showcerts | \
  openssl x509 -noout -dates
```

---

## 🚀 生产部署建议

### 性能优化

#### 数据库连接池配置

```bash
# 环境变量设置
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

#### 缓存策略

- 使用 Redis 缓存 JWT Token 黑名单
- 缓存频繁查询的证书列表
- 缓存用户权限信息

#### 静态文件 CDN

```bash
# 前端构建生成的 dist 文件可上传到 CDN
# 配置 .env
VITE_PUBLIC_BASE_URL=https://cdn.company.com
```

### 监控和日志

#### 应用日志查看

```bash
# 查看实时日志
capdf logs -f backend

# 导出日志到文件
docker compose logs backend > app.log 2>&1

# 查看错误日志
docker compose logs backend | grep ERROR
```

#### 性能指标收集

```bash
# 监控容器资源使用
docker compose stats

# 查看 SQL 日志（开发环境仅用）
# DATABASE_ECHO=true
```

### 安全加固

#### HTTPS 配置

```bash
# 确保所有流量都通过 HTTPS
TRAEFIK_ACME_CA_SERVER=https://acme-v02.api.letsencrypt.org/directory
```

#### 防火墙规则

```bash
# 只允许必要的端口
sudo ufw default deny incoming
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
```

#### 定期备份

- 每日自动备份数据库
- 备份 Traefik SSL 证书
- 定期验证备份可恢复性

#### 密钥轮换计划

- **SECRET_KEY**：每 6 个月轮换
- **ENCRYPTED_STORAGE_MASTER_KEY**：每 12 个月轮换
- **数据库密码**：每 3 个月轮换

---

## 🐛 故障排查

### 常见部署问题

#### 1. 端口被占用

```bash
# 查看占用端口的进程
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000

# 修改 .env 中的端口
TRAEFIK_HTTP_PORT=8080
TRAEFIK_HTTPS_PORT=8443
```

#### 2. 数据库连接失败

```bash
# 检查数据库是否运行
docker compose ps db

# 查看数据库日志
capdf logs db

# 验证 DATABASE_URL 格式
DATABASE_URL=postgresql+asyncpg://app_user:password@db:5432/app_db
```

#### 3. CORS 配置错误

```bash
# 错误示例（字符串格式）
BACKEND_CORS_ORIGINS=https://app.company.com

# 正确示例（JSON 数组格式）
BACKEND_CORS_ORIGINS=["https://app.company.com"]
```

#### 4. 环境变量缺失

```bash
# 检查所需变量
docker compose exec backend env | grep -E "SECRET_KEY|ENCRYPTED"
```

#### 5. 容器健康检查失败

健康检查失败通常表现为容器状态为 `unhealthy` 或服务无法通过 Traefik 访问。

##### Traefik 容器 unhealthy

```bash
# 查看 Traefik 日志
capdf logs traefik

# 检查 Traefik ping 端点
curl http://localhost/ping

# 验证动态配置文件
cat config/traefik/dynamic.yml

# 常见错误：
# - "dial tcp: lookup frontend/backend on 127.0.0.11:53: server misbehaving"
#   => DNS 解析问题，检查 Docker 网络配置
# - "context deadline exceeded"
#   => 健康检查超时，增加 timeout 或 start_period
```

##### 后端健康检查失败

```bash
# 直接测试后端健康检查端点
docker compose exec backend curl -v http://127.0.0.1:8000/health

# 检查数据库连接
docker compose exec backend env | grep DATABASE_URL

# 查看后端日志
capdf logs backend

# 常见原因：
# - 数据库未就绪：增加 start_period（当前 40s）
# - 应用启动慢：检查 WEB_CONCURRENCY 和资源限制
# - 端点响应慢：优化 /health 端点（当前为简单响应）
```

##### 前端健康检查失败

```bash
# 直接测试前端健康检查端点
docker compose exec frontend wget --spider -q http://127.0.0.1:8080/healthz && echo "OK" || echo "FAIL"

# 检查 nginx 配置
docker compose exec frontend cat /etc/nginx/conf.d/default.conf

# 查看前端日志
capdf logs frontend

# 注意：
# - 前端健康检查路径：/healthz（不是 /）
# - nginx 监听端口：8080
# - 健康检查超时：10s，start_period：30s
```

##### Traefik 负载均衡器健康检查配置

Traefik 的动态配置文件中定义了服务健康检查：

```yaml
# config/traefik/dynamic.yml
services:
  backend:
    loadBalancer:
      servers:
        - url: "http://backend:8000"
      healthCheck:
        path: "/health"        # 后端健康检查路径
        interval: "30s"        # 每 30 秒检查一次
        timeout: "10s"         # 超时 10 秒
  
  frontend:
    loadBalancer:
      servers:
        - url: "http://frontend:8080"
      healthCheck:
        path: "/healthz"       # 前端健康检查路径（注意不是 /）
        interval: "30s"
        timeout: "10s"
```

如果需要修改健康检查配置：

```bash
# 1. 编辑 config/traefik/dynamic.yml
vim config/traefik/dynamic.yml

# 2. 重启 Traefik 服务
docker compose restart traefik

# 3. 验证配置生效
docker compose logs traefik | grep -i health
```

### 日志查看方法

```bash
# 查看所有服务日志
capdf logs

# 实时监控后端日志
capdf logs -f backend

# 查看最后 50 行日志
capdf logs backend --tail 50

# 保存日志到文件
docker compose logs > app_$(date +%Y%m%d_%H%M%S).log 2>&1
```

### 容器检查命令

```bash
# 查看容器状态
capdf status

# 进入容器 Shell
docker compose exec backend bash

# 查看容器资源使用
docker compose stats

# 查看容器网络
docker network ls
docker network inspect ca-pdf_internal
```

---

## 📦 升级和维护

### 应用升级步骤

```bash
# 1. 备份数据
docker compose exec db pg_dump -U app_user app_db > backup.sql

# 2. 拉取最新代码
git pull origin main

# 3. 更新迁移
cd backend
poetry run alembic upgrade head

# 4. 重建并重启
docker compose up -d --build
```

### 数据库版本升级

```bash
# 1. 备份数据
docker compose exec db pg_dump -U app_user app_db > backup.sql

# 2. 停止服务
capdf down

# 3. 修改 docker-compose.yml 中的 PostgreSQL 版本
# image: postgres:16  # 改为 postgres:17

# 4. 启动并验证
capdf up
```

### 备份验证

```bash
# 定期验证备份可恢复性
createdb test_app_db
psql test_app_db < backup.sql

# 验证数据完整性
psql test_app_db -c "SELECT COUNT(*) FROM users;"
```

---

## ⚡ 性能调优

### 后端性能配置

#### Gunicorn 工作进程数

```bash
# 环境变量配置
WEB_CONCURRENCY=4

# 公式：(CPU 核心数 * 2) + 1
```

#### 数据库查询优化

```bash
# 添加适当的数据库索引
# 避免 N+1 查询问题
# 使用连接池管理连接

# 启用慢查询日志
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

### 前端构建优化

```bash
# 启用代码分割和懒加载
# vite.config.ts 中配置 rollupOptions
# 生成构建分析报告
npm run build -- --analyze
```

---

## 📞 支持和反馈

- **GitHub Issues**：https://github.com/QAQ-AWA/ca-pdf/issues
- **GitHub Discussions**：https://github.com/QAQ-AWA/ca-pdf/discussions
- **邮件**：7780102@qq.com

---

**版本**：1.0  
**更新时间**：2024 年  
**维护者**：ca-pdf 开发团队
---

🔗 **相关文档**
- [安全指南](./SECURITY.md)
- [故障排查](./TROUBLESHOOTING.md)
- [文档索引](./DOCUMENTATION.md)
- [架构概览](./ARCHITECTURE.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

