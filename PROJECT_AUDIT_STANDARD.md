# RAG Pro Max 项目里程碑全量审计标准 (Audit Standard)

**适用范围**: 每次主版本升级 (Major/Minor Update)
**执行官**: 项目审计员 (或自动化 Agent)

## 1. 需求与交互闭环 (UX Alignment)
- [ ] 界面上的所有按钮是否都有对应的代码逻辑实现？
- [ ] 所有的“并集逻辑”是否都有明确的文件计数反馈？
- [ ] **全源一致性**: 检查侧边栏是否已彻底移除独立的“数据库同步”入口，确保所有摄入操作均通过 Omni 面板完成。
- [ ] **审计闭环**: 检查暂存区文件是否 100% 配备了对应的 `.meta` 伴生文件。
- [ ] 错误提示是否具有“自愈指引”？

## 2. 代码与文档闭环 (Documentation Consistency)
- [ ] `version.json` 中的版本号与 `README.md` 是否 100% 对应？
- [ ] `USER_MANUAL.md` 中的截图/步骤描述是否与当前 UI 布局一致？
- [ ] 代码中的“隐藏 Bug 修复”是否已同步至 `CHANGELOG.md`？

## 3. 架构与实现闭环 (Architecture Traceability)
- [ ] 新增的物理目录（如 `task_staging_dir`）是否已在 `ARCHITECTURE.md` 中注册？
- [ ] 所有的逻辑变更是否都附带了对应的 `ADR` 记录？

## 4. 安全与隔离闭环 (Security Guard)
- [ ] 新产生的数据目录是否已加入 `.gitignore`？
- [ ] `.LOCAL_ASSETS_PROTECTION.md` 是否已更新以覆盖新资产？

---
*注：任何一项未达成，均视为审计不通过，禁止发布正式 Release。*
