# RAG Pro Max v9.5.37 企业级系统架构文档

**版本**: v9.5.37 (Search Revolution Edition)  
**更新日期**: 2026-01-26  
**核心特性**: Violent Discovery, Redirect Unwrapping, Staging Inspector, Meta-Shielding

---

## 🏗️ 网页抓取层级架构 (Smart Search Architecture)

在 v9.5.37 中，系统重写了搜索模式的调度核心，引入了 **「种子探测与获取分离」** 模式。

### 1. Level 0: 暴力探测层 (Violent Discovery)
- **Physical Inlining**: 为了绕过 Python 多进程环境下的模块缓存陈旧问题，探测算法 (`discovery_links_violently`) 直接物理嵌入 `apppro.py`。
- **Regex Extraction**: 放弃对脆弱 HTML 标签的选择性依赖，采用正则表达式扫描原始字节流，从混淆代码中暴力提取 `https://` 链接。
- **Redirect Unwrapping**: 引入 `extract_real_url` 算法，在探测阶段直接剥离 Bing/DDG 跳转外壳，锁定目标终点。

### 2. Level 1+: 饱和抓取层 (Document Crawling)
- **Isolation Principle**: 搜索引擎结果页（L0）仅用于链接分发，内容会被强制清空，不计入深度配额。
- **Concurrent Execution**: 采用 `ThreadPoolExecutor` (I/O 密集型) 替代多进程，彻底解决 macOS 下的 `ProcessPool` 崩溃问题。
- **Markdown Normalization**: 所有 HTML 均通过 `HtmlToMarkdown` 转化为高纯度 `.md` 文件，保留标题层级结构。

---

## 🏗️ 全源归一化暂存架构 (Omni-Source Staging)

### 1. Staging Inspector 工具链
系统为 `task_staging_dir` 赋予了完整的生命周期管理能力：
- **Unified 5 Sources**: 本地上传、目录扫描、文本粘贴、网页抓取、数据库快照。
- **Audit Sidecars**: 每一份源文件 (`file.ext`) 均配有 `.meta` 伴生文件 (`file.ext.meta`)，记录物理来源与采集时间。
- **Meta-Shielding (审计屏蔽)**: 在 `IndexBuilder` 构建阶段，文件扫描器 (`_scan_files`) 内置了 `not f.endswith('.meta')` 过滤器。这确保了审计文件 **仅用于 UI 展示与溯源**，绝对不会进入向量索引或被误读为文档内容。

### 2. 物理自愈机制
- **Pre-Write Check**: 在每一次 IO 操作前检查暂存目录完整性，实现 Session 级别的路径自愈。
- **Direct Finder Integration**: 集成 macOS `open -R` 指令，实现物理路径的秒级跳转定位。

### 3. 全源归一化摄入层 (Omni-Ingestion Architecture)
在 v9.5 系列中，系统实现了**“一切皆源文件 (Everything is a Source File)”**的终极架构统一：
- **Unified Engine**: `src/ui/unified_ingestion.py` 是系统的唯一摄入入口，同时服务于 **Create Mode** 和 **Append Mode**。
- **Dual Staging Buffers**: 
    - **Global Buffer**: `temp_uploads` (用于创建新库)。
    - **Append Buffer**: `vector_db_storage/<kb>/append_staging` (用于追加维护)，实现物理隔离。
- **Source Aggregators**: 
    - **Upload Ingestor**: 处理 Streamlit 文件缓冲区流，具备 `md5` 哈希去重能力。
    - **Path Ingestor**: 执行 `os.walk` 递归文件扫描与物理镜像。
    - **Paste Ingestor**: 实时文本持久化引擎，生成 `Pasted_{Timestamp}.txt`。
    - **Web Ingestor**: 网页爬虫与智能搜索结果 Markdown 化。
    - **Database Exporter**: 数据库查询结果流式物料化 (CSV)。
- **Atomic Dispatcher**: 将暂存区的“并集合集”一次性投递给 `IndexBuilder`，确保了构建原子性。

---

## 🧬 构建管线与资产沉淀 (Pipeline & Assets)

构建过程严格遵循 **“物理归档优先”** 原则：

1.  **索引构建**: `VectorStoreIndex` 处理有效文档，生成 `vector_store.json`。
2.  **物理归档**: 执行 `shutil.copy2` 将暂存区有效文件（排除 `.meta`）全量镜像到 `raw_sources/`。
3.  **模型锁定**: 生成 `.kb_info.json`，永久记录构建时使用的 Embedding 模型，防止未来模型不匹配。
4.  **户籍登记**: 生成 `manifest.json`，记录所有权、摘要及文件指纹。

---

## 🧬 双核组装与严选路由 (Iron-Gate Routing)

在 v8.1.0 迭代中，系统确立了“能力预装”与“实时激活”相分离的顶层架构模式。

### 1. 意图严选路由 (Iron-Gate Routing)
为了防止 SQL 引擎对定性查询的“逻辑干扰”，系统在提问主循环中实施了防御式网关：
- **物理判定 (`is_data_kb`)**: 检查 KB 目录是否存在 `business_schema.json`。
- **意图判定 (`manual_da_on`)**: 实时监听 Session State 中的数据分析开关。
- **铁闸决策**: 只有当 `is_data_kb AND manual_da_on` 为真时，流量才允许流向逻辑核（SQL 推演）。否则，一律默认路由至语义核（RAG 检索）。

---

## 🏗️ 归一化摄入管线图 (Pipeline Diagram)

```mermaid
graph TD
    A[📂 文件/目录/粘贴] --> N[归一化摄入中心]
    B[🌐 网页/搜索] --> N
    C[🗄️ 数据库快照 (CSV)] --> N
    
    N --> S[暂存区 Staging Area]
    S -.-> M[.meta 审计文件]
    
    S --> I[IndexBuilder]
    M -- "Shielding" --> X[屏蔽过滤]
    
    I --> R[<b>RAG 核心管线</b><br/>向量化固化]
    I --> P[<b>物理归档</b><br/>raw_sources/]
    
    R --> D{勾选: 智能分析?}
    D -- "True" --> DA[<b>SQL 核心管线</b><br/>business_data.db]
    
    DA --> G[🛡️ 旗舰治理中心]
    R --> G
```
