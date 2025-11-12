# ca-pdf 故障排查指南
> 📖 **文档导航**：[README](./index.md) · [文档索引](./DOCUMENTATION.md) · [部署手册](./DEPLOYMENT.md) · [用户指南](./USER_GUIDE.md) · [API 文档](./API.md)
> 🎯 **适用人群**：所有角色
> ⏱️ **预计阅读时间**：25 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本文整理常见问题与排查步骤。请结合 [DEPLOYMENT.md](./DEPLOYMENT.md) 和 [USER_GUIDE.md](./USER_GUIDE.md) 确认前置条件，接口异常可参考 [API.md](./API.md)。如果对整体流程不熟悉，请先阅读 [README.md](./index.md)。

---

本指南旨在帮助运维工程师、开发团队和技术支持人员在最短时间内定位并解决自托管 PDF 电子签章平台 **ca-pdf** 的常见故障。文档覆盖认证、证书管理、PDF 签章、验签、用户管理、数据库、性能、部署等重点领域，并提供标准化的排查步骤、日志位置、常用命令、预防建议以及性能优化策略。通过统一的排障流程和详尽的场景说明，可显著降低沟通成本，提升问题解决效率。

> **最佳实践**：排障过程中请同步记录所执行的操作、观察到的现象和相关日志，以便后续复盘和经验沉淀。

---

## 1. 快速排查流程图

在开始详细诊断之前，建议先确认问题所属的模块，以便快速定位责任团队和日志来源。以下文本流程图可作为判定的第一步：

```text
ca-pdf 故障排查总览
├── 认证与用户问题
│   ├── 登录失败 / Token 失效
│   └── 权限不足 / 用户操作异常
├── 证书与密钥管理
│   ├── 根 CA / 中间证书生成
│   └── 证书导入与吊销列表
├── PDF 签章与验签
│   ├── 上传、配置、签章
│   └── 验签与时间戳
├── 平台运维
│   ├── 数据库与存储
│   ├── 性能与资源
│   └── 部署与网络
└── 工具与支持
    ├── 日志、监控、调试
    └── 报错码与支持渠道
```

**初步诊断通用步骤**：

1. **确认影响范围**：问题是影响单个用户、某个租户还是全局服务？是否仅限于特定浏览器或终端？
2. **收集基础信息**：记录复现时间、操作用户、操作路径、客户端版本、部署环境（本地 / Docker / Kubernetes）、最近是否有发布或配置变更。
3. **运行健康检查**：访问 `/api/v1/health`，确认后端服务状态码为 200；前端可刷新页面并观察静态资源是否成功加载。
4. **查看核心日志**：`docker-compose logs backend --since 10m` 或本地 `poetry run uvicorn app.main:app --reload` 的终端输出，必要时调高日志级别至 `DEBUG`。
5. **检查依赖服务**：确认 PostgreSQL、Redis、对象存储、TSA、SMTP 等外部依赖运行正常，环境变量未被误改。
6. **比对配置差异**：若问题只发生在某个环境，请比对 `.env`、反向代理配置、域名证书等差异。
7. **根据分类树进入对应章节**，按步骤逐项排查。若涉及多个模块，可交叉引用相关章节。

> **排查准备清单**：确保拥有服务器访问权限、数据库读写权限、相关服务的日志读取权限，以及必要的调试工具（curl、psql、openssl、qpdf）。

---

## 2. 认证问题

### 2.1 无法登录
- **可能原因**：
  - 用户名或密码错误；用户被禁用或未验证邮箱。
  - 数据库连接异常导致认证查询失败。
  - 后端使用的加密主密钥（`ENCRYPTED_STORAGE_MASTER_KEY`）变更，导致加密凭证无法解密。
  - 使用外部身份源（OAuth/LDAP）时网络中断或凭证配置错误。
- **检查步骤**：
  1. 使用 `curl -X POST http://<host>/api/v1/auth/login` 测试 API，观察返回的状态码与错误信息。
  2. 在后台日志中搜索 `login`、`Invalid credentials`、`User disabled` 关键字。
  3. 若使用 LDAP，执行 `ldapsearch -x -H ldap://<server>` 验证连通性。
  4. 查看数据库 `users` 表确认 `is_active`、`is_verified` 字段状态。
- **日志位置**：`docker-compose logs backend`、系统日志目录 `/var/log/ca-pdf/backend.log`（若配置了文件输出）。
- **解决方案**：
  - 使用脚本重置密码：`poetry run python scripts/reset_password.py --email <user@example.com>`。
  - 恢复或重新配置 `ENCRYPTED_STORAGE_MASTER_KEY`，确保与历史密钥一致。
  - 若数据库不可达，参考第 7 章进行连通性和服务状态排查。
