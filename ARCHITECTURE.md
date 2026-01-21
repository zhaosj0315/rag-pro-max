# RAG Pro Max v8.1.3 企业级系统架构文档

**版本**: v8.1.3 (Flagship Dual-Core Edition)  
**更新日期**: 2026-01-20  
**核心特性**: Full-Link Audit, Logic Core Hardening, Minimalist UI Fusion

---

## 🧠 业务层内核加固 (Service Layer Hardening)

在 v8.1.2/v8.1.3 中，数据分析引擎 (`src/processors/data_analyst.py`) 经历了深度逻辑增强：

- **Dual-Logging Architecture**: 实现了终端标准输出与文件结构化日志的“双写同步”，确保每一行执行逻辑都可被审计。
- **Atomic Decomposition**: 引入原子化拆解 Prompt，强制 Planner 遵循 DAG（有向无环图）执行逻辑。
- **Precision Schema Linking**: 在选表阶段注入 "Fact-First" 与 "Time-Aligned" 决策权重。
- **Zero-Row Diagnostics**: 建立执行后验回路，自动识别并诊断 `JOIN` 关联失效导致的空结果集。

---

## 🏗️ 表现层架构融合 (v8.1.1)

在 v8.1.1 中，表现层（Presentation Layer）经历了深度重构，实现了**入口逻辑的归一化**。

- **单一入口原则**: 废弃了基于 `main_mode` 的多页面分发逻辑（Legacy）。
- **配置下沉**: 将“数据分析”从顶级导航下沉为 `IndexBuilder` 的配置参数 `enable_data_analysis`。
- **状态流转**: 侧边栏不再负责复杂的模式切换，仅负责参数收集与任务触发。

---

## 🧬 双核组装与严选路由 (v8.1.0)

在 v8.1.0 迭代中，系统确立了“能力预装 (Provisioning)”与“实时激活 (Activation)”相分离的顶层架构模式。

### 1. 意图严选路由 (Iron-Gate Routing)
为了防止 SQL 引擎对定性查询的“逻辑干扰”，系统在提问主循环中实施了防御式网关：
- **物理判定 (`is_data_kb`)**: 检查 KB 目录是否存在 `business_schema.json`。
- **意图判定 (`manual_da_on`)**: 实时监听 Session State 中的数据分析开关。
- **铁闸决策**: 只有当 `is_data_kb AND manual_da_on` 为真时，流量才允许流向逻辑核（SQL 推演）。否则，一律默认路由至语义核（RAG 检索）。

### 2. 归一化摄入不变式 (Normalized Invariants)
不论摄入源头如何变化，构建管线必须满足以下物理闭环：
- **RAG 基准**: 必须生成 `docstore.json` 与 `index_store.json`。
- **影子库可选**: 仅在用户勾选增强项时生成 `.db` 物理库。
- **元数据归口**: 所有者与处理指纹必须统一写入 `manifest.json`。

---

## 🏗️ 归一化摄入管线 (Normalized Ingestion Pipeline)

```mermaid
graph TD
    A[本地文件] --> N[归一化摄入中心]
    B[网页爬取] --> N
    C[粘贴文本] --> N
    D[智能搜索] --> N
    
    N --> R[<b>RAG 核心管线 (必经)</b><br/>向量化固化]
    R --> S{勾选: 智能分析?}
    S -- "True" --> DA[<b>SQL 核心管线 (增强)</b><br/>物理建表 / 影子映射]
    S -- "False" --> SKIP[跳过建模]
    
    DA --> G[🛡️ 旗舰治理中心]
    R --> G
```

### 1. 技术先进性结论
- **高内聚**: RAG 逻辑与 SQL 逻辑物理独立，互不污染。
- **可审计**: 通过 `Route Discovery` 日志，实现了系统决策的透明化。
- **稳定性**: 架构极大地减少了由于“自作聪明”引发的逻辑死锁。
