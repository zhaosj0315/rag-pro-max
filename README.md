# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v8.8.0 (Flagship Unified Edition)  
![Version](https://img.shields.io/badge/version-v8.8.0-purple)

RAG Pro Max v8.8.0 实现了 **「极简归一化 (Minimalist Unified)」** 架构的终极演进。通过将数据摄入收敛为三大全能入口，配合 9 种异构数据库集成，系统现在可以作为企业级数据中台，一站式吞噬并分析全域数据。

---

## 🚀 v8.8.0 核心特性

### 🔌 全异构数据库大满贯 (9+ DB Support)
- **极广适配**: 原生支持 MySQL, PostgreSQL, SQLite, DuckDB, ClickHouse, SQL Server, Oracle, MaxCompute (DataWorks), Snowflake。
- **四维全景透视**: 在管理端提供字段定义、50 行数据采样、物理外键关联及业务洞察统计。

### 🎨 侧边栏交互革命 (Unified Ingestion)
- **三大全能入口**: 界面重构为 **📂文件上传 (含粘贴/路径)、🌐互联网提取 (含爬虫/搜索)、🔌数据库同步** 三大核心支柱。
- **智能意图识别**: 互联网提取模式下，自动根据输入内容（URL 或关键词）路由至精准爬虫或全网搜索引擎。
- **万能附件下沉**: “📝 粘贴文本”与“本地路径”深度融合至文件上传面板，支持失焦自动保存。
- **即时预览 (Instant Peek)**: 选表时点击 **`👁️`** 图标，即可在侧边栏气泡中秒看表内容，告别盲选。

### ⚡ 问答模式智能联动 (Smart Linkage)
- **探测即激活**: 自动感应知识库能力并开启分析开关。
- **归一化身份**: 统一全模式下的“知识库名称”录入与 💡 智能命名建议。

### 🕸️ 智能图谱构建器 (Schema Graph Builder)
- **深度画像**: 自动识别主键 (PK)、枚举值 (Enums) 并推演表间关联拓扑。


## 🛠️ 安装与启动

1. **环境准备**: Python 3.10+ / macOS (推荐) 或 Linux
2. **安装依赖**: `pip install -r requirements.txt`
3. **启动系统**: `streamlit run src/apppro.py`

---

**🎯 目标**: 为企业用户提供最专业、高性能、高稳定的智能双核分析与 RAG 解决方案！