# Ticket Summary: Fix Alembic Migration Names and Enhance Deployment Script Robustness

## 概述 (Overview)

本次任务解决了生产部署中遇到的核心问题，并显著增强了部署脚本的健壮性和用户体验。

This task resolved critical production deployment issues and significantly enhanced the robustness and user experience of deployment scripts.

---

## ✅ 完成的工作 (Completed Work)

### 1. Alembic 迁移文件名修复 (Alembic Migration Name Fix)

#### 问题 (Problem)
- **根本原因**: PostgreSQL 的 `alembic_version` 表中 `version_num` 列为 `VARCHAR(32)`
- **错误症状**: KeyError: '0002_rename_audit_logs_metadata_to_meta' (38 字符超过限制)
- **影响**: 数据库迁移失败，阻塞部署流程

#### 解决方案 (Solution)
1. **重命名迁移文件**:
   - 原文件名: `0002_rename_audit_logs_metadata_to_meta.py`
   - 新文件名: `0002_rename_audit_meta.py`
   - Revision ID: `0002_rename_audit_meta` (22 字符 ✓)

2. **更新依赖引用**:
   - 文件: `backend/app/db/migrations/versions/0003_add_username_to_users.py`
   - 修改: `down_revision` 从 `"0002_rename_audit_logs_metadata_to_meta"` → `"0002_rename_audit_meta"`

3. **验证迁移链**:
   ```
   0001_initial_schema (19 chars) ✓
     ↓
   0002_rename_audit_meta (22 chars) ✓
     ↓
   0003_add_username_to_users (26 chars) ✓
   ```

#### 验收标准 (Acceptance Criteria)
- ✅ 所有 Alembic 迁移 revision ID ≤ 32 字符
- ✅ `alembic upgrade head` 成功执行
- ✅ 迁移链完整且正确引用

---

### 2. 部署脚本增强功能 (Deployment Script Enhancements)

#### 2.1 新增命令行参数 (New Command-Line Parameters)

为 `capdf install` 命令添加了 4 个新参数：

```bash
capdf install [选项]
  --force-clean       强制清理旧数据卷和目录
  --no-cache          Docker 镜像构建不使用缓存
  --force-stop        自动停止占用端口的容器
  --skip-validation   跳过部署后验证（不推荐）
```

**使用示例**:
```bash
# 完全清理并重建
capdf install --force-clean --no-cache

# 自动处理端口冲突
capdf install --force-stop

# 快速安装（跳过验证）
capdf install --skip-validation
```

#### 2.2 端口占用检测 (Port Occupation Detection)

**新增功能**:
- 检测端口: 80, 443, 5432, 8000
- 显示占用进程信息（使用 `ss` 或 `lsof`）
- `--force-stop` 参数自动停止占用端口的 Docker 容器
- 友好的错误提示和解决建议

**实现文件**: `scripts/deploy.sh` - `check_port()` 函数

**关键代码逻辑**:
```bash
# 增强的端口检查，支持强制停止
check_port() {
  local port="$1"
  local force_stop="${2:-0}"
  
  # 检测端口占用
  if port_in_use; then
    if (( force_stop )); then
      # 自动停止 Docker 容器
      stop_containers_on_port
    else
      # 提示用户手动处理
      show_error_and_suggestions
    fi
  fi
}
```

#### 2.3 PostgreSQL 数据清理逻辑 (PostgreSQL Data Cleanup Logic)

**新增函数**: `clean_old_data()`

**功能特性**:
- 检测已存在的 Docker Compose 栈
- 检测 PostgreSQL 数据目录（默认: `${PROJECT_ROOT}/data/postgres`）
- 交互式确认清理操作
- `--force-clean` 参数自动清理无需确认
- 清理内容:
  - 停止并删除容器和数据卷
  - 删除 PostgreSQL 数据目录
  - 清理匹配 `ca_pdf` 或 `ca-pdf` 的 Docker 数据卷

**使用场景**:
- 重新安装时清理旧数据
- 解决数据库损坏问题
- 版本升级需要重置数据库

#### 2.4 Docker 构建缓存管理 (Docker Build Cache Management)

**实现位置**: `start_stack()` 函数

**功能**:
```bash
# 默认使用缓存（快速构建）
capdf install

# 强制重建（忽略缓存）
capdf install --no-cache
```

