# 🗺️ RAG Pro Max 代码全典 (Code Index)

> **审计状态**: 已同步至 v9.7.0 (Unified Governance Edition)  
> **外部审计员备注**: 严禁将 [OBSOLETE] 模块用于生产逻辑。

## 目录结构

### 📄 src/apppro.py
- **📝 核心逻辑**: 系统主入口，集成了三核路由 (`Iron-Gate Routing`) 与 UI 渲染。
- **🏗️ 架构变更**: [v9.7.0] 移除了所有前端监控逻辑 (`tab_monitor`)，将其降维迁移至后台治理中心。
- **⚡ 关键函数**:
  - `def suggestions_fragment`: [v9.5.38] 追问组件，调用 `UnifiedSuggestionEngine` 实现高质后续追问。
  - `def process_knowledge_base_logic`: 处理知识库逻辑 (使用 `IndexBuilder`)。
  - `def enhanced_web_search`: 增强的联网搜索功能。

### 📄 src/auth/resource_governance.py
- **📝 描述**: **[CORE]** 全域资源治理中心。v9.7.0 之后，此处是系统唯一的管理与监控中枢。
- **⚡ 关键集成**:
  - **Monitoring Integration**: 融合了 `RealtimeMonitor` 面板，提供单行 5 列的极简监控视图。
  - **Scheduling Control**: 接管了智能调度器的前端交互逻辑。
  - **Panoramic Logs**: 集成了审计与终端日志的双视图管理。

---

### 📄 src/ui/unified_ingestion.py
- **📝 描述**: **[CORE]** 全能采集统一组件。系统唯一的资料摄入枢纽。
- **⚡ 关键能力**:
  - **Five-Source Ingestion**: 统筹本地文件、递归目录、文本粘贴、网页抓取、数据库快照。
  - **Staging Management**: 维护 `temp_uploads` 与 `append_staging` 两个物理隔离的缓冲区。
  - **Advanced Options**: 统揽 OCR、Metadata、Reindex、Data Analysis、Summary 五大构建参数。

---

### 📄 src/chat/unified_suggestion_engine.py
- **📝 描述**: **[CORE]** 归一化建议引擎。
- **🏗️ 核心算法**:
  - **Grounding Check**: 引入 `_can_answer_from_kb` 逻辑，在返回追问建议前执行后台 RAG 模拟，确保问题 100% 可被知识库回答。
  - **Hybrid Strategy**: 融合用户预设 (Manifest)、LLM 实时推理与文档实体提取。

---

### 📄 src/query/query_processor.py
- **📝 描述**: **[OBSOLETE / TEST-ONLY]**
- **警告**: 此模块在 v9.5.x 架构中已被 `rag_engine.py` 取代。主程序不再引用，目前仅保留用于兼容旧版单元测试。**请勿在任何业务流中使用。**

---

### 📄 src/auth/session_manager.py
- **📝 描述**: 会话与安全性管理。
- **⚡ 关键功能**:
  - `def validate_session`: 支持基于 URL Query Parameter (`?session_token=`) 的身份验证与会话持久化。
  - `def get_visible_kbs`: 实现细粒度的 RBAC 资源可见性过滤。

---

### 📄 src/common/business.py
- **📝 描述**: 业务逻辑中转站。
- **⚡ 关键函数**:
  - `def click_btn`: 实现追问按钮的点击反馈逻辑，确保与 `suggestions_history` 的原子级交互。

---

### 📄 src/processors/index_builder.py
- **📝 描述**: 索引构建核心。
- **⚡ 关键逻辑**:
  - **Meta-Shielding**: 构建扫描时自动忽略 `.meta` 审计文件，防止溯源信息污染向量空间。
  - **Action Mode**: 支持 `APPEND` (增量) 与 `NEW` (全量重建) 两种构建模式。