- **预防措施**：开启登录失败告警，定期备份密钥与 `.env` 文件。

### 2.2 Token 过期或无效
- **可能原因**：Access Token 超出有效期、系统时间漂移、签名密钥变更、Token 被压缩或修改。
- **检查步骤**：
  1. 查看返回的 HTTP 状态码（通常为 401）及响应消息 `Token expired` 或 `Invalid token`。
  2. 在服务器上执行 `date`，确保时间同步；必要时执行 `sudo timedatectl set-ntp true`。
  3. 确认 `.env` 中的 `SECRET_KEY` 未被误改；若更换了密钥，需通知所有用户重新登录。
  4. 使用 `jwt.io` 或 `python -m jose.jws` 解码 Token，核对 `exp` 等字段。
- **日志位置**：后端日志中的 `JWT decode error`、`Signature verification failed`、`ExpiredSignatureError`。
- **解决方案**：
  - 再次登录以刷新 Token。
  - 确保集群中的所有副本使用相同的 `SECRET_KEY`。
  - 若系统时间漂移过大，配置 Chrony/NTP 服务保持同步。
- **预防措施**：监控系统时间漂移，启用 Token 过期前的续签机制。

### 2.3 权限不足（403）
- **可能原因**：角色配置错误、权限策略未同步、JWT 中缺少 `scopes`，或资源所属租户与用户不匹配。
- **检查步骤**：
  1. 查看用户角色：登录后台管理页面或执行 `SELECT email, roles FROM users WHERE email = 'xxx';`。
  2. 检查 API 的角色要求，参考 `backend/app/api/deps.py` 中的权限依赖与 FastAPI 路由配置。
  3. 在 JWT payload 中确认 `scopes` 与系统定义一致。
  4. 若涉及多租户，确认请求头或 Token 中的 `tenant_id` 与资源所属一致。
- **日志位置**：`Access denied`、`Insufficient privileges`、`Permission denied`。
- **解决方案**：
  - 通过 `/api/v1/users/{id}` PATCH 接口或后台界面更新角色。
  - 若新增了权限点，确保在部署后重新加载权限策略缓存。
  - 审核多租户配置，防止跨租户访问。
- **预防措施**：建立角色变更流程，定期审计权限配置。

### 2.4 邮箱和密码正确但仍无法登录
- **可能原因**：账号锁定策略生效、邮箱未验证、用户被手动禁用、外部身份源延迟同步。
- **检查步骤**：
  1. 查询 `users` 表中的 `failed_login_attempts`、`last_login_at` 字段。
  2. 查看安全策略配置，如连续失败次数上限和锁定时间。
  3. 检查 SMTP 日志确认验证邮件是否发送成功，必要时在邮箱系统内查找。
  4. 对于外部身份源，确认同步任务或定时器运行正常。
- **日志位置**：`Account locked`、`Email not verified`、SMTP 发送日志。
- **解决方案**：
  - 通过管理界面或 SQL 清理失败次数：`UPDATE users SET failed_login_attempts = 0 WHERE email = 'xx';`
  - 手动标记邮箱为已验证：`UPDATE users SET is_verified = true WHERE email = 'xx';`
  - 修复 SMTP 配置，重新发送验证邮件。
- **预防措施**：在通知用户密码或策略变更前提前公告，避免因锁定策略造成误报。

