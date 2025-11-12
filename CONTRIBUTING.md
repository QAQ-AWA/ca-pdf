# 贡献指南 (CONTRIBUTING)
> 📖 **文档导航**：[README](./README.md) · [文档索引](./DOCUMENTATION.md) · [开发指南](./DEVELOPMENT.md) · [安全指南](./SECURITY.md) · [更新日志](./CHANGELOG.md)
> 🎯 **适用人群**：贡献者 / 开发者
> ⏱️ **预计阅读时间**：35 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本文阐述贡献流程、代码规范与审核要求。在开始之前，请先了解项目概览 [README.md](./README.md)，开发细节参阅 [DEVELOPMENT.md](./DEVELOPMENT.md)，安全考量见 [SECURITY.md](./SECURITY.md)，版本发布历史可查看 [CHANGELOG.md](./CHANGELOG.md)。

---

感谢您对 ca-pdf 项目的关注！我们欢迎所有形式的贡献，包括代码、文档、测试和反馈。

## 🎯 欢迎贡献者

ca-pdf 是一个开源的自托管 PDF 电子签章平台，我们相信开源社区的力量可以让这个项目变得更好。无论您是经验丰富的开发者还是初学者，都可以为项目做出有意义的贡献。

### 贡献的方式

- **代码贡献**：修复 Bug、实现新功能、性能优化等
- **文档贡献**：改进 README、API 文档、部署指南、使用教程等
- **测试贡献**：编写单元测试、集成测试、改进测试覆盖率等
- **反馈贡献**：提交 Issue、建议改进、参与讨论等

### 行为准则

我们致力于营造一个包容、尊重的社区环境。请遵守以下原则：

- **尊重**：尊重所有贡献者和社区成员的想法和意见
- **包容**：欢迎不同背景、经验水平和观点的人参与
- **建设性**：以积极、建设性的方式进行讨论和反馈
- **专业**：保持专业的沟通态度，避免人身攻击或不适当的语言

---

## 🔄 开发工作流程

### 1. Fork 仓库

