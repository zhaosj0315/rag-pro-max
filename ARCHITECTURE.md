# RAG Pro Max v6.9.0 企业级系统架构文档

**版本**: v6.9.0 (Flagship Governance Edition)  
**更新日期**: 2026-01-19  
**核心特性**: Individual Security Cabins, Multi-modal Resource Compliance, 45px Visual Alignment

---

## 🛡️ 旗舰级治理中心架构 (v6.9.0)

在 v6.9.0 中，系统架构实现了从“宽泛审计”到“精细化生命周期治理”的质变：

### 1. 个体化安全策略架构 (Individualized Security Strategy)
- **策略优先级 (Settings Priority)**: 引入三级 TTL（生存时间）判定逻辑：
    1. `Level 1`: 用户专属设置 (User-specific settings in `sessions.json`).
    2. `Level 2`: 全局默认配置 (Global default).
    3. `Level 3`: 代码硬编码安全值 (7 Days).
- **交互舱状态机**: 采用单选监听模式。当且仅当账户列表的勾选位（Checked State）为 1 时，激活 `Individual Cabin` 容器。该容器通过 `revoke_user_sessions` 接口与 `SessionStore` 直接通信，实现“手术刀式”的会话切断。

### 2. 全能资源合规扫描引擎 (Compliance Scanning Engine)
- **物理指纹深度探测**:
    - **损坏判定**: 校验物理路径下是否存在 `manifest.json` 与 `docstore.json` 的闭环。
    - **容量水位线**: 引入 500MB 软限制。引擎通过递归扫描 `os.walk` 计算文件夹物理总量，触发容量预警状态。
    - **休眠状态监测**: 比较 `time.time()` 与文件系统 `st_mtime` 的 delta 值，判定资源是否进入 30 天冷数据期。
- **治理指令流水线**: 整合 `KBManager.rename`、`shutil.rmtree` 和 `set_kb_public` 接口，形成统一的资产决策输出端。

### 3. 全域风险画像系统 (Unified Risk Profiling)
- **时序风险建模**: 整合了 24 小时风险得分脉搏图。系统实时计算行为权重（Critical=50, Warning=10, Info=1），揭示全员意图画像。
- **设备指纹追踪**: 引入 MD5 设备哈希指纹，结合 IP 物理位置，实现对异常登录或共享账号的秒级识别。

---

## 🎨 视觉对齐与交互架构 (v6.8.8)

### 1. 登录页重心偏移算法
- **黄金分割优化**: 采用 `translateY(-85px)` 取代原本的 `-130px`。该偏移量基于多分辨率交集计算，确保主标题处于视觉“黄金安全区”。
- **留白缓冲 (Gutter Architecture)**: 增加顶部 45px 透明 padding，显著缓解大屏设备的视觉空旷感。

### 2. 交互样式原子化覆盖
- **精细化选择器**: 利用 CSS `:has` 伪类（`[data-testid="stVerticalBlock"]:has(.login-anchor)`）实现了对 Streamlit 原生组件的深度样式隔离。
- **样式清洗**: 针对高优先级组件，通过 `!important` 强制剥离背景、边框，实现了组件形态的平滑转化。

---

## 🏗️ 架构瘦身与代码净化 (System Cleanup)

在 v6.9.0 迭代中，系统完成了史上最大规模的代码治理，物理删除了 25+ 冗余模块：
- **废弃 UI 架构**: 移除了 `src/app/` 和 `src/ui/sidebar_manager.py` 等旧版模块化尝试，统一回归 `apppro.py` 极简流式架构。
- **逻辑归口**: 清理了 `MainController` 与 `user_management.py`，将核心业务逻辑整合至 `common/business.py` 与旗舰治理中心。
- **性能减负**: 移除了过时的 `optimization_manager.py` 与 `logger.py` 包装器，全面转向 `LogManager` 高性能日志体系。

## 🧠 Strategic Workshop 3.0 架构 (v6.7.2)

在 v6.7.2 中，战略分析车间（Strategic Workshop）实现了从“全量模拟”到“精准推演”的跨越：

### 1. 精准选表引擎 (Precise Table Pruning)
系统引入了 **LLM-Based Semantic Pruning** 技术，解决了大规模表结构下的臃肿问题：
- **Semantic Filtering**: 在生成物理执行计划前，系统利用 LLM 审视 `business_schema.json` 中的字段备注。
- **Relevance Scoring**: 自动为所有表打分，仅将 Top 1-3 张核心业务表及其关联键载入候选池。
- **Domain Adaptation**: 内置财务（销项/进项）与跨境贸易（出口/进口）的前缀感知逻辑（如 `mxck` 前缀自动绑定出口业务上下文）。