### 2.5 调试命令与技巧
- **基础命令**：
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "secret"}'
  ```
- **解码 JWT**：`poetry run python -m jose.jwt decode <token> <SECRET_KEY>`。
- **浏览器调试**：打开开发者工具（F12），在 Network 面板确认 `Authorization` 头是否携带 Bearer Token，Console 是否存在跨域或脚本错误。
- **MFA/SSO**：如果集成第三方 SSO，请查看回调日志以及 `redirect_uri` 是否正确。

### 2.6 常见认证案例复盘
- **场景 A：升级后所有用户登出**：升级过程中误更换 `SECRET_KEY`，导致旧 Token 失效。解决方案为恢复旧密钥或通知用户重新登录，并在发布流程中增加密钥校验。
- **场景 B：特定用户登录失败**：发现该用户被分配到已删除的角色组。通过数据库修复角色关系并重新缓存权限后问题解决。

---

## 3. 证书管理问题

### 3.1 无法生成根 CA
- **可能原因**：
  - 选择的签名算法不受系统或 OpenSSL 支持，如 `SM2` 在部分环境缺少依赖。
  - CSR 或主体信息字段格式不符合校验，如国家代码必须为两个大写字母。
  - 数据库写入失败，常见于序列号冲突或磁盘空间不足。
- **排查步骤**：
  1. 查看后端日志中的 `create_root_ca` 调用栈及异常信息。
  2. 检查 `cas` 表中是否已有相同名称或序列号的记录。
  3. 确认证书文件目录（默认 `storage/certs`）具备写权限。
  4. 运行 `openssl version -a` 确认依赖库版本。
- **解决方案**：
  - 切换受支持的算法（RSA2048/4096、ECDSA P-256）。
  - 校验输入参数，遵循 X.509 字段规范。
  - 修复数据库冲突或清理磁盘空间后重试。
- **预防措施**：在上线前使用测试环境验证各算法，并设置磁盘使用率告警。

### 3.2 证书签发失败
- **可能原因**：CSR 签名算法与 CA 不匹配、有效期超出限制、策略限制导致拒签。
- **排查步骤**：
  1. 使用 `openssl req -in req.csr -noout -text` 查看 CSR 详细信息。
  2. 在日志中查找 `issue_certificate` 及相关异常。
  3. 检查策略配置（有效期、KeyUsage、ExtendedKeyUsage）。
- **解决方案**：
  - 重新生成与 CA 算法匹配的 CSR。
  - 调整签发策略或与安全团队确认策略变更。
  - 若是自动化流程，确认模板文件未损坏。
- **预防措施**：将策略与模板纳入版本管理，变更需评审。

### 3.3 证书导入失败
- **常见原因**：
  - 上传文件格式不受支持或编码不正确。
  - PFX 密码错误或证书链不完整。
  - 文件损坏或上传过程中被截断。
- **排查步骤**：
  1. 核对文件扩展名、MIME 类型。若为 DER，使用 `openssl x509 -inform DER -in cert.cer -out cert.pem` 转换。
  2. 对 PFX 使用 `openssl pkcs12 -in cert.pfx -info` 检查能否解包。
  3. 查看后端日志 `Certificate import failed`、`Invalid certificate format`。
- **解决方案**：
  - 重新导出证书，确保包含完整链与私钥。
  - 使用正确密码并避免使用非 ASCII 字符（部分库不支持）。
  - 若是大文件，通过命令行导入以避免超时。
- **预防措施**：提供标准导出模板，指导用户统一格式提交。

### 3.4 找不到证书
- **原因**：筛选条件错误、证书被吊销或隐藏、索引不同步。
- **排查步骤**：
  1. 确认搜索关键词（名称、序列号、颁发者）。
  2. 在数据库执行 `SELECT * FROM certificates WHERE serial_number = '<SN>';`。
  3. 若使用全文索引或外部搜索服务，检查同步任务状态。
  4. 确认当前登录用户是否有权限查看该证书所属租户。
- **解决方案**：清理无效缓存、重新触发索引同步、调整权限。

### 3.5 CRL 生成错误
- **原因**：CRL 模板缺失、吊销列表为空、OpenSSL 配置异常、时间戳错误。
- **排查步骤**：
  1. 查看日志 `Generate CRL failed`、`OpenSSL error`。
  2. 确认根 CA 或中间 CA 的 CRL 分发点已配置。
  3. 检查 CRL 输出路径的读写权限。
  4. 若报错与时间相关，校正服务器时间。
- **解决方案**：补全模板、确保至少有一条吊销记录、修复 OpenSSL 配置。
- **预防措施**：定期生成 CRL 并验证文件可被下载与解析。

---

## 4. PDF 签章问题

### 4.1 PDF 上传失败
- **可能原因**：
  - 文件格式不支持，仅允许标准 PDF。
  - 文件大小超出 `PDF_MAX_SIZE_MB` 限制。
  - 文件损坏或加密，无法解析。
  - 对象存储或磁盘不可写。
- **排查步骤**：
  1. 检查日志中 `Unsupported file type`、`File too large` 信息。
  2. 使用 `pdfinfo`、`qpdf --check` 验证文件完整性。
  3. 确认上传目录或对象存储凭证可用。
  4. 在浏览器 Network 面板查看上传请求是否成功返回。
- **解决方案**：
  - 提供符合规范的 PDF 文件或压缩文件尺寸。
  - 在 `.env` 中适当调高 `PDF_MAX_SIZE_MB`。
  - 修复存储权限或更换上传路径。
- **预防措施**：在客户文档中明确上传限制，前端提前校验文件大小。

### 4.2 签章配置无法保存
- **可能原因**：配置校验失败、名称重复、数据库事务回滚。
- **排查步骤**：
  1. 查看请求返回的 422 错误详情。
  2. 检查 `signature_profiles` 表是否存在重复记录。
  3. 观察日志 `Save signature profile failed`。
- **解决方案**：
  - 补全必填字段，确保 JSON 结构正确。
  - 更换唯一名称，或清理旧配置。
  - 修复数据库事务错误。
- **预防措施**：前端增加实时校验，后端使用幂等接口防止重复提交。

### 4.3 签章过程中出错
- **常见错误**：`Signature process failed`、`Certificate revoked`、`TSA timeout`。
- **排查步骤**：
  1. 确认签章所用证书未过期且未被吊销。
  2. 若启用时间戳，测试 TSA 服务连通性。
  3. 检查签章服务临时目录和 `/tmp` 是否可写。
  4. 查看签章线程是否因内存不足被 OOM Killer 终止。
- **解决方案**：
  - 更新证书或重新申请。
  - 配置 TSA 备用地址或增加超时重试。
  - 调整容器内存限制，优化临时文件清理。

### 4.4 签章后 PDF 无法打开
- **可能原因**：签章后文件结构损坏、可见签章资源丢失、签章过程中断导致文件不完整。
- **排查步骤**：
  1. 使用 `qpdf --check signed.pdf` 分析结构。
  2. 对比签章前后文件大小，确认未被截断。
  3. 在日志中搜索 `Finalize signed PDF failed`。
- **解决方案**：
  - 重新签章，确保签章过程中无异常终止。
  - 验证可见签章图片路径可用。
  - 检查签章组件版本，必要时回退。

### 4.5 时间戳无法获取（TSA 不可用）
- **排查步骤**：
  1. `curl -k https://tsa.example.com` 测试网络连通。
  2. 查看 TSA 返回码或响应体，确认是否认证失败。
  3. 检查 `.env` 中 `TSA_URL`、`TSA_USERNAME`、`TSA_PASSWORD`。
