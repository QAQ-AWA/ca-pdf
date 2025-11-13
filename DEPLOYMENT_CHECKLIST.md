# ca-pdf 部署流程检查清单

> 本文档提供完整的部署前、部署中、部署后检查清单，确保部署成功率。

## 📋 部署前检查清单

### 系统环境

- [ ] **操作系统**: Linux 发行版（Ubuntu/Debian/CentOS/Rocky/AlmaLinux/openSUSE/Arch）
- [ ] **CPU**: 至少 1 核（推荐 2 核+）
- [ ] **内存**: 至少 2GB RAM
- [ ] **磁盘空间**: 至少 5GB 可用
- [ ] **权限**: root 用户或具有 sudo 权限

### 网络环境

- [ ] **外网连接**: 能够访问互联网
- [ ] **GitHub 访问**: `curl -I https://github.com` 成功
- [ ] **Docker Hub 访问**: `curl -I https://hub.docker.com` 成功
- [ ] **代理配置**（如需要）: 已设置 `http_proxy`/`https_proxy`
- [ ] **DNS 解析**: `nslookup github.com` 成功

### 端口可用性

- [ ] **80 端口**: HTTP（未被占用）
- [ ] **443 端口**: HTTPS（未被占用）
- [ ] **8000 端口**: 后端 API（未被占用，可选）
- [ ] **3000 端口**: 前端开发（未被占用，可选）
- [ ] **5432 端口**: PostgreSQL（未被占用，可选）

检查命令：
```bash
# 检查端口占用
ss -ltn | grep -E ':(80|443|8000|3000|5432)\s'
# 或
lsof -i :80,443,8000,3000,5432
```

### 防火墙配置

- [ ] **UFW/iptables**: 已允许 80/443 端口入站
- [ ] **云服务安全组**: 已开放 80/443 端口

```bash
# UFW 示例
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

---

## 🚀 部署中检查清单

### 执行一键安装

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
```

### 安装过程监控

- [ ] **系统资源检查**: 通过（CPU/内存/磁盘警告已确认）
- [ ] **依赖安装**: curl、git、jq、openssl、tar、gzip 安装成功
- [ ] **Docker 安装**: Docker Engine 安装成功
- [ ] **Docker Compose**: V2 或 V1 检测成功
- [ ] **网络检查**: GitHub 连接成功（3次重试内）
- [ ] **代码克隆**: 项目代码克隆完成
- [ ] **结构验证**: backend/、frontend/ 目录存在
- [ ] **脚本安装**: deploy.sh 下载成功
- [ ] **启动器创建**: /usr/local/bin/capdf 创建成功

### 配置向导

- [ ] **域名配置**: 
  - 生产环境：已输入实际域名
  - 本地测试：使用 localtest.me
- [ ] **子域名**: 前端和后端子域名已设置
- [ ] **管理员邮箱**: 已输入有效邮箱
- [ ] **ACME 邮箱**（生产）: Let's Encrypt 证书邮箱已设置
- [ ] **数据库路径**: PostgreSQL 数据目录已确认
- [ ] **CORS 配置**: JSON 列表格式正确

### Docker 构建与启动

- [ ] **镜像拉取**: traefik、postgres 镜像拉取成功
- [ ] **镜像构建**: backend、frontend 镜像构建成功
- [ ] **容器启动**: 所有容器启动成功
- [ ] **健康检查**: 
  - [ ] traefik: 健康
  - [ ] db: 健康
  - [ ] backend: 健康
  - [ ] frontend: 健康（依赖 backend）
- [ ] **数据库迁移**: Alembic 迁移执行成功

---

## ✅ 部署后验证清单

### 1. 容器状态检查

```bash
capdf status
```

预期输出：所有容器状态为 `Up` 或 `running`

- [ ] traefik: Up
- [ ] db: Up (healthy)
- [ ] backend: Up (healthy)
- [ ] frontend: Up

### 2. 健康检查

```bash
capdf doctor
```

检查项：
- [ ] 操作系统检查通过
- [ ] Docker 环境正常
- [ ] 系统资源充足
- [ ] 网络连接正常
- [ ] DNS 解析正常
- [ ] 端口未被占用
- [ ] 配置文件语法正确
- [ ] 项目结构完整
- [ ] 数据库连接正常
- [ ] 后端 API 健康检查通过

