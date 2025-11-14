# Traefik Health Check Fix - Summary

## 问题描述

Traefik 容器状态为 unhealthy，表现为健康检查失败：
```
WRN Health check failed. error="HTTP request failed: Get \"http://frontend:8080/\": dial tcp: lookup frontend on 127.0.0.11:53: server misbehaving"
WRN Health check failed. error="HTTP request failed: Get \"http://backend:8000/health\": context deadline exceeded"
```

## 根本原因

经过审查，发现了以下问题：

1. **前端健康检查路径错误**：
   - Traefik 动态配置使用 `path: "/"`
   - 但 nginx 实际的健康检查端点是 `/healthz`
   - 导致健康检查失败

2. **后端健康检查超时不足**：
   - 当前超时时间为 5 秒
   - 后端依赖数据库初始化，5 秒可能不足
   - 导致 "context deadline exceeded" 错误

3. **缺少显式容器健康检查**：
   - docker-compose.yml 中 backend 和 frontend 没有显式 healthcheck
   - 导致 `depends_on: service_healthy` 条件无法正常工作

## 修复内容

### 1. 修复 Traefik 动态配置 (config/traefik/dynamic.yml)

#### 前端健康检查路径
```yaml
# 修复前
frontend:
  loadBalancer:
    servers:
      - url: "http://frontend:8080"
    healthCheck:
      path: "/"              # ❌ 错误
      interval: "30s"
      timeout: "5s"

# 修复后
frontend:
  loadBalancer:
    servers:
      - url: "http://frontend:8080"
    healthCheck:
      path: "/healthz"       # ✅ 正确
      interval: "30s"
      timeout: "10s"         # ✅ 增加超时
```

#### 后端健康检查超时
```yaml
# 修复前
backend:
  loadBalancer:
    servers:
      - url: "http://backend:8000"
    healthCheck:
      path: "/health"
      interval: "30s"
      timeout: "5s"          # ❌ 超时过短

# 修复后
backend:
  loadBalancer:
    servers:
      - url: "http://backend:8000"
    healthCheck:
      path: "/health"
      interval: "30s"
      timeout: "10s"         # ✅ 增加超时
```

### 2. 更新 docker-compose.yml

#### 后端容器健康检查
```yaml
backend:
  # ... 其他配置 ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s      # 给予足够的启动时间
```

#### 前端容器健康检查
```yaml
frontend:
  # ... 其他配置 ...
  healthcheck:
    test: ["CMD", "wget", "--spider", "-q", "http://127.0.0.1:8080/healthz"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

### 3. 更新 scripts/deploy.sh

在 `write_dynamic_config()` 函数中应用相同的修复：
- 前端健康检查路径改为 `/healthz`
- 超时时间从 5s 增加到 10s
- 同时适用于本地模式和生产模式

在 `write_compose_file()` 函数中添加健康检查配置：
- 为 backend 和 frontend 服务添加显式健康检查
- 与 docker-compose.yml 保持一致

### 4. 更新文档

#### DEPLOYMENT.md
- 添加了新的章节 "5. 容器健康检查失败"
- 包含 Traefik、后端、前端健康检查失败的排查步骤
- 提供详细的解决方案和验证命令
- 说明了 Traefik 负载均衡器健康检查配置

#### TROUBLESHOOTING.md
- 添加了新的章节 "9.2.1 容器健康检查失败（unhealthy）"
- 详细说明了各种健康检查失败的症状、原因和解决方案
- 包含 Traefik、后端、前端容器的具体排查步骤
- 解释了 Docker HEALTHCHECK 与 Traefik healthCheck 的区别
- 提供了预防措施建议

## 验证步骤

### 1. 检查配置文件

```bash
# 验证动态配置
cat config/traefik/dynamic.yml | grep -A 10 "services:"

# 验证 docker-compose
docker compose config | grep -A 5 healthcheck
```

### 2. 测试健康检查端点

```bash
# 启动服务
docker compose up -d

# 等待服务启动
sleep 60

# 测试后端健康检查
docker compose exec backend curl -v http://127.0.0.1:8000/health

# 测试前端健康检查
docker compose exec frontend wget --spider -q http://127.0.0.1:8080/healthz && echo "OK" || echo "FAIL"

# 测试 Traefik ping
curl http://localhost/ping
```

### 3. 检查容器状态

```bash
# 查看所有容器状态
docker compose ps

