# RAG Pro Max v4.3.0 企业级系统架构文档

**版本**: v4.3.0 (Stable Data Analysis Edition)  
**更新日期**: 2026-01-11  
**适用范围**: 企业级高性能 RAG 与数据分析平台  
**核心特性**: 分析实验室 2.0、全宽流式布局、macOS 线程安全并发模型

---

## 🏗️ 整体架构图

### 1. 表现层 (Presentation Layer - Fluid UI)
- **Fluid Layout Engine**: 放弃固定比例分屏，采用全宽流式布局。根据数据特征动态渲染“对话流”与“成果流 (Artifacts)”。
- **Artifacts 2.0 Workspace**: 针对结构化数据自动激活，支持左结论右图表的 1:3 布局。
- **Streamlit Fragments**: 核心 UI 组件（如文件列表、监控看板）采用局部刷新技术，避免整页跳动。

### 2. 服务层 (Service Layer)
- **Data Analyst Engine 11.0**: 
    - **SQL 自动校准**: 针对 LLM 生成的 SQL 进行物理 Schema 校验与纠偏。
    - **语义数据嗅探**: 自动感应 CSV 数据特征并触发可视化流程。
- **RAG Engine**: 支持跨知识库多库检索与混合流式协议输出。

### 3. 公共层 (Common & Utils Layer)
- **Concurrency Manager (v4.3.0)**: 
    - **ThreadPool Strategy**: 在 macOS 平台全面启用 `ThreadPoolExecutor` 替代 `ProcessPoolExecutor`，解决 I/O 密集型任务（如 OCR、搜索）引发的 Fork 崩溃。
- **Metadata Management**: `ManifestManager` 负责 30+ 项物理属性与系统元数据（mdls/xattr）的存取。

---

## 🧩 核心流程演进

### 1. 数据分析流 (Analysis Pipeline)
```
用户查询 (SQL/趋势/对比)
    ↓
RAG 引擎语义召回
    ↓
Data Analyst 引擎嗅探
    ↓
SQL/数据清洗与自愈
    ↓
Fluid Layout 触发 (Artifacts)
    ↓
Plotly 交互式绘图渲染
```

### 2. 高性能并发模型
针对 macOS (Darwin) 系统，系统在启动时自动检测平台并配置调度策略：
- **CPU 密集型**: 向量计算由底层库（如 OpenBLAS/MKL）处理。
- **I/O 与混合型 (OCR/Web)**: 使用线程隔离，确保在 Streamlit 全局状态下保持线程安全。

---

## 🔧 技术栈 (v4.3.0 对齐)

- **前端**: Streamlit (使用 Fragment 与 Custom CSS 实现流式布局)
- **核心框架**: LlamaIndex v0.10+ (流式协议对齐)
- **数据库**: ChromaDB (本地持久化) + SQLite (元数据)
- **并发控制**: ThreadPoolExecutor (macOS 深度优化)
- **可视化**: Plotly + Container Proxy 渲染

---

## 🛡️ 安全与审计架构

- **零噪存储**: 文档物理路径与原始 URL 溯源信息通过系统级元数据 (xattr) 实现持久化锁定。
- **隔离机制**: 多知识库间实现物理存储与会话上下文的严格隔离。

