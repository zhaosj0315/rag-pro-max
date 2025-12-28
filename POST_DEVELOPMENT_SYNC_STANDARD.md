# 项目全量同步、对齐与清理标准 (Post-Development Synchronization Standard)
**版本**: v1.0.0  
**类型**: 工程管理规范  
**适用阶段**: 开发完成 (Code Freeze) 后，发布/推送前

---

## 🎯 核心原则 (Core Principles)

1.  **代码即真理 (Code is Truth)**: 代码库一旦锁定，即为最终事实标准。所有文档必须向代码现状看齐，严禁修改代码以适配文档。
2.  **全量对齐 (Full Alignment)**: 不允许存在“代码已更新但文档未更新”的灰色地带。
3.  **非必要不保留 (Minimalism)**: 交付物必须纯净，所有过程性、临时性文件必须物理删除。

---

## 1. 锚定当前事实 (Phase 1: Anchor Truth)

在执行同步前，必须明确以下三个基准：

- **🔒 代码锁定**: 确认所有功能代码已提交，不再进行任何逻辑修改。
- **🏷️ 版本确立**: 确定本次发布的最终版本号 (e.g., `v2.7.2`)。
- **📝 变更范围**: 明确本次迭代的核心逻辑变更点（Core Changes）。

---

## 2. 三步走执行路径 (Phase 2: Execution Workflow)

### 第一阶段：全量同步 (Full Synchronization)
必须按照以下四个维度顺序检查并更新文档：

#### 1. 配置层 (Configuration Layer)
- [ ] **version.json**: 更新 `version` 字段，确保与锚定版本一致。
- [ ] **.gitignore**: 检查是否有新增的临时文件类型或敏感配置需忽略。

#### 2. 记录层 (Record Layer)
- [ ] **README.md**: 更新版本徽章 (Badges)、更新核心功能列表、更新最新更新日期。
- [ ] **CHANGELOG.md**: 按照 `[版本号] - 日期` 格式，详细记录新增功能、修复 Bug 和技术改进。

#### 3. 用户层 (User Layer)
- [ ] **USER_MANUAL.md**: 若 UI 或操作流程有变，必须更新对应章节截图或文字说明。
- [ ] **FAQ.md**: 若引入新机制可能导致用户困惑，需新增 Q&A。
- [ ] **FIRST_TIME_GUIDE.md**: 确保新手引导流程与当前版本启动逻辑一致。

#### 4. 技术层 (Technical Layer)
- [ ] **INTERFACE_SUMMARY.md**: 更新模块统计、API 端点列表及文件结构树。
- [ ] **API_DOCUMENTATION.md**: 若 API 参数或返回值变更，必须同步。
- [ ] **TESTING.md**: 更新测试覆盖率数据、新增测试用例说明。
- [ ] **ARCHITECTURE.md**: 若系统架构或数据流发生变化，需更新架构图或描述。

---

### 第二阶段：逻辑与标准对齐 (Logic & Standard Alignment)

#### 1. 术语一致性审计 (Terminological Consistency)
确保以下三处使用的术语完全一致（100% Match）：
- **UI 界面**: 用户看到的按钮、标签名称 (e.g., "OCR识别").
- **代码变量**: 关键配置项或变量名 (e.g., `use_ocr`).
- **文档描述**: 用户手册或注释中的用词 (e.g., "OCR文字识别").

#### 2. 测试对齐 (Test Alignment)
- 若新增了功能代码，必须确认已添加对应的测试脚本（如 `tests/test_new_feature.py`）。
- 必须在 `TESTING.md` 中记录新测试脚本的用途和覆盖范围。

#### 3. 规范审计 (Standard Audit)
- 检查代码和文档是否符合 `DEVELOPMENT_STANDARD.md`（开发规范）。
- 检查是否符合 `NON_ESSENTIAL_PUSH_STANDARD.md`（推送规范）。

---

### 第三阶段：深度清理 (Standardized Cleanup)

严格执行 `DEVELOPMENT_CLEANUP_STANDARD.md`，执行“保留”与“删除”操作：

#### ✅ 保留清单 (Keep)
- 核心门面文档 (`README`, `LICENSE`)
- 用户文档 (`USER_MANUAL`, `FAQ`)
- 技术标准文档 (`API`, `ARCHITECTURE`)
- 工程治理文档 (`*_STANDARD.md`)

#### 🗑️ 物理删除清单 (Delete)
- **过期版本摘要**: 如 `DOCUMENTATION_UPDATE_SUMMARY_v2.6.x.md`。
- **开发过程文档**: 如 `REFACTOR_PLAN.md`, `TODO_LIST.md`。
- **冗余测试输出**: 如 `temp_test_output/`, `*.log`。
- **草稿文件**: 任何以 `draft_` 或 `temp_` 开头的文件。

#### 🔍 瘦身确认 (Git Staging)
- 运行 `git status`，确保暂存区（Staging Area）只包含当前版本必须的、且已清洗干净的资产。

---

## 3. 交付反馈报告 (Final Audit Report)

任务完成后，必须输出以下格式的报告：

```markdown
### ✅ 全量同步与清理报告

**版本**: [版本号]
**状态**: [已对齐/待修正]

#### 1. 更新列表 (Updated)
- [文件名]: [修改点简述] (例如：README.md: 更新版本至 v2.7.2，新增 OCR 功能说明)
- [文件名]: [修改点简述]

#### 2. 删除清单 (Deleted)
- [文件名]: [删除原因] (例如：*_v2.6.1.md: 过期过程文档)

#### 3. 一致性状态 (Consistency Status)
- [ ] 版本号统一 (Version Tag)
- [ ] 术语对齐 (Terminology)
- [ ] 逻辑闭环 (Logic Check)

**结论**: 项目已达到交付标准，准备推送。
```
