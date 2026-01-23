# RAG Pro Max v9.1.0 企业级系统架构文档

**版本**: v9.1.0 (Flagship Evolution - Ultra Performance)  
**更新日期**: 2026-01-23  
**核心特性**: Fragment UI Isolation, Seamless Chat Pipeline, Decoupled Pure Chat

---

## 🏗️ 极致表现层隔离 (Presentation Layer Isolation)

### 1. 局部刷新隔离架构 (Fragment-Level UI Isolation)
在 v9.1.0 中，表现层引入了 **「组件级状态隔离 (Fragment Isolation)」** 模式，解决了 Streamlit 传统的“单向数据流引发的全量重绘”痛点：
- **Lifecycle Decoupling**: 利用 `@st.fragment` 装饰器，将工具栏切换、参数微调、数据摄入配置等高频交互组件的生命周期与主对话区解耦。
- **Visual Performance**: 局部刷新机制将配置操作的响应延迟从秒级降低至 **50ms** 以内，彻底消除白屏闪烁。
- **Incremental Rendering**: 对话结束后的“追问建议”采用原地增量渲染技术，确保用户在流式输出结束的瞬间即可进行下一次点击，无需等待页面重载。

### 2. 跨生命周期 Key 映射 (Stable-Key Binding)
为了解决 Fragment 内部点击事件在全页刷新后丢失的问题，系统实现了一套**基于内容的稳定哈希算法**：
- **Deterministic Keying**: 实时计算回答内容的哈希值，确保即时生成的按钮 Key 与持久化后的历史记录 Key **100% 对齐**。
- **Interaction Seamlessness**: 确保了用户在点击即时出现的建议按钮时，系统能精准映射到后台处理队列，实现了交互的无缝衔接。

---

## 🏗️ 业务层内核加固 (Service Layer Hardening)

### 1. 纯对话模式深度解耦 (Decoupled Pure Chat)
在 v9.1.0 中，系统彻底剥离了纯对话模式对底层知识库索引的依赖：
- **Filesystem-Agnostic Execution**: 纯对话模式下直接跳过 `KnowledgeBaseLoader` 与磁盘扫描步骤，不再强制要求 `vector_db_storage` 路径存在。
- **Bypass LLM Channel**: 建立专用 LLM 直连链路，绕过向量化检索步骤，通过 `Settings.llm` 容器实现高性能的无损流式输出。

### 2. 网页抓取层级架构 (Precision Crawler Strategy)
在 v8.9.0 中，系统重写了网页抓取逻辑的层级传播模型：
- **Level-0 Seed Isolation**: 引入种子隔离层，确保主域名起始页不占用爬取名额。
- **Exponential Depth Propagation**: 采用 $n^{depth}$ 扩散模型，平衡了抓取速度与文档关联广度。
- **Unified Engine Interface**: 抽象了统一的 `crawl_recursive` 接口，解耦了同步（Requests）与异步（Aiohttp）底层实现。

### 3. 全源归一化摄入层 (Omni-Ingestion Architecture)
在 v9.0.0 中，系统引入了 **「物理暂存区 (Physical Staging Area)」** 架构，实现了前端交互与后端引擎的解耦：
- **Staging Buffer (`task_staging_dir`)**: 作为所有非结构化数据的统一汇聚点，通过 `uuid` 隔离不同任务。
- **Source Aggregators**: 
    - **Upload Ingestor**: 处理 Streamlit 文件缓冲区流。
    - **Path Ingestor**: 执行 `os.walk` 递归文件扫描与物理镜像。
    - **Paste Ingestor**: 实时文本持久化引擎。
- **Atomic Dispatcher**: 将暂存区的“并集合集”一次性投递给 `IndexBuilder`，确保了构建原子性。
- **Heterogeneous Drivers**: 封装了从 MySQL, Oracle 到 MaxCompute 的全量驱动逻辑。
- **Source-Agnostic Mirroring**: 所有的远程表在摄入阶段均会被转化为标准 `.csv` 片段，确保下游的 RAG 向量化与 SQL 影子库构建逻辑 **100% 复用**。

### 4. 架构鲁棒性模式 (Robustness Patterns)
- **Scope Safeguard**: 针对 Fragment 引入引发的作用域黑洞，实施了“全局初始化兜底”策略，确保 `btn_start` 等调度变量在任意生命周期阶段均可见。
- **Conflict Resolution**: 解决了 Widget Key 与 Session State 的同步竞态，确保了状态机的单向一致性。
- **Cache Buster (结构位移修复)**: 针对 Streamlit 热重载引发的内存陈旧问题，实施了“局部函数封装”策略，通过改变代码物理位置强制解释器重刷符号表。


---

## 🧬 归一化摄入管线 (Normalized Ingestion Pipeline)

在 v8.8.0 中，表现层（Presentation Layer）经历了深度重构，实现了**入口逻辑的归一化**。

- **三大全能入口**: 界面收敛为文件、互联网、数据库三大核心支柱。
- **智能路由**: 互联网模式下内置自动意图识别引擎 (Intent Recognition Engine)。
- **万能附件 (Universal Attachment)**: 实现了全源文件上传入口，支持图片 OCR 与文档解析逻辑的深度复用。
- **配置下沉**: 将“数据分析”从顶级导航下沉为 `IndexBuilder` 的配置参数 `enable_data_analysis`。

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
    A[📂 文件上传 (含粘贴/路径)] --> N[归一化摄入中心]
    B[🌐 互联网提取 (含爬虫/搜索)] --> N
    C[🔌 数据库同步] --> N
    
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