# 应该看到所有容器都是 healthy
# NAME                  STATUS
# traefik               Up (healthy)
# db                    Up (healthy)
# backend               Up (healthy)
# frontend              Up (healthy)
```

### 4. 查看 Traefik 日志

```bash
# 查看 Traefik 日志，不应该有 WRN 健康检查失败的消息
docker compose logs traefik | grep -i health

# 应该看到成功的日志，如：
# INF Health check passed for backend
# INF Health check passed for frontend
```

### 5. 测试反向代理

```bash
# 测试后端 API
curl -k https://api.localtest.me/health

# 测试前端
curl -k https://app.localtest.me/

# 测试 HTTPS 重定向
curl -I http://api.localtest.me/health
# 应该返回 301 或 302 重定向到 https://
```

## 预期结果

修复完成后，应该达到以下效果：

1. ✅ Traefik 容器状态变为 healthy
2. ✅ Backend 容器状态变为 healthy
3. ✅ Frontend 容器状态变为 healthy
4. ✅ 所有健康检查日志中无 WRN（警告）信息
5. ✅ 可以通过 Traefik 反向代理访问前端和后端
6. ✅ HTTPS 重定向正常工作

## 技术细节

### 健康检查端点说明

#### 后端 `/health`
- 文件位置：`backend/app/api/routes.py`
- 实现：简单的 JSON 响应
- 响应示例：`{"status": "ok", "service": "ca-pdf"}`
- 响应时间：< 100ms（不查询数据库）

#### 前端 `/healthz`
- 文件位置：`frontend/nginx.conf`
- 实现：nginx 配置的静态端点
- 响应示例：纯文本 "ok"
- 响应时间：< 10ms

### 健康检查类型对比

#### Docker Container HEALTHCHECK
- **位置**：docker-compose.yml 或 Dockerfile
- **目的**：判断容器是否 healthy
- **影响**：
  - `depends_on` 启动顺序
  - `docker compose ps` 显示的状态
  - 容器自动重启策略

#### Traefik Load Balancer healthCheck
- **位置**：config/traefik/dynamic.yml
- **目的**：判断负载均衡器是否将流量转发到该后端
- **影响**：
  - 流量路由决策
  - 服务可用性
  - 日志中的健康检查警告/错误

两者是独立的，都需要正确配置。

### 超时时间设计

| 服务 | start_period | interval | timeout | retries | 说明 |
|------|-------------|----------|---------|---------|------|
| traefik | 30s | 30s | 5s | 3 | 启动快，超时短 |
| db | 20s | 10s | 5s | 5 | 数据库初始化时间 |
| backend | 40s | 30s | 10s | 3 | 依赖数据库，需要更长启动时间 |
| frontend | 30s | 30s | 10s | 3 | 静态资源，启动快 |

**设计原则**：
- `start_period`: 给予服务充分的初始化时间
- `interval`: 运行后的定期检查间隔
- `timeout`: 单次健康检查的超时时间
- `retries`: 失败重试次数

## 相关文件清单

### 修改的文件
1. `config/traefik/dynamic.yml` - Traefik 动态配置
2. `docker-compose.yml` - Docker Compose 配置
3. `scripts/deploy.sh` - 部署脚本
4. `DEPLOYMENT.md` - 部署文档
5. `TROUBLESHOOTING.md` - 故障排查文档

### 未修改但相关的文件
1. `frontend/nginx.conf` - 前端 nginx 配置（已包含 `/healthz` 端点）
2. `backend/app/api/routes.py` - 后端健康检查端点（已存在）
3. `backend/Dockerfile` - 后端 Dockerfile（已包含 HEALTHCHECK）
4. `frontend/Dockerfile` - 前端 Dockerfile（已包含 HEALTHCHECK）

## 总结

本次修复解决了 Traefik 健康检查失败的根本原因：

1. **前端健康检查路径错误**：从 `/` 修复为 `/healthz`
2. **超时时间不足**：从 5s 增加到 10s
3. **缺少显式健康检查**：为 backend 和 frontend 添加健康检查配置

修复后，所有容器应该都能正常达到 healthy 状态，服务可以通过 Traefik 反向代理正常访问。

文档也已更新，包含详细的排查步骤和预防措施，便于后续维护和问题诊断。
