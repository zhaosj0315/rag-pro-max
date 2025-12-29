# 项目全量同步、对齐与清理标准 (Post-Development Synchronization Standard)
**版本**: v2.8.0 (Expert Reviewed)  
**类型**: 工程管理规范  
**适用阶段**: 开发完成 (Code Freeze) 后，发布/推送前  
**执行角色**: Release Manager / Tech Lead

---

## 🎯 核心原则 (Core Principles)

1.  **代码即真理 (Code is Truth)**: 代码库一旦锁定，即为最终事实标准。所有文档必须向代码现状看齐，严禁反向修改代码以适配文档。
2.  **全量对齐 (Full Alignment)**: 不允许存在“代码已更新但文档未更新”的灰色地带。
3.  **零噪交付 (Zero Noise)**: 交付物必须纯净，所有过程性、临时性文件必须物理删除或归档。
4.  **自动化优先 (Automation First)**: 凡是可以通过脚本验证的检查项，必须优先使用脚本执行。

---

## 1. 锚定当前事实 (Phase 1: Anchor Truth)

在执行同步前，必须明确以下三个基准：

- **🔒 代码锁定 (Code Freeze)**: 确认所有功能分支已合并，本地工作区干净 (`git status` clean)，不再进行逻辑变更。
- **🏷️ 版本确立 (Versioning)**: 严格遵循 [SemVer 2.0](https://semver.org/) 规范确定版本号 (e.g., `v2.8.0`)。
- **📝 变更范围 (Scope)**: 明确本次迭代的核心逻辑变更点（Core Changes），区分 "Feature", "Fix", "Refactor"。

---

## 2. 三步走执行路径 (Phase 2: Execution Workflow)

### 第一阶段：自动化验证与配置同步 (Automated Verification)

利用项目内置脚本进行初筛，确保低级错误被拦截。

#### 1. 脚本扫描 (Script Execution)
- [ ] **文档同步检查**: 运行 `./scripts/check_docs_sync.sh` (如有) 或相关检查脚本，扫描文档中的版本号是否滞后。
- [ ] **清理脚本执行**: 运行 `./scripts/cleanup.sh`，自动清理 `__pycache__`, `.DS_Store`, 临时日志等。

#### 2. 配置层 (Configuration Layer)
- [ ] **version.json**: 更新 `version` 字段，确保与锚定版本一致。
- [ ] **.gitignore**: 检查是否有新增的临时文件类型或敏感配置需忽略。使用 `git check-ignore -v <file>` 验证关键文件是否被正确忽略。

---

### 第二阶段：全量文档同步 (Documentation Synchronization)

必须按照以下四个维度顺序检查并更新文档：

#### 1. 记录层 (Record Layer)
- [ ] **CHANGELOG.md**: 
    - 按照 `[版本号] - 日期` 格式记录。
    - 分类记录：`🚀 New`, `⚡ Improvement`, `🐛 Fix`, `🔧 Refactor`。
    - **关键**: 必须包含 Breaking Changes 的显式警告。
- [ ] **README.md**: 
    - 更新顶部 Badges (Version, Coverage)。
    - 更新核心功能列表 (Features)，移除已废弃功能的描述。
    - 检查 "Quick Start" 命令是否依然有效。

#### 2. 用户层 (User Layer)
- [ ] **USER_MANUAL.md**: 
    - **UI截图**: 若 UI 布局变更（如新按钮、新布局），必须替换对应截图。
    - **参数说明**: 检查配置项说明是否与代码中的 `rag_config.json` 默认值一致。
- [ ] **FAQ.md**: 针对本次更新可能引发的常见疑问（如：为什么原来的按钮不见了？），预置 Q&A。

#### 3. 技术层 (Technical Layer)
- [ ] **INTERFACE_SUMMARY.md**: 更新模块统计、API 端点列表。
- [ ] **API_DOCUMENTATION.md**: 若 API 参数或返回值变更，必须同步 Swagger/OpenAPI 定义或 Markdown 描述。
- [ ] **ARCHITECTURE.md**: 若引入了新的中间件（如 DuckDuckGo, Redis），需更新架构图。

---

### 第三阶段：逻辑审计与深度清理 (Audit & Deep Cleanup)

#### 1. 术语一致性审计 (Terminological Consistency)
确保以下三处使用的术语完全一致（100% Match）：
- **UI 界面**: 用户看到的 Label (e.g., "联网搜索", "深度思考").
- **代码变量**: 关键配置项 Key (e.g., `enable_web_search`, `enable_deep_think`).
- **文档描述**: 用户手册中的用词 (e.g., "联网搜索 (Web Search)", "深度思考 (Deep Think)").

**v2.8.0 核心术语检查清单**:
- [ ] 联网搜索 / Web Search / enable_web_search
- [ ] 深度思考 / Deep Think / enable_deep_think  
- [ ] 功能工具栏 / Function Toolbar / toolbar_enabled
- [ ] 动态配置 / Dynamic Config / dynamic_model_selection

#### 2. 深度清理 (Standardized Cleanup)
执行比自动化脚本更严格的手动检查：

**🗑️ 物理删除清单 (Delete Immediately)**:
- **过期版本摘要**: 如 `DOCUMENTATION_UPDATE_SUMMARY_v2.6.x.md`。
- **开发过程文档**: 如 `REFACTOR_PLAN.md`, `TODO_LIST.md`, `scratchpad.txt`。
- **冗余测试输出**: 如 `temp_test_output/`, `*.log`, `ocr_debug/`。
- **草稿文件**: 任何以 `draft_` 或 `temp_` 开头的文件。

**✅ 保留清单 (Keep)**:
- 核心门面文档 (`README`, `LICENSE`)
- 用户文档 (`USER_MANUAL`, `FAQ`)
- 技术标准文档 (`API`, `ARCHITECTURE`)
- 工程治理文档 (`*_STANDARD.md`)

#### 3. 提交前最终检查 (Pre-Commit Check)
- 运行 `git diff --staged` 逐行审查本次提交的内容。
- 确保没有意外删除核心逻辑代码。
- 确保没有将 `config/users.json` 或 `secrets.key` 等敏感文件加入暂存区。

---

## 3. 交付反馈报告 (Final Audit Report)

任务完成后，必须输出以下格式的报告，作为 Release Note 的一部分：

```markdown
### ✅ 全量同步与清理报告

**版本**: [vX.Y.Z] (当前: v2.8.0)
**审计人**: [Role/Name]

#### 1. 变更摘要 (Summary)
- **核心变更**: [一句话描述，如：集成联网搜索与深度思考查询优化模块]
- **文档同步**: [已完成/有遗留]

#### 2. 一致性检查 (Consistency Checklist)
- [ ] 版本号 (Version Tag): [vX.Y.Z]
- [ ] UI/文档术语对齐 (Terminology Match)
- [ ] 敏感信息扫描 (Security Check)
- [ ] v2.8.0 核心功能术语检查 (联网搜索、深度思考、功能工具栏)

#### 3. 遗留问题/风险 (Risks)
- [如有，请列出；无则填 None]

**结论**: 项目已达到交付标准，准备推送。
```