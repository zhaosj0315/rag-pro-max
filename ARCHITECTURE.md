# RAG Pro Max v9.7.0 Unified Governance & Monitoring Edition 架构白皮书

**版本**: v9.7.0 (Unified Governance & Monitoring Edition)  
**更新日期**: 2026-01-30  
**核心特性**: Governance & Monitoring Fusion, Panoramic Log System, Minimalist UI, Omni-Append

---

## 🏗️ 顶层逻辑：三核驱动架构 (Triple-Core Drive)

在 v9.5.38 中，系统从传统的单核 RAG 演进为三核协同模式，所有流量受 `Iron-Gate Routing` 严选。

### 1. 语义核 (Semantic Core) - RAG Engine
- **基础检索**: 基于 `vector_db_storage` 执行向量相似度检索。
- **混合增强**: 支持 BM25 与向量重排序的混合路径。

### 2. 逻辑核 (Logical Core) - Data Analyst Engine
- **SQL 推演**: 针对结构化物料（CSV/SQL），将自然语言转化为 SQL 并在本地 SQLite 中执行。
- **铁闸准入**: 只有当 KB 包含 `business_schema.json` 且用户开启“数据分析”开关时才激活。

### 3. 协同核 (Synergy Core) - Smart Agents
- **Precise Query (精准提问)**: 替代了旧版的 Deep Thinking。在提问阶段，调用 LLM 对用户原始意图进行重写（Rewrite）与扩展，解决用户表达模糊的问题。
- **Unified Suggestion Engine**: 负责生成“后续追问”。引入 **Grounding Check** 机制，生成的每一个问题都会预先跑一遍 RAG 检索，确保这些问题在当前库中是有答案的。

---

## 🏗️ 系统管理与监控架构 (System Management & Monitoring)

v9.7.0 引入了极其严格的“治理优先”架构，将所有敏感的系统级操作与监控功能从前台剥离，降维收纳至后台资源治理中心。

### 1. 资源治理中心 (Resource Governance Hub)
- **定位**: 系统的最高管理权力中心，仅 Admin 角色可见。
- **模块融合**:
    - **Asset Governance**: 知识库的物理管理（删除、迁移、重命名）。
    - **Real-time Monitoring**: 实时系统负载监控（CPU/Mem/Response），采用 JS 驱动的 5秒倒计时机制。
    - **Intelligent Scheduling**: 核心调度参数与并发控制。
    - **Panoramic Logs**: 行为审计与系统日志的深度融合。

### 2. 全景日志系统 (Panoramic Log System)
- **Dual-View Architecture**: 采用双视图设计。
    - **View A (Audit)**: 基于 `AuditLogger` 的结构化行为追踪（Who, When, What）。
    - **View B (System)**: 基于 `CompactLogDisplay` 的底层运行日志（Error, Warning, Info）。
- **Strategic Dashboard**: 顶层集成了战略仪表盘，提供流量趋势与资产概况的宏观视角。

---

## 🏗️ 全源归一化摄入管线 (Omni-Ingestion Pipeline)

### 1. 归一化摄入中心 (Unified Ingestor)
- **入口统一**: `src/ui/unified_ingestion.py` 统筹 5 大源头：文件/目录、文本粘贴、网页抓取、数据库快照。
- **暂存解耦**: 
    - **Creation Staging**: `temp_uploads`。
    - **Append Staging**: `vector_db_storage/<kb>/append_staging`。

### 2. 物理自愈与审计
- **Meta-Shielding (审计屏蔽)**: 每一份源文件均配有 `.meta` 伴生文件记录溯源信息。`IndexBuilder` 内置过滤器，确保审计文件不进入向量索引。
- **Atomic Commit (原子提交)**: 
    - **Incremental Append**: 将暂存区文件移动至 `raw_sources/`，仅对差异部分进行增量索引。
    - **Full Rebuild**: 物理合并后，触发全量 `NEW` 模式构建，彻底重置索引。

---

## 🏗️ 交互增强：归一化建议引擎 (Normalized Suggestion Engine)

为了解决“僵尸建议”问题，v9.5.38 确立了 `UnifiedSuggestionEngine` 的正统地位：

- **Multi-Strategy Model**:
    1. **Custom Strategy**: 优先展示用户在 `manifest.json` 中预设的引导问题。
    2. **LLM Strategy**: 结合对话历史，由大模型生成关联性问题。
    3. **Source Strategy**: 从最近检索到的文档块中提取实体和关键词进行生成。
- **Grounding Check (落地校验)**: 这是系统的核心防御。所有候选问题必须通过一次后台 RAG 模拟测试（`_can_answer_from_kb`），无法回答的问题将被丢弃。

---

## 🏗️ 归一化摄入管线图 (Updated Mermaid)

```mermaid
graph TD
    A[📂 文件/目录/粘贴] --> N[归一化摄入中心]
    B[🌐 网页/搜索] --> N
    C[🗄️ 数据库快照 (CSV)] --> N
    
    N --> S[暂存区 Staging Area]
    S -.-> M[.meta 审计文件]
    
    S --> I[IndexBuilder]
    M -- "Shielding" --> X[屏蔽过滤]
    
    I --> R[<b>RAG 核心管线</b>]
    R --> PQ[Precise Query 提问增强]
    
    PQ --> D{勾选: 数据分析?}
    D -- "True" --> DA[<b>SQL 核心管线</b>]
    D -- "False" --> RG[<b>语义检索管线</b>]
    
    RG --> SE[Unified Suggestion Engine]
    SE -- "Grounding Check" --> F[三路高质后续追问]
```