### 3. 前端访问测试

```bash
# 本地测试（自签证书，使用 -k 忽略证书警告）
curl -k https://app.localtest.me

# 生产环境
curl https://app.yourdomain.com
```

- [ ] HTTP 返回 200 或重定向到 HTTPS
- [ ] HTTPS 返回 HTML 内容
- [ ] 浏览器可以打开前端页面

### 4. 后端 API 测试

```bash
# 健康检查端点
curl -k https://api.localtest.me/health

# API 文档
curl -k https://api.localtest.me/docs
```

- [ ] `/health` 返回 `{"status":"healthy"}` 或类似
- [ ] `/docs` 返回 Swagger UI HTML

### 5. 证书检查

**本地测试（自签证书）**:
```bash
openssl s_client -connect app.localtest.me:443 -servername app.localtest.me < /dev/null 2>&1 | grep "Verify return code"
```
- [ ] 证书存在（自签证书，验证码 18 或 21 正常）

**生产环境（Let's Encrypt）**:
```bash
openssl s_client -connect app.yourdomain.com:443 -servername app.yourdomain.com < /dev/null 2>&1 | grep "Verify return code"
```
- [ ] 证书有效（验证码 0 = ok）

### 6. 数据库连接测试

```bash
capdf logs db | tail -20
```

- [ ] 无错误消息
- [ ] 显示 "database system is ready to accept connections"

### 7. 日志检查

```bash
# 查看所有服务日志
capdf logs | tail -50

# 查看特定服务日志
capdf logs backend | tail -20
capdf logs frontend | tail -20
```

- [ ] 无严重错误（ERROR/FATAL）
- [ ] 后端 uvicorn 启动日志正常
- [ ] 前端 nginx 启动日志正常

### 8. 功能测试

**访问前端**:
- [ ] 登录页面正常显示
- [ ] 可以注册新用户（如果开放注册）
- [ ] 使用默认管理员账号登录成功

**管理员账号**（安装完成时显示）:
- 邮箱：（见安装输出）
- 密码：（见安装输出或 .env 文件）

**基础操作**:
- [ ] 创建根 CA 证书
- [ ] 签发用户证书
- [ ] 上传 PDF 文件
- [ ] 签署 PDF 文件
- [ ] 下载已签署 PDF

---

## 🔧 故障排查清单

### 安装失败

#### 网络连接问题

**症状**: 无法连接到 GitHub 或 Docker Hub

**排查步骤**:
1. [ ] 测试基础网络：`ping 8.8.8.8`
2. [ ] 测试 DNS：`nslookup github.com`
3. [ ] 测试 GitHub：`curl -I https://github.com`
4. [ ] 检查代理配置：`echo $https_proxy`
5. [ ] 配置代理（如需要）：`export https_proxy=http://proxy:port`

**解决方案**:
```bash
# 配置代理后重试
export https_proxy=http://your-proxy:port
bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
```

#### Docker 安装失败

**症状**: Docker 安装报错

**排查步骤**:
1. [ ] 检查系统支持：`cat /etc/os-release`
2. [ ] 手动安装 Docker：访问 https://docs.docker.com/engine/install/
3. [ ] 验证安装：`docker --version`
4. [ ] 启动 Docker：`sudo systemctl start docker`
5. [ ] 设置开机自启：`sudo systemctl enable docker`

**解决方案**:
```bash
# 手动安装 Docker 后重新运行
CAPDF_SKIP_INSTALL=1 bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)
capdf install
```

#### 端口被占用

**症状**: 80/443 端口已被占用

**排查步骤**:
1. [ ] 查看占用进程：`sudo ss -tlnp | grep ':80\|:443'`
2. [ ] 停止占用服务（如 Apache/Nginx）：
   ```bash
   sudo systemctl stop apache2  # Ubuntu/Debian
   sudo systemctl stop httpd    # CentOS/RHEL
   sudo systemctl stop nginx
   ```
3. [ ] 或修改 ca-pdf 端口（在 .env.docker 中）

#### 磁盘空间不足

**症状**: 构建镜像时失败

**排查步骤**:
1. [ ] 检查磁盘空间：`df -h`
2. [ ] 清理 Docker：
   ```bash
   docker system prune -a --volumes
   ```