### 2. 外科手术式数据仿真 (Targeted Data Synthesis)
针对“无数据、仅结构”的知识库，仿真引擎进化为按需注入模式：
- **Execution Plan Driven**: 系统根据 SQL 的 `SELECT` 列表和 `JOIN` 条件，实时计算出必须实例化的“物理节点”。
- **Selective Injection**: 只有命中的表和字段会被注入模拟数据，非相关表保持逻辑留白，计算资源消耗降低 80%。
- **Data Lineage Integration**: 在构建阶段，系统通过 **Business Semantic Brain** 自动推导表间血缘（如 `djxh` 关联关系），并将其固化为 `graph_store.json`。

---

## 🏗️ 附件解析架构 (Universal Attachment Handling)

为了解决对话增强功能中临时解析逻辑与核心加载逻辑的分裂，v6.7.0 引入了**归一化解析管线**：

### 1. 统一处理器 (`src/utils/file_upload_handler.py`)
该模块作为 UI 层与文件处理层的中间件，提供以下能力：
- **Context Preservation**: 自动创建临时文件以适配核心解析器。
- **Core Reuse**: 直接调用 `src/file_processor.py` 中的 `_load_single_file`，确保附件解析质量与入库质量 100% 对齐。
- **Multi-modal Branching**: 自动识别图片类与非图片类文件，分别走 OCR 追加或纯文本提取链路。

### 2. 流转逻辑
```
User Upload (UI)
    ↓
File Upload Handler (Middleware)
    ↓
File Processor (Core Logic)
    ↓
Prompt Context Injection
```

---

## 🛡️ 资源治理架构 (Enhanced Governance)

### 1. 物理与逻辑双透视
系统不再通过单一的数据库记录管理资产，而是通过 **“Manifest + FileSystem”** 双重扫描构建治理视图：
- **Activity Monitoring**: 通过对知识库物理目录的递归时间戳扫描，计算出“最后修改时间”。
- **Smart Categorization**: 根据库名称模式（Regex）与 Manifest 元数据自动推断库类型。

---

## 🧠 Data Analyst Agent 2.0 架构

### 1. 构建即就绪 (Build-First Architecture)
本项目数据分析引擎遵循“物理闭环”原则，严禁将数据准备工作推迟至对话阶段：
- **物理底座前置构建**：点击“构建知识库”时，系统必须完成从 Schema 提取到物理 DB 注入的全链路，确保后续对话是基于确定性的物理实体而非实时推演。
- **有数传数 (Deterministic Ingestion)**：解析 CSV/Excel 时，利用 `pandas` 强制固化为 SQLite 物理表。
- **无数造数 (Synthetic Bootstrapping)**：对于 PDF/MD 等非结构化需求文档，系统自动提取逻辑 Schema 并启动仿真引擎注入模拟数据，确保 `business_data.db` 始终处于非空且可查询状态。
- **数据指纹对齐 (Fingerprint Alignment)**：在对话生成前，必须从物理 DB 中提取列值采样（Value Samples），确保 SQL 生成精准对齐真实的物理取值分布。

### 2. 记忆与自愈引擎 (Memory & Healing Engine)
*   **On-Demand Schema Loading**: 
    *   **Pruning**: 在数据库校验前，先根据问题进行相关性裁剪（Relevant Table Selection），仅保留当前查询必需的表定义。
    *   **Speed**: 避免了对百表规模知识库的全量扫描，将环境初始化时间从 $O(N)$ 降至 $O(1)$。
*   **Schema Healing & Mapping**:
    *   **Alias Discovery**: 当检测到 Schema 与物理库表名不一致时，通过模糊匹配（单复数、前缀后缀）寻找“物理替身”。
    *   **Memory Redirection**: 在内存中建立映射字典，后续 SQL 生成阶段自动将逻辑表名重定向为物理表名。

---

## 🏗️ 爬虫架构演进 (v6.6.5)

### 1. 饱和式抓取管线 (Saturation Queue Pipeline)
系统废弃了传统的 BFS 分层递归模式，转向**饱和式队列模式**以对齐高性能原生脚本：
*   **Continuity**: 采用单线程 `while` 队列逻辑。只要发现符合 `scope_prefix` 的链接，立刻入队，直至队列耗尽。
*   **WAF Safe**: 引入了物理级降速（Intelligent Throttling），并发限制为 1，确保抓取过程不被云端防火墙中断。
*   **Strict Scoping**: 直接应用 `startswith(Full_URL_Prefix)` 判定逻辑，消除协议与路径解析导致的断流。

---

## 🧩 核心流程演进

### 1. 饱和式抓取流程 (v6.6.5)
```
输入 Start URL 
    ↓
计算 Full URL Scope (含协议+域名+根路径)
    ↓
初始化饱和队列 (urls_to_visit)
    ↓
[循环抓取]
    ↓
html2text 提取 (锁定 content-wrapper)
    ↓
1:1 链接提取 (urljoin + prefix match)
    ↓
URL 路径映射文件名 (物理对齐)
    ↓
自动化元数据打标 (Mac xattr)
```