- **解决方案**：
  - 启用本地 TSA 备份或配置多个 TSA 地址轮询。
  - 临时禁用强制时间戳以保持业务连续性，并标记签章结果存在风险。
  - 若为证书过期，联系 TSA 提供方更新。
- **预防措施**：为 TSA 接口配置健康检查与告警。

### 4.6 印章上传失败
- **排查步骤**：
  1. 确认文件类型（建议 PNG、SVG、JPG）。
  2. 检查大小限制：在 `.env` 中通过 `STAMP_MAX_SIZE_MB` 控制。
  3. 查看日志 `Seal upload failed`、`Image processing failed`。
- **解决方案**：
  - 压缩图片或转换为受支持格式。
  - 安装图像处理依赖（Pillow、libjpeg）。
  - 确保存储目录可写。

### 4.7 可见签章中的印章不显示
- **可能原因**：签章配置引用的 `image_id` 不存在、前端缓存未更新、PDF 阅读器不支持透明度。
- **排查步骤**：
  1. 在数据库 `stamps` 表确认图片存在。
  2. 清理前端缓存或强制刷新页面（Ctrl+F5）。
  3. 使用多种 PDF 阅读器测试。
- **解决方案**：
  - 修复配置中的引用 ID。
  - 更新前端版本，确保可见签章渲染逻辑兼容。
  - 若涉及透明度，调整图片底色或格式。

---

## 5. 验签问题

### 5.1 无法验签
- **可能原因**：文件损坏、非 PDF、签名数据缺失、上传过程中被截断。
- **排查步骤**：
  1. 使用 `file signed.pdf` 验证文件类型。
  2. 查看日志 `verify_pdf_signature`、`Signature block not found`。
  3. 对比上传前后的文件哈希：`sha256sum`。
  4. 若用户来自外部系统，确认其导出的文件未被再次处理。
- **解决方案**：要求重新上传完整文件或提供原始签名文档。

### 5.2 验签结果显示无效
- **原因**：证书过期、被吊销、签名被篡改、摘要不匹配。
- **排查步骤**：
  1. 在验签详情中查看失败原因。
  2. 使用 `openssl pkcs7 -in signed.pdf -print_certs` 提取证书，检查有效期。
  3. 更新 CRL/OCSP，确保最新吊销信息同步。
- **解决方案**：
  - 重新签章或更新证书。
  - 如果是文件被修改，要求提供原始文件。

### 5.3 信任链无法验证
- **可能原因**：缺少根证书、证书链顺序错误、交叉签名未导入。
- **排查步骤**：
  1. 确认根 CA 已被导入信任库。
  2. 检查证书链顺序是否正确（根证书应在末尾）。
  3. 查看日志 `Trust chain incomplete`。
- **解决方案**：
  - 导入完整证书链。
  - 对于自签根证书，手动设置信任。