3. [ ] 扩展磁盘或挂载新磁盘

### 容器启动失败

#### 数据库容器无法启动

**排查步骤**:
1. [ ] 查看日志：`capdf logs db`
2. [ ] 检查数据目录权限：`ls -la /opt/ca-pdf/data/postgres/`
3. [ ] 检查磁盘空间：`df -h`
4. [ ] 清理并重启：
   ```bash
   capdf down
   sudo rm -rf /opt/ca-pdf/data/postgres/
   capdf up
   ```

#### 后端容器无法启动

**排查步骤**:
1. [ ] 查看日志：`capdf logs backend`
2. [ ] 检查环境变量：`cat /opt/ca-pdf/.env | grep -v PASSWORD`
3. [ ] 检查数据库连接：
   ```bash
   capdf logs backend | grep "database"
   ```
4. [ ] 重建镜像：
   ```bash
   capdf down
   docker rmi ca_pdf-backend
   capdf up
   ```

#### 前端容器无法启动

**排查步骤**:
1. [ ] 查看日志：`capdf logs frontend`
2. [ ] 检查后端依赖：`capdf logs backend | tail -20`
3. [ ] 确认后端健康：`curl -k https://api.localtest.me/health`
4. [ ] 重建镜像：
   ```bash
   capdf down
   docker rmi ca_pdf-frontend
   capdf up
   ```

### 访问问题

#### 浏览器无法访问

**症状**: ERR_CONNECTION_REFUSED 或超时

**排查步骤**:
1. [ ] 检查容器状态：`capdf status`
2. [ ] 检查端口监听：`sudo ss -tlnp | grep ':80\|:443'`
3. [ ] 检查防火墙：
   ```bash
   sudo ufw status
   # 或
   sudo iptables -L
   ```
4. [ ] 检查域名解析（生产环境）：`nslookup app.yourdomain.com`

**解决方案**:
```bash
# 本地测试
echo "127.0.0.1 app.localtest.me api.localtest.me" | sudo tee -a /etc/hosts

# 防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

#### 证书错误

**症状**: 浏览器显示证书不安全

**本地测试**:
- 正常现象（自签证书），点击"高级" → "继续访问"

**生产环境**:
1. [ ] 检查 Traefik 日志：`capdf logs traefik | grep -i acme`
2. [ ] 确认域名 DNS 解析正确
3. [ ] 确认 80 端口可从外网访问（ACME HTTP Challenge）
4. [ ] 等待证书申请完成（可能需要几分钟）
5. [ ] 强制重新申请：
   ```bash
   capdf down
   sudo rm -rf /opt/ca-pdf/data/traefik/acme.json
   capdf up
   ```

---

## 📊 部署成功指标

所有以下指标应为"通过"：

- ✅ **容器运行**: 所有 4 个容器状态为 Up
- ✅ **健康检查**: `capdf doctor` 无错误
- ✅ **前端可访问**: HTTP 200 响应
- ✅ **后端可访问**: `/health` 返回健康状态
- ✅ **API 文档**: `/docs` 正常显示
- ✅ **数据库连接**: 后端日志无数据库错误
- ✅ **管理员登录**: 可以使用默认账号登录
- ✅ **基础功能**: 可以创建 CA、签发证书、签署 PDF

---

## 🎯 快速诊断命令

```bash
# 一键诊断
capdf doctor

# 导出完整日志（用于技术支持）
capdf export-logs

# 查看容器状态
capdf status

# 查看最近日志
capdf logs | tail -100

# 重启服务
capdf restart

# 查看环境配置（脱敏）
cat /opt/ca-pdf/.env | grep -v -E "PASSWORD|SECRET|KEY"
```

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. **导出诊断日志**：
   ```bash
   capdf export-logs
   ```

2. **提交 Issue**：
   - 访问：https://github.com/QAQ-AWA/ca-pdf/issues
   - 附上诊断日志文件

3. **发送邮件**：
   - 邮箱：7780102@qq.com
   - 主题：[ca-pdf部署问题] 简短描述
   - 内容：包含系统信息和诊断日志

---

**文档版本**: v2.0  
**最后更新**: 2024  
**适用版本**: ca-pdf v0.1.0+
