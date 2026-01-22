# RAG Pro Max v8.9.0 企业级系统架构文档

**版本**: v8.9.0 (Flagship Unified Edition)  
**更新日期**: 2026-01-22  
**核心特性**: Precision Crawler Algorithm, Minimalist Unified Architecture, Omni-Source DB Integration

---

## 🏗️ 业务层内核加固 (Service Layer Hardening)

### 1. 网页抓取层级架构 (Precision Crawler Strategy)
在 v8.9.0 中，系统重写了网页抓取逻辑的层级传播模型：
- **Level-0 Seed Isolation**: 引入种子隔离层，确保主域名起始页不占用爬取名额。
- **Exponential Depth Propagation**: 采用 $n^{depth}$ 扩散模型，平衡了抓取速度与文档关联广度。
- **Unified Engine Interface**: 抽象了统一的 `crawl_recursive` 接口，解耦了同步（Requests）与异步（Aiohttp）底层实现。

### 1. 全源归一化摄入层 (Omni-Ingestion Architecture)
在 v9.0.0 中，系统引入了 **「物理暂存区 (Physical Staging Area)」** 架构，实现了前端交互与后端引擎的解耦：
- **Staging Buffer (`task_staging_dir`)**: 作为所有非结构化数据的统一汇聚点，通过 `uuid` 隔离不同任务。
- **Source Aggregators**: 
    - **Upload Ingestor**: 处理 Streamlit 文件缓冲区流。
    - **Path Ingestor**: 执行 `os.walk` 递归文件扫描与物理镜像。
    - **Paste Ingestor**: 实时文本持久化引擎。
- **Atomic Dispatcher**: 将暂存区的“并集合集”一次性投递给 `IndexBuilder`，确保了构建原子性。
- **Heterogeneous Drivers**: 封装了从 MySQL, Oracle 到 MaxCompute 的全量驱动逻辑。
- **Source-Agnostic Mirroring**: 所有的远程表在摄入阶段均会被转化为标准 `.csv` 片段，确保下游的 RAG 向量化与 SQL 影子库构建逻辑 **100% 复用**。

### 2. 架构鲁棒性模式 (Robustness Patterns)
- **Cache Buster (结构位移修复)**: 针对 Streamlit 热重载引发的内存陈旧问题，实施了“局部函数封装”策略，通过改变代码物理位置强制解释器重刷符号表。
- **On-Demand Loading (按需加载)**: 实现了 Admin 治理模块的延迟加载，物理隔离了认证拦截与管理逻辑的命名空间冲突。

### 3. 模式感应联动 (Mode-Sensing Linkage)
- **Capability Sensing**: 实时探测 `business_schema.json` 指纹，自动注入 Session State 以激活 UI 层分析开关。

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
