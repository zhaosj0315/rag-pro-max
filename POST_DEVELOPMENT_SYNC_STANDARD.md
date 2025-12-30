# 项目全量同步、对齐与清理标准 (Post-Development Synchronization Standard)



**版本**: v3.2.1 (Expert Reviewed)  
**更新日期**: 2025-12-30
**类型**: 工程管理规范
**适用阶段**: 开发完成 (Code Freeze) 后，发布/推送前
**执行角色**: Release Manager / Tech Lead

------

## 🎯 核心原则 (Core Principles)



1. **代码即真理 (Code is Truth)**: 代码库一旦锁定，即为最终事实标准。所有文档必须向代码现状看齐，严禁反向修改代码以适配文档。
2. **全量对齐 (Full Alignment)**: 不允许存在“代码已更新但文档未更新”的灰色地带。
3. **零噪交付 (Zero Noise)**: 交付物必须纯净，所有过程性、临时性文件必须物理删除或归档。
4. **自动化优先 (Automation First)**: 凡是可以通过脚本验证的检查项，必须优先使用脚本执行。

------

## 1. 锚定当前事实 (Phase 1: Anchor Truth)



在执行同步前，必须明确以下三个基准：

- **🔒 代码锁定 (Code Freeze)**: 确认所有功能分支已合并，本地工作区干净 (`git status` clean)，不再进行逻辑变更。
- **🏷️ 版本确立 (Versioning)**: 严格遵循 [SemVer 2.0](https://semver.org/) 规范确定版本号 (e.g., `v2.8.0`)。
- **📝 变更范围 (Scope)**: 明确本次迭代的核心逻辑变更点（Core Changes），区分 "Feature", "Fix", "Refactor"。

------

## 2. 三步走执行路径 (Phase 2: Execution Workflow)



### 第一阶段：自动化验证与配置同步 (Automated Verification)



利用项目内置脚本进行初筛，确保低级错误被拦截。

#### 1. 脚本扫描 (Script Execution)



-  **文档同步检查**: 运行 `./scripts/check_docs_sync.sh` (如有) 或相关检查脚本，扫描文档中的版本号是否滞后。
-  **清理脚本执行**: 运行 `bash ./scripts/cleanup.sh`，自动清理 `__pycache__`, `.DS_Store`, 临时日志等。

#### 2. 配置层 (Configuration Layer)



-  **version.json**: 更新 `version` 字段，确保与锚定版本一致。
-  **.gitignore**: 检查是否有新增的临时文件类型或敏感配置需忽略。使用 `git check-ignore -v <file>` 验证关键文件是否被正确忽略。

------

### 第二阶段：全量文档同步 (Documentation Synchronization)



必须按照以下四个维度顺序检查并更新文档：

#### 1. 记录层 (Record Layer)



-  

  CHANGELOG.md

  :

  - 按照 `[版本号] - 日期` 格式记录。
  - 分类记录：`🚀 New`, `⚡ Improvement`, `🐛 Fix`, `🔧 Refactor`。
  - **关键**: 必须包含 Breaking Changes 的显式警告。

-  

  README.md

  :

  - 更新顶部 Badges (Version, Coverage)。
  - 更新核心功能列表 (Features)，移除已废弃功能的描述。
  - 检查 "Quick Start" 命令是否依然有效。

#### 2. 用户层 (User Layer)



-  

  USER_MANUAL.md

  :

  - **UI截图**: 若 UI 布局变更（如新按钮、新布局），必须替换对应截图。
  - **参数说明**: 检查配置项说明是否与代码中定义的默认配置值 (e.g., `src/core/app_config.py` 中的 `defaults`) 一致。

-  **FAQ.md**: 针对本次更新可能引发的常见疑问（如：为什么原来的按钮不见了？），预置 Q&A。

#### 3. 技术层 (Technical Layer)



-  **INTERFACE_SUMMARY.md**: 更新模块统计、API 端点列表。
-  **API_DOCUMENTATION.md**: 若 API 参数或返回值变更，必须同步 Swagger/OpenAPI 定义或 Markdown 描述。
-  **ARCHITECTURE.md**: 若引入了新的中间件（如 DuckDuckGo, Redis），需更新架构图。

------

### 第三阶段：逻辑审计与深度清理 (Audit & Deep Cleanup)



#### 1. 术语一致性审计 (Terminological Consistency)



确保以下三处使用的术语完全一致（100% Match）：

- **UI 界面**: 用户看到的 Label (e.g., "联网搜索", "深度思考").
- **代码变量**: 关键配置项 Key (e.g., `enable_web_search`, `enable_deep_think`).
- **文档描述**: 用户手册中的用词 (e.g., "联网搜索 (Web Search)", "深度思考 (Deep Think)").

**v2.8.0 核心术语检查清单 (示例/当前版本重点)**:
*(注：新版本发布时需在此处更新当期核心功能的关键术语)*

-  联网搜索 / Web Search / enable_web_search
-  深度思考 / Deep Think / enable_deep_think
-  功能工具栏 / Function Toolbar / toolbar_enabled
-  动态配置 / Dynamic Config / dynamic_model_selection

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

------

## 4. 多轮专家审查协议 (Multi-Round Expert Review Protocol)



为了确保逻辑一致性和交付质量，执行严格的**十人五轮**审查机制。这不一定需要十个不同的人，而是要求审查者戴上十顶不同的“专家帽”进行五轮深度遍历。

### 🎩 十位虚拟专家角色 (The 10 Expert Personas)

1.  **🏗️ 架构师 (System Architect)**: 审查模块依赖、架构图一致性、代码结构完整性。
2.  **🛡️ 安全审计员 (Security Auditor)**: 扫描敏感信息泄露、权限漏洞、依赖库风险。
3.  **⚡ 性能工程师 (Performance Engineer)**: 检查资源泄露、潜在的 IO 瓶颈、启动时间劣化。
4.  **🎨 UI/UX 专家 (UI/UX Specialist)**: 验证界面文案一致性、布局回退、交互逻辑闭环。
5.  **📝 文档官 (Doc Specialist)**: 确保 README/手册与代码 1:1 对应，无歧义、无死链。
6.  **🧪 QA 负责人 (QA Lead)**: 确认测试覆盖率、边缘用例覆盖、Bug 修复验证。
7.  **🚀 DevOps 工程师 (DevOps Engineer)**: 验证 Docker 构建、部署脚本、环境变量配置。
8.  **💼 产品经理 (Product Owner)**: 确认功能完整性、业务价值交付、版本变更日志准确性。
9.  **⚖️ 合规专员 (Compliance Officer)**: 检查开源协议冲突、引用规范、版权声明。
10. **🧹 代码洁癖者 (Clean Code Advocate)**: 审查命名规范、注释质量、废弃代码清理。

### 🔄 五轮审查流程 (The 5-Round Review Cycle)

#### 第一轮：静态与基础 (Round 1: Static & Foundation)
- **参与专家**: 🏗️ 架构师, 🛡️ 安全审计员, 🚀 DevOps 工程师
- **关注点**: 代码能否通过编译/Lint？脚本能否跑通？是否有明文密钥提交？
- **动作**: 执行所有自动化检查脚本 (`check_push.sh`, `test.sh`)。

#### 第二轮：逻辑与功能 (Round 2: Logic & Functionality)
- **参与专家**: 💼 产品经理, 🧪 QA 负责人, ⚡ 性能工程师
- **关注点**: 核心功能（如联网搜索、深度思考）是否符合逻辑预期？是否存在死循环或逻辑断路？
- **动作**: 手动走查核心业务流程，模拟极端输入。

#### 第三轮：体验与一致性 (Round 3: Experience & Consistency)
- **参与专家**: 🎨 UI/UX 专家, 📝 文档官
- **关注点**: "界面上写的" vs "文档里写的" vs "代码里做的" 是否三位一体？
- **动作**: 对照 `USER_MANUAL.md` 操作软件，寻找任何不一致之处。

#### 第四轮：代码与规范 (Round 4: Code & Standards)
- **参与专家**: 🧹 代码洁癖者, ⚖️ 合规专员
- **关注点**: 代码风格是否统一？TODO 是否已清理？引用是否合规？
- **动作**: 深度 Code Review，查阅 `DEVELOPMENT_STANDARD.md` 对齐情况。

#### 第五轮：终局验收 (Round 5: Final Sign-off)
- **参与专家**: 🏗️ 架构师 (回归), 💼 产品经理 (回归)
- **关注点**: 前四轮发现的问题是否已修正？是否准备好发布？
- **动作**: 签署发布确认，打 Tag。

------

## 5. 交付反馈报告 (Final Audit Report)



任务完成后，必须输出以下格式的报告，作为 Release Note 的一部分：

```
### ✅ 全量同步与清理报告 (Expert Reviewed)

**版本**: [vX.Y.Z] (当前: v2.8.0)
**执行人**: [Role/Name]

#### 1. 变更摘要 (Summary)
- **核心变更**: [一句话描述]
- **文档同步**: [已完成]

#### 2. 五轮审查概览 (5-Round Review Status)
- [ ] Round 1 (Static/Sec): Pass
- [ ] Round 2 (Logic/Func): Pass
- [ ] Round 3 (UI/Doc): Pass
- [ ] Round 4 (Code/Std): Pass
- [ ] Round 5 (Final): Pass

#### 3. 核心一致性检查 (Consistency Checklist)
- [ ] 术语一致性 (UI vs Doc vs Code)
- [ ] 敏感信息零残留 (Security)
- [ ] 临时文件全清理 (Zero Noise)

#### 4. 遗留风险 (Risks)
- [None / Describe Risk]

**结论**: 项目已通过 10 角色 5 轮次审查，准予发布。
```

------

## 6. 推送决策与执行 (Phase 4: Push Decision & Execution)

### 推送必要性评估

完成全量同步后，必须按照 **[NON_ESSENTIAL_PUSH_STANDARD.md](NON_ESSENTIAL_PUSH_STANDARD.md)** 的"非必要不推送"原则进行最终评估：

#### 评估流程
1. **变更性质分析**: 区分核心功能变更 vs 文档同步 vs 代码优化
2. **用户影响评估**: 评估变更对最终用户的实际影响
3. **推送必要性判断**: 
   - 🔴 **必须推送**: 核心功能、安全修复、关键Bug修复
   - 🟡 **建议推送**: 用户体验改进、文档完整性、性能优化
   - 🟢 **可选推送**: 代码重构、注释更新、内部优化

#### 推送执行
```bash
# 1. 最终检查
git status  # 确保工作区干净
git log --oneline -5  # 确认提交历史

# 2. 按需推送
git push origin main  # 仅在通过必要性评估后执行
```

### 推送后验证
- [ ] 远程仓库状态确认
- [ ] CI/CD 流水线状态检查
- [ ] 部署环境验证（如适用）

------

## 📚 相关标准文档

- [NON_ESSENTIAL_PUSH_STANDARD.md](NON_ESSENTIAL_PUSH_STANDARD.md) - 非必要不推送原则
- [DEVELOPMENT_CLEANUP_STANDARD.md](DEVELOPMENT_CLEANUP_STANDARD.md) - 开发清理标准
- [DOCUMENTATION_MAINTENANCE_STANDARD.md](DOCUMENTATION_MAINTENANCE_STANDARD.md) - 文档维护标准

---

**遵循此标准，确保每次发布的质量和一致性** 🚀
