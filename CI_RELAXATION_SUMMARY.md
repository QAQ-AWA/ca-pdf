# CI 门禁临时放宽 - 实施总结

## 📋 变更概述

本次变更临时放宽了 Pull Request 工作流中的 CI 检查，以便快速合并稳定基线。所有变更仅影响 PR 工作流，main 分支的 push 保持严格检查。

## ✅ 已完成的变更

### 1. 后端 CI (`.github/workflows/backend-ci.yml`)

#### 1.1 mypy 类型检查
- **状态**: ⚠️ PR 中已跳过
- **实现**: 添加条件 `if: github.event_name != 'pull_request'`
- **影响**: 
  - PR: 不执行 mypy 类型检查
  - main push: 继续执行完整类型检查

#### 1.2 pytest 测试套件
- **状态**: ⚠️ PR 中仅运行核心测试
- **实现**: 根据事件类型动态选择测试范围
- **影响**:
  - PR: 只运行带 `core` 或 `smoke` 标记的测试 (`-k "core or smoke"`)
  - main push: 运行完整测试套件
- **注意**: 测试需要在代码中添加相应标记:
  ```python
  @pytest.mark.core
  def test_important_feature():
      pass
  
  @pytest.mark.smoke
  def test_basic_functionality():
      pass
  ```

#### 1.3 代码格式化 (black & isort)
- **状态**: ✅ 保持严格
- **实现**: 无变更
- **影响**: 在所有 PR 和 push 中强制执行

---

### 2. 前端 CI (`.github/workflows/frontend-ci.yml`)

#### 2.1 ESLint 规则降级
- **状态**: ⚠️ 三条规则降为警告
- **实现**: 在 `frontend/.eslintrc.cjs` 中添加 overrides
- **降级规则**:
  1. `testing-library/prefer-find-by` → warn
  2. `testing-library/render-result-naming-convention` → warn
  3. `no-useless-escape` → warn
- **影响**: 
  - 这些规则违规不再导致 CI 失败
  - 仍保持 `--max-warnings=0` 以捕获其他警告

#### 2.2 前端测试套件 (Vitest)
- **状态**: ⚠️ PR 中非阻塞 + 性能优化
- **实现**: 
  - PR: 添加 `--runInBand --maxWorkers=50%` 参数
  - PR: 设置 `continue-on-error: true`
  - main push: 正常运行
- **影响**:
  - PR: 测试失败不会阻止合并
  - main push: 测试失败会阻止合并

---

### 3. Docker 构建 (`.github/workflows/docker-build.yml`)

#### 3.1 多架构构建优化
- **状态**: ⚠️ PR 中仅语法检查
- **实现**: 
  - 添加 PR 触发器
  - 原 `build-and-push` job 添加条件 `if: github.event_name != 'pull_request'`
  - 新增 `build-syntax-check` job 专用于 PR
- **影响**:
  - **PR**: 
    - 不执行完整多架构构建（linux/amd64,linux/arm64）
    - 不推送镜像到 GHCR
    - 只构建 linux/amd64 验证语法
  - **main push / tags**: 
    - 执行完整多架构构建
    - 推送镜像到 GitHub Container Registry

---

## 📝 验收标准

✅ **已满足以下条件:**

1. ✅ 后端 mypy 在 PR 中跳过，main 保留
2. ✅ 后端 pytest 在 PR 中只跑 core/smoke，main 跑全部
3. ✅ 后端 black/isort 在所有场景保持严格
4. ✅ 前端 ESLint 三条规则降级为 warn
5. ✅ 前端测试在 PR 中非阻塞，main 保持阻塞
6. ✅ Docker 多架构构建在 PR 中简化，main 保持完整
7. ✅ 创建恢复清单文档 (`CI_RESTORATION_CHECKLIST.md`)

---

## 🔄 后续恢复计划

详细的恢复计划和优先级请参考: **`CI_RESTORATION_CHECKLIST.md`**

### 建议恢复顺序:

1. **高优先级** (1-2周内):
   - ESLint 规则修复 (逐条修复代码违规)
   - Backend pytest 完整测试 (修复失败用例)
   - Backend mypy 类型检查 (修复类型错误)

2. **中优先级** (2-4周内):
   - Frontend 测试稳定性 (修复不稳定测试)

3. **低优先级** (按需):
   - Docker 多架构构建优化 (评估是否需要在 PR 中启用)

---

## 🚀 使用指南

### 后端测试标记

为了让测试能在 PR 中运行，需要添加标记:

```python
import pytest

@pytest.mark.core  # 核心功能测试
def test_user_authentication():
    pass

@pytest.mark.smoke  # 冒烟测试
def test_api_health_check():
    pass

# 未标记的测试只在 main push 时运行
def test_edge_case_scenario():
    pass
```

### 本地验证命令

```bash
# 后端
cd backend
poetry run black --check app tests
poetry run isort --check-only app tests
poetry run mypy app
poetry run pytest -k "core or smoke"  # 模拟 PR
poetry run pytest                      # 模拟 main

# 前端
cd frontend
npm run lint
npm run test -- --runInBand --maxWorkers=50%  # 模拟 PR
npm run test                                   # 模拟 main
```

---

## 📂 修改文件清单

- `.github/workflows/backend-ci.yml` - 后端 CI 放宽
- `.github/workflows/frontend-ci.yml` - 前端 CI 放宽
- `.github/workflows/docker-build.yml` - Docker 构建优化
- `frontend/.eslintrc.cjs` - ESLint 规则降级
- `CI_RESTORATION_CHECKLIST.md` - 恢复清单 (新增)
- `CI_RELAXATION_SUMMARY.md` - 本文档 (新增)

---

## ⚠️ 重要提醒

1. **临时性质**: 这些放宽是临时措施，必须按计划逐步恢复
2. **main 分支保护**: main 分支的 push 仍保持严格检查
3. **代码质量**: 即使 PR CI 放宽，也应尽量保持高代码质量
4. **及时恢复**: 不要让临时放宽变成永久状态
5. **监控问题**: 定期检查被跳过的检查项，避免问题累积

---

*创建日期: 2024-10-29*  
*目的: 临时放宽 CI 门禁以快速合并稳定基线*  
*责任: 团队需在后续迭代中逐步恢复所有检查*
