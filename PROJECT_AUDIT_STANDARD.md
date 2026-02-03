# RAG Pro Max 项目里程碑全量审计标准 (Audit Standard)

**版本**: v9.8.0 (DA-ECP Edition)
**适用范围**: 每次主版本升级 (Major/Minor Update)
**执行官**: 项目审计员 (或自动化 Agent)

## 5. DA-ECP V4.5 协议闭环 (Deep Understanding)
- [ ] **全息日志**: 构建过程中终端是否显示了 `📦` (Solid) 和 `📐` (Virtual) 图标？
- [ ] **动静分离**: 构建完成后，`business_data.db` 是否**未包含**虚拟表的模拟数据？
- [ ] **JIT 触发**: 在回答涉及虚拟表的问题时，日志中是否出现了 `🎲 正在为 X 个表生成虚拟数据`？
- [ ] **Schema 完整性**: `business_schema.json` 是否包含 `stats`, `enums` 和 `is_virtual` 字段？

## 1. 需求与交互闭环 (UX Alignment)
- [ ] **全源一致性**: 检查侧边栏是否已彻底移除独立的“数据库同步”入口，确保所有摄入操作均通过 Omni 面板完成。
- [ ] **审计闭环**: 检查暂存区文件是否 100% 配备了对应的 `.meta` 伴生文件。
- [ ] **预览闭环**: 验证 macOS 环境下点击 `👁️` 是否能成功唤起 `qlmanage` 并置顶。
- [ ] **零白屏**: 验证所有开关与配置切换是否均为 Fragment 局部刷新。

## 2. 代码与文档闭环 (Documentation Consistency)
- [ ] `version.json` 中的版本号 (v9.8.0) 与 `README.md` 是否 100% 对应？
- [ ] `USER_MANUAL.md` 是否已更新“暂存区治理中心”的四维操作指引？
- [ ] 核心架构图 (`ARCHITECTURE.md`) 是否已包含“Level 0 暴力探测”逻辑？

## 3. 架构与实现闭环 (Architecture Traceability)
- [ ] 新增的物理目录（如 `task_staging_dir`）是否已在架构文档中注册？
- [ ] **暴力探测**: 是否已在 `apppro.py` 中物理嵌入了正则提取逻辑？
- [ ] **元数据屏蔽**: 是否确认 `IndexBuilder` 包含 `not f.endswith('.meta')` 过滤逻辑？

## 4. 安全与隔离闭环 (Security Guard)
- [ ] 新产生的数据目录是否已加入 `.gitignore`？
- [ ] `DATA_SOVEREIGNTY_WHITEPAPER.md` 是否已声明“审计文件不入库”原则？

---
*注：任何一项未达成，均视为审计不通过，禁止发布正式 Release。*