### 5.4 时间戳状态异常
- **原因**：TSA 返回 `grantedWithMods`、时间戳证书过期、响应签名无效。
- **排查步骤**：
  1. 查看时间戳详细信息（可通过 Adobe 或 `openssl ts -replyin`）。
  2. 检查 TSA 证书有效期。
  3. 确认系统时间同步。
- **解决方案**：
  - 联络 TSA 服务商修复。
  - 对于内部 TSA，更新证书并重启服务。

---

## 6. 用户管理问题

### 6.1 创建用户失败
- **常见原因**：邮箱重复、密码策略不符合、角色不存在、数据库写入异常。
- **排查步骤**：
  1. 检查响应码（409/422/500）。
  2. 查看日志 `create_user`、`IntegrityError`。
  3. 在数据库确认邮箱是否唯一。
- **解决方案**：
  - 指导用户使用未注册的邮箱。
  - 调整密码以满足策略（长度、复杂度、历史密码限制）。
  - 修复角色配置并重新同步。
- **预防措施**：提供标准的导入模板和在线校验提示。

### 6.2 无法编辑用户信息
- **可能原因**：权限不足、请求方法错误、租户隔离导致无法修改其他租户用户。
- **排查步骤**：
  1. 确认当前用户角色是否具备 `user:update` 权限。
  2. 检查 API 请求是否使用 PATCH/PUT。
  3. 查看日志 `Permission denied editing user`、`Tenant mismatch`。
- **解决方案**：
  - 授予必要权限。
  - 在多租户场景下，通过管理员入口进行跨租户操作。

### 6.3 重置密码后仍无法登录
- **原因**：用户仍使用旧 Token、重置脚本未成功写入、邮箱通知失败。
- **排查步骤**：
  1. 查看重置脚本输出是否为 `Password updated`。
  2. 在数据库确认密码哈希更新时间。
  3. 通知用户清理浏览器缓存并重新登录。
- **解决方案**：
  - 再次执行重置脚本或在后台手动设置。
  - 若 SMTP 失败，补发通知邮件。

### 6.4 批量导入用户时出错（CSV 格式问题）
- **常见错误**：编码非 UTF-8、字段缺失、分隔符错误、存在额外 BOM、空行。
- **排查步骤**：
  1. 使用 `iconv -f utf-8 -t utf-8` 检查编码。
  2. 使用 `csvlint` 或在线工具验证格式。
  3. 在日志中定位具体行号。
- **解决方案**：
  - 根据模板修正 CSV。
  - 对每行数据进行预处理，确保角色名称存在。
- **预防措施**：在导入前先执行预检查接口，减少一次性错误。

---

## 7. 数据库相关问题

### 7.1 数据库连接失败
- **检查数据库服务**：`docker-compose ps db`、`systemctl status postgresql`。
- **验证连接字符串**：`DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`，注意特殊字符需 URL 编码。
- **检查防火墙**：`nc -vz host 5432` 或 `telnet host 5432`。
- **观察日志**：`Connection refused`、`timeout expired`。
- **解决方案**：
  - 启动数据库服务或恢复实例。
  - 更新 `.env` 中的凭证并重启后端。
  - 在云环境中配置安全组和防火墙规则。
- **预防措施**：为数据库配置健康检查、连接池告警。

### 7.2 迁移失败
- **症状**：执行 `poetry run alembic upgrade head` 报错。
- **排查步骤**：
  1. 查看错误堆栈，关注 `alembic.util.exc.CommandError`、`AsyncConnection` 等关键字。
  2. 若脚本本身错误，可运行 `poetry run alembic downgrade -1` 回滚。
  3. 检查迁移脚本是否包含同步与异步混用、未提交事务等问题。
  4. 确认迁移版本号长度不超过 32 字符（PostgreSQL 限制）。
- **解决方案**：修复迁移脚本、重新生成并验证，再次执行升级。
- **预防措施**：迁移前在测试环境执行完整升级，使用 CI 自动验证。

### 7.3 数据库锁定（并发操作冲突）
- **表象**：接口长时间无响应，日志出现 `deadlock detected` 或 `could not obtain lock`。
- **排查步骤**：
  1. 使用 `SELECT * FROM pg_locks WHERE NOT granted;` 查看锁等待。
  2. 通过 `SELECT pid, query FROM pg_stat_activity WHERE state <> 'idle';` 找到阻塞进程。
  3. 如需强制释放，可执行 `SELECT pg_terminate_backend(pid);`（谨慎操作）。
- **解决方案**：优化事务粒度、拆分批量操作、设置合理的锁等待超时。
- **预防措施**：对高并发写操作使用队列或乐观锁，定期审查慢查询。