**内部逻辑**:
```bash
if (( NO_CACHE )) || (( FORCE_REBUILD )); then
  docker compose build --no-cache
else
  docker compose build
fi
```

**适用场景**:
- 版本更新时确保使用最新代码
- 故障排查时排除缓存问题
- 依赖包更新后强制重新安装

#### 2.5 部署失败自动回滚 (Auto Rollback on Failure)

**增强的错误处理**: `on_error()` 函数

**改进内容**:
```bash
on_error() {
  if (( DEPLOY_STARTED )); then
    # 停止并删除容器
    docker compose down --remove-orphans
    
    # 清理部分构建的镜像
    docker image prune -f --filter "dangling=true"
  fi
  
  # 显示日志文件位置
  log_error "请查看日志：${LOG_FILE}"
}
```

**触发条件**:
- 任何脚本执行错误 (通过 `trap ERR`)
- 服务启动超时
- 数据库迁移失败
- 健康检查失败

**清理操作**:
- 停止所有容器
- 删除孤立容器
- 清理悬空镜像
- 保留日志以供排查

#### 2.6 健康检查和验证 (Health Checks and Validation)

**新增函数**: `validate_deployment()`

**验证内容**:
1. **服务运行状态**:
   - traefik
   - db (PostgreSQL)
   - backend (FastAPI)
   - frontend (Vue.js)

2. **后端 API 健康检查**:
   - URL: `${BACKEND_URL}/health`
   - 方法: HTTP GET with curl
   - 超时: 10 秒

3. **数据库迁移验证**:
   - 命令: `alembic upgrade head`
   - 错误处理: 迁移失败时显示详细错误
   - 日志提示: 建议查看 `capdf logs backend`

**输出示例**:
```
==> 验证部署状态
ℹ 检查服务运行状态...
✔ 服务 traefik 运行中
✔ 服务 db 运行中
✔ 服务 backend 运行中
✔ 服务 frontend 运行中
✔ 所有服务运行正常（4/4）
ℹ 验证后端 API...
✔ 后端 API 健康检查通过: https://api.localtest.me/health
✔ 部署验证完成
```

#### 2.7 增强的帮助文档 (Enhanced Help Documentation)

**更新内容**: `print_help()` 函数

**新增章节**:
1. **install 命令选项详解**
2. **使用示例**（5 个场景）
3. **部署流程清单**（9 个步骤）

**帮助文本示例**:
```
用法: capdf <命令> [参数]

install 命令选项：
  --force-clean       强制清理旧数据卷和 PostgreSQL 数据目录
  --no-cache          Docker 镜像构建时不使用缓存（强制重新构建）
  --force-stop        自动停止占用端口 (80/443/5432/8000) 的 Docker 容器
  --skip-validation   跳过部署后的验证步骤（不推荐）

部署流程（install 命令执行步骤）：
  1. ✓ 环境预检查（操作系统、Docker、端口、资源）
  2. ✓ 端口占用检查（80/443/5432/8000）
  3. ✓ 交互式配置（域名、邮箱、数据库路径、CORS）
  4. ✓ 旧数据清理提示（可选）
  5. ✓ 生成配置文件（.env、docker-compose.yml）
  6. ✓ Docker Compose 启动（支持缓存控制）
  7. ✓ Alembic 数据库迁移验证
  8. ✓ 服务健康检查验证
  9. ✓ 部署失败自动回滚清理
```

---

## 📋 验收标准检查表 (Acceptance Criteria Checklist)

### 代码修复 (Code Fixes)
- ✅ Alembic 迁移名称 ≤32 字符
- ✅ `alembic upgrade head` 成功执行
- ✅ 迁移链正确且完整

### 脚本功能 (Script Features)
- ✅ 支持 `--force-clean` 参数自动清理旧数据
- ✅ 支持 `--no-cache` 参数强制重建镜像
- ✅ 部署前检测端口 5432 和 8000 占用
- ✅ 部署前检测端口 80 和 443 占用
- ✅ 支持 `--force-stop` 参数自动停止占用端口的容器
- ✅ 部署失败时自动回滚清理
- ✅ 执行 Alembic 迁移验证
- ✅ 执行服务健康检查验证
- ✅ 完整部署流程可重复执行无需手动干预

### 文档 (Documentation)
- ✅ 所有参数在 `capdf --help` 中有文档说明
- ✅ 部署流程清单完整
- ✅ 使用示例丰富且实用

