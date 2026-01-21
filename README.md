# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v8.6.9 (Flagship Dual-Core Edition)  
![Version](https://img.shields.io/badge/version-v8.6.9-purple)

RAG Pro Max v8.6.9 实现了 **「全源归一化 (Source-Agnostic)」** 架构的终极演进。通过支持 9 种异构数据库集成与极致的侧边栏交互重构，系统现在可以作为企业级数据中台，一站式吞噬并分析全域数据。

---

## 🚀 v8.6.9 核心特性

### 🔌 全异构数据库大满贯 (9+ DB Support)
- **极广适配**: 原生支持 MySQL, PostgreSQL, SQLite, DuckDB, ClickHouse, SQL Server, Oracle, MaxCompute (DataWorks), Snowflake。
- **四维全景透视**: 在管理端提供字段定义、50 行数据采样、物理外键关联及业务洞察统计。

### 🎨 侧边栏交互革命 (One-Click Ingestion)
- **一键直达**: 勾选即构建，彻底消除中间预取步骤。
- **即时预览 (Instant Peek)**: 选表时点击 **`👁️`** 图标，即可在侧边栏气泡中秒看表内容，告别盲选。
- **滚动容器与全选**: 优化了大库同步体验，支持一键全选。

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