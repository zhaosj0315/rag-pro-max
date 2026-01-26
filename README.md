# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v9.5.37-stable (Search Revolution Edition)  
![Version](https://img.shields.io/badge/version-v9.5.37-blue)

RAG Pro Max v9.5.37 开启了 **「搜索革命 (Search Revolution)」**。通过 **Level 0 暴力链路探测** 与 **重定向解壳** 技术，系统实现了对互联网知识的“饱和式提取”。配合全功能的 **暂存区治理中心** 与 **macOS 原生预览**，为您提供最稳健的异构数据编排体验。

---

## 🚀 v9.5.37 核心特性

### 🕷️ 智能搜索革命 (Smart Search Revolution)
- **Level 0 暴力探测 (Violent Discovery)**: 放弃 HTML 解析器，采用正则表达式直接扫描原始 HTTP 字节流。物理绕过 WAF 结构混淆与模块缓存，抓取成功率直逼 100%。
- **自动解壳技术 (Direct Unwrapping)**: 内置重定向解析器，直接从 Bing/DuckDuckGo/Google 的跳转链接（如 `bing.com/ck/...`）中剥离原始 URL，实现秒级直连。
- **种子隔离架构**: 搜索引擎结果页仅作为 L0 探测种子，**不消耗** 抓取深度配额，且 **绝不** 作为文档落盘，确保知识库纯净度。

### 📦 暂存区治理中心 (Staging Inspector)
- **四维工具链**: 集成 **预览(📂)、定位(📍)、刷新(🔄)、清理(🧹)**。
- **审计追踪**: 每一份入库材料均伴生 `.meta` 审计文件（记录来源与时间），但在构建索引时会被 **自动屏蔽**，防止污染知识库。
- **物理自愈**: 支持暂存区物理路径自动重建，杜绝 Session 重置后的文件丢失报错。

### 📥 全源归一化摄入 (Omni-Ingestion)
- **物理并集 (Physical Union)**: 摒弃“单选”模式，支持文件上传、目录扫描、文本粘贴、网页摄入、数据库快照的任意组合。
- **一切皆源文件**: 所有的数据库快照（含自定义 SQL）均转化为标准 CSV 存入暂存区，与 PDF 文档实现原子化混合入库。

### 👁️ 原生系统级体验
- **macOS QuickLook**: 在文档列表中点击 `👁️`，直接唤起 macOS 原生预览窗口并强制置顶，体验如 Finder 般丝滑。
- **零白屏交互**: 全面应用 Streamlit Fragment 技术，实现局部刷新，彻底消除操作时的全页白屏闪烁。

---

## 🛠️ 安装与启动

1. **环境准备**: Python 3.10+ / macOS (推荐，支持原生预览) 或 Linux
2. **安装依赖**: `pip install -r requirements.txt`
3. **启动系统**: `streamlit run src/apppro.py`

---

## 🛠️ 维护与审计 (Maintenance & Auditing)

本项目内置了工业级的**“代码资产透视系统” (Codebase Cartography System)**，用于自动化生成项目地图与健康报告。

### 📊 生成全景图
运行以下命令，即可在 `docs/` 目录下生成最新的代码档案：

```bash
python3 scripts/maintenance/audit_codebase.py
```

### 📄 产物说明
- **`docs/CODE_INDEX.md`**: **代码户籍档案** —— 自动扫描所有源文件，列出类、函数及其核心职责。
- **`docs/DEPENDENCY_GRAPH.svg`**: **血缘关系图** —— 可视化展示模块间的调用依赖拓扑。
- **`docs/DEAD_CODE_REPORT.txt`**: **僵尸代码报告** —— 基于静态分析侦测未使用的变量与函数。

---

**🎯 目标**: 为企业用户提供最专业、极致流畅、高稳定的智能双核分析与 RAG 解决方案！