---

## 🔧 技术实现细节 (Technical Implementation Details)

### 文件修改清单 (Modified Files)

1. **backend/app/db/migrations/versions/0002_rename_audit_meta.py**
   - 重命名自: `0002_rename_audit_logs_metadata_to_meta.py`
   - 内容: revision ID 已经是正确的 22 字符版本

2. **backend/app/db/migrations/versions/0003_add_username_to_users.py**
   - 修改行 9: `down_revision = "0002_rename_audit_meta"`
   - 原值: `"0002_rename_audit_logs_metadata_to_meta"`

3. **scripts/deploy.sh**
   - 新增全局变量: `FORCE_CLEAN`, `FORCE_REBUILD`, `NO_CACHE`, `FORCE_STOP`, `SKIP_VALIDATION`
   - 新增函数: `clean_old_data()`, `validate_deployment()`
   - 增强函数: `check_port()`, `on_error()`, `run_migrations()`, `start_stack()`, `command_install()`, `print_help()`
   - 代码行数: ~1,670 行 (增加约 150 行)

### 新增函数签名 (New Function Signatures)

```bash
# 清理旧数据
clean_old_data() {
  local force="${1:-0}"
  # 检测并清理现有数据
}

# 验证部署
validate_deployment() {
  # 检查服务状态
  # 测试 API 健康检查
}

# 增强的端口检查
check_port() {
  local port="$1"
  local force_stop="${2:-0}"
  # 检测并可选择性地自动停止占用进程
}
```

---

## 🎯 使用场景示例 (Usage Scenarios)

### 场景 1: 首次部署
```bash
# 标准安装流程
capdf install
```

### 场景 2: 重新安装（清理旧数据）
```bash
# 自动清理所有旧数据
capdf install --force-clean

# 或交互式确认清理
capdf install
# 脚本会询问: "是否清理旧数据并重新开始？"
```

### 场景 3: 解决端口冲突
```bash
# 自动停止占用 80/443/5432/8000 的 Docker 容器
capdf install --force-stop
```

### 场景 4: 强制重建镜像（版本更新）
```bash
# 忽略 Docker 缓存，完全重新构建
capdf install --no-cache
```

### 场景 5: 完全清理并重建
```bash
# 组合使用多个参数
capdf install --force-clean --no-cache --force-stop
```

### 场景 6: 快速安装（跳过验证）
```bash
# 适用于测试环境，不推荐生产环境
capdf install --skip-validation
```

---

## 🐛 故障排查 (Troubleshooting)

### 常见问题和解决方案

#### 问题 1: 端口已被占用
**错误信息**:
```
✖ 端口 5432 已被占用，请释放后重试。
提示: 使用 --force-stop 参数可自动停止占用端口的容器
```

**解决方案**:
```bash
# 方案 A: 自动停止容器
capdf install --force-stop

# 方案 B: 手动停止进程
lsof -i :5432
kill <PID>

# 方案 C: 停止所有 Docker 容器
docker stop $(docker ps -q)
```

#### 问题 2: 数据库迁移失败
**错误信息**:
```
✖ 数据库迁移失败
提示: 查看日志 capdf logs backend
```

**解决方案**:
```bash
# 1. 查看后端日志
capdf logs backend

# 2. 如果是数据损坏，清理并重新安装
capdf install --force-clean

# 3. 手动执行迁移（调试）
docker compose exec backend alembic upgrade head
```

#### 问题 3: 构建缓存导致的问题
**症状**: 代码更新后服务行为未变化

**解决方案**:
```bash
# 强制重新构建镜像
capdf install --no-cache
```

#### 问题 4: 旧数据导致的冲突
**症状**: PostgreSQL 启动失败或数据不一致

**解决方案**:
```bash
# 清理所有旧数据
capdf install --force-clean
```

---

## 📊 性能和影响分析 (Performance and Impact Analysis)

### 脚本执行时间估算

| 操作 | 无缓存 | 有缓存 | 说明 |
|------|--------|--------|------|
| 环境检查 | 5-10s | 5-10s | 网络、资源、端口检查 |
| 数据清理 | 10-30s | N/A | 仅在 --force-clean 时执行 |
| Docker 构建 | 5-10 分钟 | 1-2 分钟 | 取决于网络速度 |
| 容器启动 | 30-60s | 30-60s | 等待服务就绪 |
| 数据库迁移 | 5-10s | 5-10s | Alembic 迁移执行 |
| 健康检查 | 10-20s | 10-20s | API 和服务验证 |
| **总计** | **8-12 分钟** | **3-5 分钟** | 首次安装 vs 更新 |

