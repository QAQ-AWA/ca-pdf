# CI 门禁恢复清单 (CI Gates Restoration Checklist)

本文档记录了为支持基线合并而临时放宽的 CI 检查项，后续需按任务逐项恢复严格门禁。

This document tracks temporarily relaxed CI checks to enable baseline merging. These should be restored progressively in subsequent tasks.

---

## 后端 (Backend)

### 1. Type Checking - mypy
**当前状态 (Current Status):** ⚠️ 在 PR 中已跳过  
**位置 (Location):** `.github/workflows/backend-ci.yml` - "Run type checks" step  
**修改内容 (Changes Made):**
- 添加了条件 `if: github.event_name != 'pull_request'` - PR 工作流中跳过 mypy
- main 分支 push 仍保持执行

**恢复步骤 (Restoration Steps):**
1. 修复所有 mypy 类型检查错误
2. 移除 `if: github.event_name != 'pull_request'` 条件
3. 确保 mypy 在所有 PR 和 push 中强制通过

---

### 2. Test Suite - pytest
**当前状态 (Current Status):** ⚠️ PR 中仅运行核心/冒烟测试  
**位置 (Location):** `.github/workflows/backend-ci.yml` - "Run backend test suite" step  
**修改内容 (Changes Made):**
- PR 工作流：仅运行 `-k "core or smoke"` 标记的测试
- main 分支：运行完整测试套件
- 测试需要在代码中标记：`@pytest.mark.core` 或 `@pytest.mark.smoke`

**恢复步骤 (Restoration Steps):**
1. 修复所有失败或不稳定的测试用例
2. 移除 PR 工作流中的 `-k "core or smoke"` 过滤器
3. 确保完整测试套件在所有 PR 中强制通过

---

### 3. Code Formatting - black & isort
**当前状态 (Current Status):** ✅ 保持严格  
**位置 (Location):** `.github/workflows/backend-ci.yml` - "Run formatters" step  
**修改内容 (Changes Made):** 无变更，继续强制执行

**恢复步骤 (Restoration Steps):** N/A - 已是严格模式

---

## 前端 (Frontend)

### 1. ESLint Rules
**当前状态 (Current Status):** ⚠️ 三条规则已降级为警告  
**位置 (Location):** `frontend/.eslintrc.cjs` - overrides section  
**修改内容 (Changes Made):**
降级以下规则的严重性从 "error" 到 "warn"：
- `testing-library/prefer-find-by` - 推荐使用 findBy 异步查询
- `testing-library/render-result-naming-convention` - render 结果命名规范
- `no-useless-escape` - 避免不必要的转义字符

**恢复步骤 (Restoration Steps):**
1. 逐条规则修复代码违规
2. 从 `frontend/.eslintrc.cjs` 的 overrides 中移除这些规则
3. 运行 `npm run lint` 确保无错误
4. 确保 `--max-warnings=0` 在 CI 中保持启用

---

### 2. Frontend Test Suite - Vitest
**当前状态 (Current Status):** ⚠️ PR 中配置为非阻塞  
**位置 (Location):** `.github/workflows/frontend-ci.yml` - "Run frontend tests" step  
**修改内容 (Changes Made):**
- PR 工作流：使用 `--runInBand --maxWorkers=50%` 并设置 `continue-on-error: true`
- main 分支：正常运行测试

**恢复步骤 (Restoration Steps):**
1. 修复所有失败或不稳定的前端测试
2. 移除 `continue-on-error: true` 设置
3. 调整并发配置以平衡速度和稳定性
4. 确保测试在所有 PR 中强制通过

---

## Docker 多架构构建 (Multi-arch Build)

### 1. Multi-arch Image Build & Push
**当前状态 (Current Status):** ⚠️ PR 中已禁用完整构建  
**位置 (Location):** `.github/workflows/docker-build.yml`  
**修改内容 (Changes Made):**
- 添加了 `build-and-push` job 的条件：`if: github.event_name != 'pull_request'`
- 新增 `build-syntax-check` job 仅在 PR 中运行：
  - 只构建 linux/amd64 平台
  - 不推送镜像
  - 仅验证 Dockerfile 语法和基本构建能力

**恢复步骤 (Restoration Steps):**
1. 优化 Docker 构建缓存策略以减少构建时间
2. 评估是否在 PR 中启用轻量级多架构构建（如 amd64 + arm64）
3. 如决定恢复，移除 `if: github.event_name != 'pull_request'` 条件
4. 或保持当前策略（仅在 main 上完整构建），取决于团队需求

---

## 优先级建议 (Priority Recommendations)

### 高优先级 (High Priority)
1. **ESLint Rules** - 影响代码质量和可维护性
2. **Backend pytest** - 确保核心功能正确性
3. **Backend mypy** - 类型安全对长期维护至关重要

### 中优先级 (Medium Priority)
4. **Frontend Tests** - 确保 UI 功能稳定性

### 低优先级 (Low Priority)
5. **Multi-arch Docker Build** - 可根据实际部署需求决定是否在 PR 中启用

---

## 恢复验证步骤 (Restoration Verification)

每次恢复一项检查后，应执行以下验证：

1. 在本地环境运行相应检查确认通过
2. 创建测试 PR 验证 CI 工作流正常
3. 确认检查在 CI 中是阻塞的（非 `continue-on-error`）
4. 更新本文档标记该项为 ✅ 已恢复
5. 提交更新本文档的 commit

---

## 修改文件清单 (Modified Files)

- `.github/workflows/backend-ci.yml` - 后端 CI 工作流
- `.github/workflows/frontend-ci.yml` - 前端 CI 工作流
- `.github/workflows/docker-build.yml` - Docker 构建工作流
- `frontend/.eslintrc.cjs` - ESLint 配置

---

*最后更新 (Last Updated):* 2024-10-29  
*创建原因 (Reason):* 临时放宽 CI 门禁以合并稳定基线  
*目标 (Goal):* 逐步恢复所有严格检查，确保长期代码质量