### 7.4 磁盘空间不足导致数据库错误
- **排查步骤**：
  1. 运行 `df -h`、`du -sh /var/lib/postgresql` 检查磁盘使用情况。
  2. 查看 PostgreSQL 日志 `No space left on device`。
  3. 清理归档日志、旧备份、无用临时文件。
- **解决方案**：
  - 扩容磁盘或迁移至更大的卷。
  - 配置自动清理机制，例如 `vacuumdb`、归档轮转。
- **预防措施**：设置磁盘使用率告警，定期监控增长趋势。

### 7.5 数据备份与恢复注意事项
- 定期执行逻辑备份：`pg_dump -Fc ca_pdf > backup.dump`。
- 恢复前暂停写操作，使用 `pg_restore` 导入并执行校验。
- 测试环境定期演练恢复流程，确保备份可用。

---

## 8. 性能问题

### 8.1 应用启动缓慢
- **排查步骤**：
  1. 查看启动日志，关注依赖初始化耗时（数据库、缓存、定时任务）。
  2. 对比启动前后 CPU/内存占用。
  3. 在 Kubernetes 环境中检查 `readinessProbe` 是否通过。
- **解决方案**：
  - 延迟加载非关键组件。
  - 对初始化步骤进行异步化处理。
  - 缩短外部依赖的超时时间。

### 8.2 API 响应缓慢
- **监控指标**：平均响应时间、P95/P99 延迟、数据库查询时间。
- **排查步骤**：
  1. 启用 SQLAlchemy 日志或 APM 工具（如 Prometheus + Grafana）。
  2. 使用 `EXPLAIN ANALYZE` 分析慢查询。
  3. 观察网络延迟（`ping`、`mtr`）。
- **解决方案**：
  - 添加索引、优化查询、减少不必要的 JOIN。
  - 使用缓存层（Redis/Memory Cache）。
  - 将耗时操作拆分为后台任务。

### 8.3 大文件签章超时
- **排查步骤**：
  1. 检查后端超时配置 `REQUEST_TIMEOUT`、`GUNICORN_TIMEOUT`。
  2. 监控签章过程中的 CPU/内存使用。
  3. 评估网络带宽是否满足大文件上传需求。
- **解决方案**：
  - 提高超时时间或拆分文件分段处理。
  - 在上传前压缩或预处理 PDF。
  - 使用任务队列异步处理大文件，前端轮询结果。

### 8.4 前端页面加载缓慢
- **排查步骤**：
  1. 使用浏览器 Performance 工具分析首屏渲染。
  2. 检查静态资源是否开启 gzip/brotli 压缩。
  3. 确认 CDN/代理缓存是否生效。
- **解决方案**：
  - 进行代码分割、懒加载非关键组件。
  - 压缩图片、合并小文件。
  - 为 API 响应设置合理的缓存头。

### 8.5 内存占用持续增长
- **排查步骤**：
  1. `docker stats` 或 `top` 查看内存趋势。
  2. 使用 `tracemalloc`、`objgraph` 定位内存泄漏。
  3. 检查异步任务是否正确关闭连接、释放句柄。
- **解决方案**：
  - 修复内存泄漏代码。
  - 为容器设置内存上限并配置重启策略。
  - 定期重启长时间运行的工作进程（配合滚动更新）。

---

## 9. 部署相关问题

### 9.1 Docker 容器无法启动
- **排查步骤**：
  1. `docker-compose ps` 查看容器状态，关注 `Exit` 代码。
  2. `docker-compose logs backend`、`docker-compose logs frontend` 查看错误信息。
  3. 确认宿主机场景：端口冲突（`lsof -i :8000`）、磁盘空间、内存限制。
  4. 校验环境变量与 `docker-compose.yml` 中的配置一致。
- **解决方案**：
  - 修复配置错误后重新 `docker-compose up -d`。
  - 若镜像拉取失败，检查网络或私有仓库凭证。
  - 对于持续重启的容器，排查健康检查与依赖启动顺序。

### 9.2 访问被拒绝（CORS 错误）
- **典型症状**：浏览器控制台提示 `No 'Access-Control-Allow-Origin' header`。
- **排查步骤**：
  1. 确认 `BACKEND_CORS_ORIGINS` 为 JSON 列表格式：`["https://example.com", "http://localhost:3000"]`。
  2. 检查前端请求是否携带凭证，若需要跨域 Cookie，需设置 `allow_credentials=true`。
  3. 使用 curl 模拟请求：`curl -H "Origin: https://example.com" -I http://backend/api/v1/users/me`。
