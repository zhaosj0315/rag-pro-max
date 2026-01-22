# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v8.9.0 (Flagship Unified Edition)  
![Version](https://img.shields.io/badge/version-v8.9.0-purple)

RAG Pro Max v8.9.0 引入了 **「精准抓取 (Crawler Precision)」** 算法升级，完美对齐用户对复杂网页结构的指数级扩散需求，同时加固了系统在大规模并发场景下的模块稳定性。

---

## 🚀 v8.9.0 核心特性

### 🕷️ 指数级精准抓取 (Crawler Precision)
- **种子页独立化**: 种子 URL 作为 Level 0 起点，完美释放后续层级配额。
- **5+25 递归扩散**: 严格遵循 $n^1 + n^2$ 的指数配额分布，输入 2x5 即可获得 30+ 深度关联文档。
- **三端逻辑统合**: 同步、异步、并发爬虫实现 100% 行为一致性，满足不同性能场景。

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