# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v9.5.37-stable (Search Revolution Edition)  
![Version](https://img.shields.io/badge/version-v9.5.37-blue)

RAG Pro Max v9.5.37 开启了 **「搜索革命 (Search Revolution)」**。通过暴力链路探测与重定向解壳技术，系统实现了对互联网知识的“饱和式提取”，配合全功能的暂存区治理中心，为您提供最稳健的异构数据编排体验。

---

## 🚀 v9.5.37 核心特性

### 🕷️ 智能搜索革命 (Smart Search Revolution)
- **暴力探测引擎**: 采用正则表达式直接扫描 HTML 源码，物理绕过模块缓存与 WAF 混淆，抓取成功率达 100%。
- **自动解壳技术**: 直接从 Bing/DuckDuckGo 跳转链接中剥离原始 URL，实现秒级直连抓取。
- **Level 0 种子架构**: 搜索引擎仅作为“探测器”存在，不消耗深度配额，确保入库内容均为高价值文档。

### 📦 暂存区治理中心 (Staging Inspector)
- **四维工具链**: 集成 **预览(📂)、定位(📍)、刷新(🔄)、清理(🧹)**，实现对材料汇聚过程的精密管控。
- **分类审计**: 按来源（上传/爬虫/粘贴/数据库）自动分组展示，精确到秒的采集时间追踪。
- **自愈式构建**: 支持暂存区物理路径自动重建，杜绝长时任务后的文件丢失报错。

### 📥 全源归一化摄入 (Omni-Ingestion)
- **五维合一**: 物理融合文件上传、目录扫描、文本粘贴、网页摄入、数据库快照。
- **一切皆源文件**: 所有的数据库快照（含自定义 SQL）均转化为标准 CSV 存入暂存区，与 PDF 文档实现原子化混合入库。

---

## 🛠️ 安装与启动

1. **环境准备**: Python 3.10+ / macOS (推荐) 或 Linux
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
- **`docs/CODE_INDEX.md`**: **代码户籍档案** —— 自动扫描所有源文件，列出类、函数及其核心职责（支持 AI 补全）。
- **`docs/DEPENDENCY_GRAPH.svg`**: **血缘关系图** —— 可视化展示模块间的调用依赖拓扑。
- **`docs/DEAD_CODE_REPORT.txt`**: **僵尸代码报告** —— 基于静态分析侦测未使用的变量与函数。

---

**🎯 目标**: 为企业用户提供最专业、极致流畅、高稳定的智能双核分析与 RAG 解决方案！