- **错误示例**：
  ```env
  BACKEND_CORS_ORIGINS="http://example.com"  # ❌ 错误写法
  BACKEND_CORS_ORIGINS='["http://example.com"]'  # ✅ 正确写法
  ```
- **解决方案**：更新配置并重启服务，若使用 Traefik/Nginx 反向代理，确保未覆盖响应头。

### 9.3 反向代理配置错误
- **常见问题**：WebSocket 未正确透传、HTTPS 回源、头部丢失。
- **排查步骤**：
  1. 检查代理配置（Nginx、Traefik）是否转发 `Upgrade`、`Connection` 头。
  2. 确认 `X-Forwarded-Proto`、`X-Real-IP` 传递正确，Uvicorn 能识别真实协议。
  3. 使用 `curl -I`、`curl -H "X-Forwarded-Proto:https"` 测试。
- **解决方案**：根据官方文档调整代理配置，必要时启用 `proxy_redirect`。

### 9.4 HTTPS 证书过期
- **排查步骤**：
  1. `openssl s_client -connect domain:443 -servername domain` 查看证书链与有效期。
  2. 检查自动续签任务（cron、certbot、acme.sh）是否执行成功。
- **解决方案**：
  - 重新申请和部署证书，更新反向代理配置后重启。
  - 对即将过期的证书提前设置告警。

### 9.5 Kubernetes 部署注意事项
- **健康检查**：配置 `livenessProbe`、`readinessProbe`，指向 `/api/v1/health`。
- **配置管理**：通过 ConfigMap/Secret 管理 `.env` 与密钥，确保滚动更新过程中密钥一致。
- **存储**：为证书与临时文件挂载持久卷，防止 Pod 重启导致数据丢失。

---

## 10. 日志和调试工具

### 10.1 查看后端日志
- **Docker 环境**：`docker-compose logs backend --tail 200 -f`
- **本地开发**：`poetry run uvicorn app.main:app --reload`，日志输出在终端。
- **结构化日志**：通过设置 `LOG_FORMAT=json` 将日志导入 ELK、 Loki 等平台。
- **日志级别**：在 `.env` 中设置 `LOG_LEVEL=debug` 或 `warning`，根据排查需要动态调整。

### 10.2 查看前端控制台
- 浏览器开发者工具（F12）：
  - **Console** 标签查看报错堆栈及警告。
  - **Network** 标签筛选 XHR/Fetch，请求详情可用于比对请求头、响应体、CORS 设置。
  - **Performance** 标签分析首屏渲染与脚本执行时间。

### 10.3 查看数据库查询
- **PostgreSQL**：
  - 启用慢查询日志 `log_min_duration_statement=500ms`。
  - 使用 `EXPLAIN (ANALYZE, BUFFERS)` 排查慢查询。
  - 结合 `pg_stat_statements` 模块统计热点 SQL。
- **SQLite（测试环境）**：启用 `PRAGMA optimize;`，使用 `EXPLAIN QUERY PLAN` 分析。

### 10.4 Swagger API 文档调试
- 访问 `http://<host>/docs` 或 `/redoc`，通过内置 UI 调用 API。
- 在 `Authorize` 中输入 `Bearer <token>` 进行认证。
- 利用 Swagger 自带的示例请求对比接口定义与实际响应。

### 10.5 使用 curl 测试 API
- **示例命令**：
  ```bash
  TOKEN="$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"admin@example.com","password":"secret"}' | jq -r '.access_token')"
  curl -H "Authorization: Bearer ${TOKEN}" http://localhost:8000/api/v1/users/me
  ```
- **常见问题**：忘记携带 Token、Content-Type 设置错误、HTTPS 证书验证失败（使用 `-k` 暂时忽略）。
- **进阶技巧**：
  - 通过 `curl -v` 查看请求头详情。
  - 使用 `jq` 格式化 JSON 响应。

### 10.6 其他调试工具
- **Postman / Insomnia**：可保存请求集合，方便团队共享。
- **tcpdump/wireshark**：排查底层网络问题。
- **Grafana / Prometheus**：监控 CPU、内存、请求量、错误率。

### 10.7 远程调试与端口转发
- **SSH 隧道**：通过 `ssh -L 8080:localhost:8000 user@server` 将远程后端端口转发到本地，方便使用浏览器或 Postman 调试。
- **Kubernetes Port-Forward**：`kubectl port-forward deployment/backend 8000:8000` 可在无需暴露服务的情况下快速定位问题，排查完毕后记得关闭转发。
- **VS Code Remote**：利用 Remote SSH 或 Dev Containers 插件，在服务器上直接打开代码并附加调试器，适用于定位复杂逻辑错误。

---

## 11. 常见错误码解读