### 兼容性

- ✅ Ubuntu 20.04/22.04/24.04
- ✅ Debian 11/12
- ✅ CentOS 7/8
- ✅ Rocky Linux 8/9
- ✅ AlmaLinux 8/9
- ✅ openSUSE Leap 15.x
- ✅ Arch Linux
- ✅ Docker Compose V1 和 V2

---

## 🔒 安全考虑 (Security Considerations)

### 数据清理安全
- `--force-clean` 参数会**永久删除**数据库数据
- 建议在生产环境使用前先备份: `capdf backup`
- 清理操作记录在日志文件中

### 端口强制停止
- `--force-stop` 仅停止 **Docker 容器**
- 不会影响宿主机上的原生服务
- 如需停止非容器进程，需手动处理

### 验证跳过风险
- `--skip-validation` 跳过健康检查
- 可能导致部署不完整但脚本仍报告成功
- **不推荐在生产环境使用**

---

## 📝 更新日志 (Changelog)

### [v3.0] - 2024-12-19

#### 修复 (Fixed)
- 修复 Alembic 迁移名称超过 32 字符限制导致的 KeyError
- 更新迁移引用链保持一致性

#### 新增 (Added)
- `--force-clean`: 强制清理旧数据参数
- `--no-cache`: 强制重建 Docker 镜像参数
- `--force-stop`: 自动停止占用端口的容器参数
- `--skip-validation`: 跳过部署验证参数（不推荐）
- `clean_old_data()`: 旧数据清理函数
- `validate_deployment()`: 部署验证函数
- 端口 5432 和 8000 的占用检测
- 自动回滚失败部署的镜像清理

#### 改进 (Improved)
- 增强 `check_port()` 支持强制停止容器
- 增强 `on_error()` 自动清理悬空镜像
- 增强 `run_migrations()` 添加错误处理
- 增强 `start_stack()` 支持无缓存构建
- 完善帮助文档，添加参数说明和使用示例
- 添加部署流程清单到帮助文档

---

## 🎓 开发者注意事项 (Developer Notes)

### 创建新的 Alembic 迁移
```bash
# 使用短名称
alembic revision -m "short_name"

# ❌ 错误示例（超过 32 字符）
alembic revision -m "rename_audit_logs_metadata_to_meta"

# ✅ 正确示例（≤ 32 字符）
alembic revision -m "rename_audit_meta"
```

### 迁移 Revision ID 命名规范
- **格式**: `{序号}_{简短描述}`
- **最大长度**: 32 字符
- **命名建议**:
  - 使用下划线分隔单词
  - 省略冗余词汇（如 logs、table、column）
  - 使用缩写（metadata → meta）
  - 保持描述性但简洁

### 测试部署脚本更改
```bash
# 1. 语法检查
bash -n scripts/deploy.sh

# 2. 在测试环境运行
capdf install --skip-validation

# 3. 验证所有参数组合
capdf install --force-clean --no-cache --force-stop

# 4. 测试错误处理
# 人为制造失败（如停止 Docker）并验证回滚
```

---

## 📚 相关文档 (Related Documentation)

- [DEPLOYMENT.md](DEPLOYMENT.md) - 完整部署指南
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献者指南
- [SECURITY.md](SECURITY.md) - 安全指南
- [API.md](API.md) - API 参考文档

---

## 👥 作者和贡献者 (Authors and Contributors)

- **Task**: Fix Alembic migration names and enhance deployment script robustness
- **Date**: 2024-12-19
- **Branch**: `fix-alembic-migration-names-deploy-script-robustness`

---

## 📞 支持 (Support)

如有问题或建议，请：
- 提交 GitHub Issue: https://github.com/QAQ-AWA/ca-pdf/issues
- 查看诊断日志: `capdf export-logs`
- 运行系统诊断: `capdf doctor`
- 邮箱联系: 7780102@qq.com

---

**总结**: 本次更新显著提升了 ca-pdf 部署脚本的健壮性和用户体验，解决了关键的数据库迁移问题，并为用户提供了更灵活的部署选项和更好的错误处理机制。
