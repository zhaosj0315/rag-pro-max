# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v9.3.0-stable (Flagship Evolution)  
![Version](https://img.shields.io/badge/version-v9.3.0-green)

RAG Pro Max v9.3.0 带来了 **「极致性能 (Ultra-Performance)」** 飞跃。通过深度应用局部刷新隔离技术，系统实现了 **“零白屏”** 的无缝交互体验，在对话流畅度与配置响应速度上达到了行业顶尖水平。

---

## 🚀 v9.3.0 核心特性

### ⚡ 极致性能：零白屏交互 (Zero White Screen)
- **局部刷新隔离**: 深度应用 `st.fragment` 技术。功能开关切换、参数调整、数据源配置均实现 **0 毫秒全页重载**，彻底消除视觉闪烁。
- **无缝对话流**: 彻底重构核心调度引擎，移除回答生成前后的冗余 `rerun` 指令，实现“输入-流式生成-追问建议”全过程一气呵成。
- **秒级响应**: 将提问到首字蹦出的感知延迟降低了 90% 以上。

### 💬 纯对话模式深度解耦 (Decoupled Pure Chat)
- **文件系统零依赖**: 纯对话模式现已彻底脱离知识库文件夹，无需创建任何物理索引，运行更轻、更纯粹。
- **直连流式生成**: 实现了直连大模型（Ollama/OpenAI）的增强型流式通道，支持原生生成器与封装对象的自动兼容。

### 📥 全能并集摄入 (Omni-Ingestion)
- **多源叠加**: 告别单选，支持同时上传文件、添加本地路径、粘贴文本，自由组装知识库材料。
- **物理暂存区**: 引入 `task_staging_dir` 机制，提供实时的文件计数与清空管理。

### 🔌 全异构数据库大满贯 (9+ DB Support)
- **极广适配**: 原生支持 MySQL, PostgreSQL, SQLite, DuckDB, ClickHouse, SQL Server, Oracle, MaxCompute, Snowflake。
- **四维全景透视**: 提供字段定义、50 行数据采样、物理外键关联及业务洞察。

### 🕷️ 指数级精准抓取 (Crawler Precision)
- **5+25 递归扩散**: 严格遵循 $n^1 + n^2$ 的指数配额分布，输入 2x5 即可获得 30+ 深度关联文档。
- **三端逻辑统合**: 同步、异步、并发爬虫实现 100% 行为一致性。

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
