# ca-pdf 文档使用指南

> 📖 **文档导航**：[文档索引](./DOCUMENTATION.md) · [README](./README.md) · [开发指南](./DEVELOPMENT.md) · [部署手册](./DEPLOYMENT.md) · [用户指南](./USER_GUIDE.md)
> 🎯 **适用人群**：首次阅读者 / 文档维护者
> ⏱️ **预计阅读时间**：8 分钟

**项目地址**：[https://github.com/QAQ-AWA/ca-pdf](https://github.com/QAQ-AWA/ca-pdf)
**联系邮箱**：[7780102@qq.com](mailto:7780102@qq.com)

本指南帮助你快速熟悉 ca-pdf 文档体系的结构、维护方式与常见入口，是阅读其他文档之前的最佳参考资料。

---

## 如何快速找到信息

1. 先阅读 [DOCUMENTATION.md](./DOCUMENTATION.md) 获取全局地图与角色推荐路线。
2. 根据自身角色在 README 的“📚 文档导航”中选择合适的阅读顺序。
3. 每份文档顶部均有“📖 文档导航”块，可在主要文档之间快速跳转。
4. 需要排查问题时，直接跳转到文末的“❓ 需要帮助？”链接回 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。

## 文档结构约定

- **顶部信息区域**：包含导航链接、适用人群、阅读时间、项目信息以及与其他文档的关联说明。
- **底部信息区域**：统一以“🔗 相关文档”列出推荐阅读，并使用“❓ 需要帮助？”指向 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。
- **命名规范**：所有文件使用大写下划线或驼峰式命名，保持与仓库现有文件一致。
- **链接风格**：统一使用 \`[文本](相对路径)\`（示例为 Markdown 语法，实际使用时请替换为具体路径），外部链接需包含协议头并定期检查有效性。
- **内容取舍**：
  - 快速开始命令保留在 [README](./README.md)。
  - 技术栈与版本矩阵仅在 [ARCHITECTURE.md](./ARCHITECTURE.md) 中维护。
  - 环境变量清单与部署脚本说明集中在 [DEPLOYMENT.md](./DEPLOYMENT.md)。
  - API 示例与错误码在 [API.md](./API.md)。

## 维护流程

1. **需求识别**：当代码或配置发生变化时，确认受影响的文档章节。
2. **内容更新**：使用与现有风格一致的标题、列表、代码块和表格格式，避免重复内容。
3. **交叉引用**：更新完毕后，检查是否需要在其他文档添加或调整链接，确保文档之间互通。
4. **自查清单**：
   - 链接是否可用、路径是否正确？
   - 是否注明项目地址与联系邮箱？
   - 是否引用了正确的专题文档（例如环境变量引用 DEPLOYMENT）？
   - 是否在 PR 模板中标记“文档更新”并描述变更？
5. **同侪评审**：在代码评审时一并审阅文档变更，确保术语一致、语气正式且友好。

## 常用术语对照

| 术语 | 说明 | 对应文档 |
|------|------|----------|
| CA | Certificate Authority，证书颁发机构 | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| LTV | Long-Term Validation，长期有效签名 | [USER_GUIDE.md](./USER_GUIDE.md) |
| TSA | Time Stamping Authority，时间戳服务 | [DEPLOYMENT.md](./DEPLOYMENT.md) |
| RBAC | Role-Based Access Control，基于角色的权限控制 | [API.md](./API.md) |
| OTA 更新 | Over-The-Air，无缝更新机制 | [CHANGELOG.md](./CHANGELOG.md) |

## 常见问题

- **找不到合适的文档？** 先阅读 [DOCUMENTATION.md](./DOCUMENTATION.md) 的“主题索引”。
- **不知道文档最新更新时间？** 可在 README 底部或各文档的“最后更新”标注中查看。
- **链接失效怎么办？** 提交 issue 或直接更新对应文档，并在 PR 中说明修复的链接。
- **想要贡献文档？** 请遵循 [CONTRIBUTING.md](./CONTRIBUTING.md) 的流程，并在 MR/PR 中附带截图或示例。

---

🔗 **相关文档**
- [DOCUMENTATION.md](./DOCUMENTATION.md)
- [README](./README.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

❓ **需要帮助？**
- 请查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
