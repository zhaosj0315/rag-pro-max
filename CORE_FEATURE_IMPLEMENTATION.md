# RAG Pro Max 核心功能实现详述 (Core Feature Implementation)

**版本**: v9.1.0 (Flagship Evolution)
**状态**: 关键性资产 (永久保存)
**描述**: 本文档记录了 v9.1「极致性能」优化、v9.0「全能摄入」逻辑及 v8.9「精准抓取」架构的底层实现、协同算法及物理闭环规范。

---

## ⚡ 1. 极致 UI 性能优化 (UI Performance Hardening)
v9.1.0 对表现层执行了深度手术，解决了 Streamlit 传统的刷新延迟痛点，实现了“零白屏”交互。

### 技术实现细节 (Technical Specs)
1. **组件级局部刷新 (Fragment Isolation)**:
   - 深度应用 `@st.fragment` 装饰器，将工具栏、功能开关及数据源配置区域包装为独立生命周期单元。
   - 内部状态变更（如切换联网搜索、勾选全选）仅触发局部 DOM 更新，绕过整页重绘流程。
2. **对话流无缝衔接 (Seamless Chat Pipeline)**:
   - **去重载调度**: 彻底移除了核心调度器 (`Core Scheduler`) 中用于状态同步的 `st.rerun()` 调用。
   - **原地增量渲染**: 移除了回答生成结束后的刷新指令。通过手动渲染建议按钮并配合**稳定 Key 映射算法** (`dyn_sug_{msg_hash}`)，实现了输出结束与后续交互的瞬间转换。
3. **变量作用域稳健性**: 实施了全局初始化策略，解决了引入局部刷新后 `btn_start` 等变量在主进程中“失踪”的问题。

---

## 💬 2. 纯对话模式深度解耦 (Pure Chat Decoupling)
剥离了轻量级聊天对重型知识库引擎的硬编码依赖。

- **Filesystem-Agnostic**: 识别 `active_kb_name == 
## 📥 3. 全源归一化摄入 (Omni-Ingestion Implementation)
v9.5.1 实现了“一切皆源文件”的终极架构，废弃了特殊的“数据库同步”模式。

### 核心引擎：`DatabaseExporter`
- **定位**: 位于 `src/processors/database_exporter.py`，是连接 SQL 世界与文件世界的桥梁。
- **流式物料化 (Streaming Materialization)**:
  - 采用 `pd.read_sql(..., chunksize=N)` 迭代器模式。
  - 逐块将查询结果写入 CSV 文件，确保内存占用恒定，不随数据量线性增长。
- **自定义 SQL 适配**:
  - 支持直接执行用户输入的 Raw SQL。
  - 自动为结果集生成带时间戳的 CSV 文件名 (`[SQL]QueryName_Timestamp.csv`)。
- **元数据伴生**:
  - 每次导出均会生成 `.meta` 伴生文件，记录 SQL 来源、执行时间与行数，为后续的数据血缘追踪提供物理依据。

### 物理暂存区 (Staging Area)
- **统一汇聚**: 无论是 PDF 上传、网页抓取还是数据库导出，所有产物最终都表现为 `task_staging_dir` 下的物理文件。
- **原子化构建**: `IndexBuilder` 不再感知数据来源，仅需扫描暂存区即可完成混合索引构建，极大降低了系统复杂度。
