# RAG Pro Max v8.1.0 企业级系统架构文档

**版本**: v8.1.0 (Flagship Dual-Core Edition)  
**更新日期**: 2026-01-20  
**核心特性**: Iron-Gate Routing, Dual-Core Co-existence, Standard Ingestion Invariants

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