访问 [ca-pdf 仓库](https://github.com/QAQ-AWA/ca-pdf)，点击右上角的 "Fork" 按钮将仓库 Fork 到您的 GitHub 账户。

### 2. Clone 本地仓库

```bash
git clone https://github.com/<your-username>/ca-pdf.git
cd ca-pdf
```

### 3. 创建功能分支

从 `main` 分支创建新的功能分支：

```bash
git fetch origin
git checkout -b feature/xxx origin/main
```

分支命名规范：
- `feature/xxx`：新功能
- `fix/xxx`：Bug 修复
- `docs/xxx`：文档更新
- `refactor/xxx`：代码重构
- `perf/xxx`：性能优化

### 4. 开发环境设置

#### Python 环境

```bash
# 安装依赖
make install

# 或手动安装
cd backend
poetry install
```

#### Node.js 环境

```bash
cd frontend
npm install
```

#### 数据库设置

```bash
# 使用 SQLite (开发推荐)
export DATABASE_URL="sqlite:///./test.db"

# 或使用 PostgreSQL
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/ca_pdf_dev"
```

#### 环境变量配置

- 复制 `.env.example` → `.env`（如使用 Docker 亦需复制 `.env.docker.example`）。
- 所有变量的说明、默认值与安全要求集中在 [DEPLOYMENT.md](./DEPLOYMENT.md) 的“环境变量清单”章节。
- 在贡献前请确认密钥通过 `openssl rand -base64 32` 生成，`BACKEND_CORS_ORIGINS` 维持 JSON 列表格式。

### 5. 代码开发

遵循项目的代码风格和规范（见下文）进行开发。

### 6. 本地测试

运行后端测试：

```bash
cd backend
poetry run pytest
```

运行前端测试：

```bash
cd frontend
npm run test
```

确保所有测试通过且代码格式符合要求。

### 7. 提交代码

遵循 Conventional Commits 规范提交：

```bash
git add .
git commit -m "type(scope): subject"
```

### 8. 创建 Pull Request

将您的分支推送到 Fork 的仓库：

```bash
git push origin feature/xxx
```

然后访问 [ca-pdf 仓库](https://github.com/QAQ-AWA/ca-pdf)，GitHub 会提示您创建 Pull Request，完填写 PR 描述并提交。

---

## 📋 代码质量要求

### Python 后端代码规范

#### 代码格式

使用 Black 进行代码格式化：

```bash
cd backend
poetry run black app tests
```

验证格式是否正确：

```bash
poetry run black --check app tests
```

#### 导入排序

使用 isort 排序 Python 导入：

```bash
poetry run isort app tests
```

验证导入顺序是否正确：

```bash
poetry run isort --check-only app tests
```

#### 类型检查

使用 mypy 进行类型检查（严格模式）：

```bash
poetry run mypy app
```

所有代码必须通过 mypy 的严格类型检查。

#### 代码风格指南

- 类名采用 PascalCase：`class UserModel`
- 函数名和变量名采用 snake_case：`def get_user_by_id()`
- 常量采用 UPPER_SNAKE_CASE：`MAX_FILE_SIZE = 10485760`
- 使用类型注解，例如：`def create_user(name: str) -> User:`
- 优先使用 async/await 处理异步操作
- 使用 Pydantic 进行数据验证和序列化

### 前端代码规范

#### ESLint

运行 ESLint 检查：

```bash
cd frontend
npm run lint
```

自动修复问题：

```bash
npm run lint -- --fix
```

#### Prettier

使用 Prettier 进行代码格式化：

```bash
npm run format
```

#### TypeScript

- 启用严格模式：`"strict": true`
- 为所有函数参数和返回值添加类型注解
- 避免使用 `any` 类型
- 使用接口定义数据结构

### 测试覆盖率

- 新功能必须包含单元测试
- **测试覆盖率要求 >= 80%**
- 所有关键路径必须被测试覆盖

---

## 🧪 测试要求

### 后端测试

#### 测试框架

使用 pytest 进行单元测试和集成测试。

#### 编写测试

```bash
# 运行全量测试
cd backend
poetry run pytest

# 运行特定测试文件
poetry run pytest tests/test_auth.py

# 显示覆盖率报告
poetry run pytest --cov=app --cov-report=html
```

#### 测试命名规范

- 测试文件：`test_*.py` 或 `*_test.py`
- 测试类：`Test*`
- 测试方法：`test_*`

示例：

```python
class TestUserService:
    async def test_create_user_success(self):
        # Arrange
        user_data = {"name": "John", "email": "john@example.com"}
        
        # Act
        user = await user_service.create_user(user_data)
        
        # Assert
        assert user.name == "John"
        assert user.email == "john@example.com"
    
    async def test_create_user_duplicate_email(self):
        # ...
```

#### 最佳实践

- 使用 Arrange-Act-Assert (AAA) 模式
- 一个测试只验证一个行为
- 使用有意义的测试名称，清晰表达测试意图
- 使用 fixtures 进行测试数据准备
- 使用 mock 和 patch 隔离依赖
- 避免在测试中硬编码数据

### 前端测试

```bash
cd frontend
npm run test
npm run test:coverage
```

---

## 📝 提交信息规范 (Conventional Commits)

遵循 Conventional Commits 规范编写清晰、规范的提交信息。

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|-----|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式，不改变功能（如空格、分号、缩进等） |
| `refactor` | 代码重构，不改变功能 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建、依赖、工具、CI 等 |

### Scope 范围

可选，表示影响的范围，例如：

- `auth`：认证相关
- `user`：用户管理
- `pdf`：PDF 处理
- `cert`：证书管理
- `seal`：企业印章
- `api`：API 接口
- `ui`：用户界面

### Subject 主题

- 使用命令式语气，"add" 而不是 "added" 或 "adds"
- 不要大写首字母
- 不要以句号结尾
- 限制在 50 字符以内

### Body 正文

- 说明代码更改的原因和内容
- 每行 72 字符换行
- 说明改了什么和为什么改，但不需要说明如何改（代码已说明）

### Footer 页脚

- 参考相关 Issue：`Closes #123`、`Fixes #456`
- 标记 Breaking Changes：`BREAKING CHANGE: ...`

### 提交信息示例

```
feat(seal): add seal management API endpoints

- Implement POST /seals for uploading seals
- Implement GET /seals for listing user seals
- Implement DELETE /seals/{id} for deleting seals
- Add comprehensive unit tests for seal operations
- Update API documentation with seal endpoints

Closes #123
```

```
fix(auth): correct token expiration calculation

The refresh token expiration was calculated incorrectly,
using minutes instead of days. This fix ensures tokens
expire after the configured duration.

Fixes #456
```

---

## 🔀 Pull Request 流程

### PR 标题

- 清晰简洁
- 遵循 Conventional Commits 格式
- 示例：`feat(seal): add seal management API endpoints`

### PR 描述

使用 PR 模板（如果有）填写以下信息：

```markdown
## 描述

简要说明这个 PR 的目的和改动。

## 改动内容

- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 代码重构

## 改动详情

- 具体改了什么
- 为什么要改
- 有什么影响

## 测试方法

说明如何测试这个改动：

1. 步骤 1
2. 步骤 2
3. ...

## 测试截图/演示

（如适用）

## 相关 Issue

Closes #123

## 检查清单

- [ ] 代码格式化通过（Black、isort）
- [ ] 类型检查通过（mypy）
- [ ] 所有测试通过
- [ ] 测试覆盖率 >= 80%
- [ ] 文档已更新
- [ ] 提交信息符合规范
```

### PR 审查

- 等待 CI 通过
- 等待至少一名维护者进行代码审查
- 根据审查意见进行修改
- 所有评论必须解决才能合并

### 合并标准

- ✅ CI 全部通过
- ✅ 至少一名维护者批准
- ✅ 没有未解决的对话
- ✅ 分支与 main 分支最新
- ✅ 测试覆盖率达要求

---

## ✅ CI/CD 检查清单

PR 提交后，GitHub Actions 会自动运行以下检查：

- [ ] **Black 格式检查** - 代码格式
- [ ] **isort 导入检查** - 导入排序
- [ ] **mypy 类型检查** - 类型安全
- [ ] **ESLint** - 前端代码规范
- [ ] **Prettier** - 代码格式化
- [ ] **后端单元测试** - pytest
- [ ] **前端单元测试** - npm test
- [ ] **代码覆盖率** - >= 80%

所有检查必须通过才能合并 PR。

---

## 📄 文档贡献

### 文档格式

所有文档使用 Markdown 格式，文件名使用大写字母，例如：

- `README.md`
- `API.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

### 文档规范

- 使用清晰的标题结构（# ## ###）
- 使用代码块展示代码示例
- 使用列表组织信息
- 使用表格展示对比信息
- 包含目录（TOC）如需要
- 使用相对链接引用其他文档

### 代码示例

在文档中包含清晰的代码示例：

```python
# Python 示例
def example():
    pass
```

```bash
# Bash 示例
echo "Hello"
```

```typescript
// TypeScript 示例
function example() {}
```

### 中英文文档

- 主要文档优先使用中文
- 如有英文版本需求，应同时维护英文版本
- 保持中英文文档内容一致

---

## 🐛 Issue 报告

### Bug 报告

如果发现 Bug，请创建 Issue 并包含以下信息：

```markdown
## 描述

清晰描述 Bug 的现象。

## 复现步骤

1. 步骤 1
2. 步骤 2
3. ...

## 期望行为

应该发生什么

## 实际行为

实际发生了什么

## 环境信息

- OS：Windows 10 / macOS 12 / Ubuntu 22.04
- Python 版本：3.11
- Node.js 版本：18
- Docker 版本：23
- 浏览器：Chrome 120

## 错误日志

```
粘贴相关日志...
```

## 附加信息

任何其他相关信息，如截图等。
```

### 功能请求

对于功能请求，请包含：

```markdown
## 功能描述

这个新功能应该做什么？

## 使用场景

什么时候会用到这个功能？

## 建议实现

（可选）您对实现方式有什么建议吗？

## 参考

相关链接或参考资料。
```

---

## 💻 开发环境需求

### 系统要求

- **操作系统**：Linux、macOS 或 Windows（WSL2 推荐）
- **Git**：2.37+

### 编程语言

- **Python**：3.11 或更高
- **Node.js**：18 或更高（LTS 版本推荐）

### 数据库

- **SQLite**：用于本地开发（无需额外安装）
- **PostgreSQL**：12+ （生产推荐）

### 其他工具

- **Docker**：23+（可选，用于容器化开发）
- **Docker Compose**：V2（可选）
- **Poetry**：用于 Python 依赖管理
- **make**：项目自动化工具

### IDE 推荐

- **VS Code**：安装 Python、Pylance、ESLint、Prettier 扩展
- **PyCharm Professional**：完整的 Python IDE 支持
- **WebStorm**：前端开发推荐

---

## 📚 常见贡献场景

### 场景 1：修复一个 Bug

#### 步骤

1. **创建 Issue 描述 Bug**
   - 检查是否已存在相同 Issue
   - 提供清晰的复现步骤
   - 包含错误日志和截图

2. **从 main 创建分支**
   ```bash
   git fetch origin
   git checkout -b fix/bug-description origin/main
   ```
   
3. **定位和修复问题**
   - 查看错误日志了解根本原因
   - 添加注释解释修复方案
   - 确保修复不引入新问题

4. **编写测试用例验证修复**
   ```python
   def test_bug_fix():
       # 重现问题
       # 验证修复
       pass
   ```

5. **本地运行完整测试**
   ```bash
   cd backend && poetry run pytest
   cd ../frontend && npm run test
   ```

6. **代码格式化和类型检查**
   ```bash
   poetry run black app tests
   poetry run isort app tests
   poetry run mypy app
   ```

7. **提交 PR**
   - 标题：`fix(scope): 修复的问题简述`
   - 描述：说明问题、原因、解决方案
   - 关联 Issue：`Fixes #123`

### 场景 2：实现一个新功能

#### 步骤

1. **创建 Issue 讨论新功能**
   - 描述功能需求
   - 说明使用场景
   - 征询维护者意见

2. **从 main 创建分支**
   ```bash
   git fetch origin
   git checkout -b feature/feature-name origin/main
   ```

3. **实现功能**
   - 创建新模块/文件
   - 遵循现有代码风格
   - 添加必要的注释
   - 处理错误和边界情况

4. **编写单元测试**
   - 测试覆盖率 >= 80%
   - 覆盖正常场景和错误场景
   - 使用有意义的测试名称

5. **更新文档**
   - 更新 API.md 文档
   - 更新 README 或相关指南
   - 添加使用示例

6. **本地测试**
   ```bash
   poetry run pytest --cov=app --cov-report=term
   ```

7. **提交 PR**
   - 标题：`feat(scope): 功能名称`
   - 详细描述实现内容和设计考虑

### 场景 3：改进文档

#### 步骤

1. **从 main 创建分支**
   ```bash
   git checkout -b docs/improvement-name origin/main
   ```

2. **编辑文档**
   - 检查语法和拼写
   - 确保示例正确运行
   - 保持风格一致
   - 更新目录（如需要）

3. **验证 Markdown 格式**
   ```bash
   # 使用在线工具或编辑器验证
   # 检查代码块、链接、列表等格式
   ```

4. **提交 PR**
   - 标题：`docs: 文档改进简述`
   - 说明改进内容

#### 文档改进建议

- 修复错别字和语法错误
- 补充缺失的信息
- 改进示例代码
- 更新过时内容
- 改进结构和可读性

### 场景 4：优化性能

#### 步骤

1. **识别性能瓶颈**
   - 使用性能分析工具
   - 运行基准测试
   - 记录当前指标

2. **创建 Issue 描述问题**
   - 说明当前性能
   - 提出优化目标
   - 估计影响范围

3. **从 main 创建分支**
   ```bash
   git checkout -b perf/optimization-name origin/main
   ```

4. **实现优化**
   - 修改算法或数据结构
   - 减少数据库查询
   - 优化网络传输
   - 添加缓存

5. **添加基准测试**
   ```python
   import timeit
   
   def test_performance():
       result = timeit.timeit(
           'function_to_test()',
           number=10000
       )
       assert result < 0.1  # 性能目标
   ```

6. **验证改进**
   - 对比优化前后指标
   - 确保不影响功能正确性
   - 检查是否引入新的性能问题

7. **提交 PR**
   - 标题：`perf(scope): 优化简述`
   - 包含性能对比数据

---

## 📞 联系和问题

### 讨论渠道

- **GitHub Issues**：报告 Bug 或讨论功能
- **GitHub Discussions**（如果启用）：一般讨论和提问
- **Email**：联系维护者

### 维护者列表

| 名称 | GitHub | 职责 |
|-----|--------|------|
| QAQ-AWA | [@QAQ-AWA](https://github.com/QAQ-AWA) | 项目创始人、核心维护者 |

### 问题反馈

- 使用 GitHub Issues 报告问题
- 使用 GitHub Discussions 提问和讨论
- 发送 Email 联系维护者

---

## 许可证

通过提交 Pull Request，您同意您的贡献将在与项目相同的许可证下发布。

---

感谢您对 ca-pdf 项目的贡献！如有任何问题，欢迎通过 GitHub Issues 或 Discussions 联系我们。
---

🔗 **相关文档**
- [开发指南](./DEVELOPMENT.md)
- [安全指南](./SECURITY.md)
- [更新日志](./CHANGELOG.md)
- [文档索引](./DOCUMENTATION.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