### 4xx 客户端错误
- **400 Bad Request**：参数缺失、格式错误或 JSON 解析失败，需检查请求体。
- **401 Unauthorized**：未认证或 Token 失效，重新登录或刷新 Token。
- **403 Forbidden**：权限不足，检查角色与权限策略。
- **404 Not Found**：资源不存在或路径错误，确认 URL 与 ID。
- **409 Conflict**：资源冲突（如重复邮箱、证书已存在、版本冲突）。
- **412 Precondition Failed**：通常出现在条件请求（If-Match）失败。
- **422 Unprocessable Entity**：字段验证失败，查看响应中 `detail` 字段。
- **429 Too Many Requests**：触发限流策略，需放慢请求或调整限流配置。

### 5xx 服务器错误
- **500 Internal Server Error**：后端异常，查看日志堆栈。
- **502 Bad Gateway**：反向代理无法连接后端，检查后端是否运行。
- **503 Service Unavailable**：服务不可用或依赖故障，确认数据库/外部服务状态。
- **504 Gateway Timeout**：上游服务超时，检查后端性能或网络。

---

## 12. 获取帮助和提交 Bug

1. **收集必要信息**：
   - 系统版本（Git 提交号、Docker 镜像标签、前端构建版本）。
   - 部署模式与拓扑（本地、Docker Compose、Kubernetes、反向代理、TSA）。
   - 关键配置（`.env`、环境变量、Traefik/Nginx 配置片段）。
   - 完整日志（时间范围、服务名称、错误堆栈）。
   - 复现步骤与输入参数、请求示例。
2. **提交 Issue 最佳实践**：
   - 标准模板：**标题** + **环境** + **复现步骤** + **期望结果** + **实际结果** + **日志/截图** + **影响范围**。
   - 若问题影响生产，请标注严重度和所需响应时间。
   - 附加网络拓扑图或部署示意有助于快速定位。
3. **支持渠道**：
   - 项目官方 Issue 列表或内部工单系统。
   - 团队即时通讯群组（Slack/微信工作群），必要时 @ 相关负责人。
   - 若购买商业支持，按照 SLA 要求提交工单并附带必要资料。
4. **复盘建议**：问题解决后撰写故障通报，记录根因与改进措施。
5. **Issue 模板示例**：
   ```text
   标题：<简明描述>
   环境：生产 / 预发布 / 本地；版本 <commit/tag>
   复现步骤：1) … 2) … 3) …
   期望结果：<期望行为>
   实际结果：<实际表现和错误信息>
   附件：相关截图 / 日志 / 网络抓包
   影响范围：<受影响用户或业务流程>
   ```

---

## 13. 性能优化建议

### 13.1 后端优化
- **数据库索引**：为高频查询字段（用户邮箱、证书序列号、任务状态）创建索引，并定期评估索引使用率。
- **查询优化**：避免 N+1 查询，使用 SQLAlchemy `selectinload` 等预加载方式；借助 `EXPLAIN` 分析慢查询并重写 SQL。
- **缓存策略**：
  - 使用 Redis 缓存权限、配置、热点数据。
  - 对静态 CRL、证书列表设置合理的缓存失效时间。
- **异步任务**：
  - 将耗时操作（大文件签章、批量导入、报告生成）放入 Celery/Redis 队列。
  - 配置重试与失败告警，防止任务堆积。
- **横向扩展**：
  - 利用容器编排（Kubernetes）增加实例数量。
  - 配置负载均衡器（Traefik/Nginx/HAProxy）与健康检查。

### 13.2 前端优化
- **代码分割**：通过动态加载、懒加载减少首屏 bundle 体积。
- **静态资源优化**：启用 gzip/brotli 压缩，合理设置 `Cache-Control` 头；将大图转换为 webp。
- **缓存策略**：对接口数据使用 SWR、本地缓存或 IndexedDB，减少重复请求。
- **监控埋点**：集成前端监控（Sentry、阿里 ARMS），收集性能指标和错误日志。

### 13.3 全局优化
- **压测与容量规划**：定期执行压测（JMeter、k6），评估并发能力，及时扩容。
- **资源治理**：设置 CPU/内存/磁盘告警阈值，结合自动扩缩容策略。
- **安全与稳定性**：启用 WAF、限流、熔断机制，避免恶意请求导致性能下降。

---

> 若仍无法解决问题，请将本指南中的排查结果、日志和环境信息一并反馈给支持团队，以便快速定位根因。祝您排障顺利、发布稳定！
---

🔗 **相关文档**
- [部署手册](./DEPLOYMENT.md)
- [用户指南](./USER_GUIDE.md)
- [API 文档](./API.md)
- [安全指南](./SECURITY.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

