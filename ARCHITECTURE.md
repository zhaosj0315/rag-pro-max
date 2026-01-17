# RAG Pro Max v6.7.0 企业级系统架构文档

**版本**: v6.7.0 (Governance & Attachment Unification)  
**更新日期**: 2026-01-17  
**核心特性**: 资源治理矩阵、万能附件解析、终端自愈诊断

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


