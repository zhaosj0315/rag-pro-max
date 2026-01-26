# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v9.5.1-stable (Omni-Source Unification)  
![Version](https://img.shields.io/badge/version-v9.5.1-green)

RAG Pro Max v9.5.1 带来了 **「全源架构统一 (Omni-Architecture Unification)」** 的里程碑式升级。通过“一切皆源文件”的设计理念，我们将数据库快照、网页抓取与本地文件彻底打通，实现了真正的异构数据混合编排。

---

## 🚀 v9.5.1 核心特性

### ⚡ 极致性能：零白屏交互 (Zero White Screen)
- **局部刷新隔离**: 深度应用 `st.fragment` 技术。功能开关切换、参数调整、数据源配置均实现 **0 毫秒全页重载**，彻底消除视觉闪烁。
- **无缝对话流**: 彻底重构核心调度引擎，移除回答生成前后的冗余 `rerun` 指令，实现“输入-流式生成-追问建议”全过程一气呵成。
- **秒级响应**: 将提问到首字蹦出的感知延迟降低了 90% 以上。

### 📥 全源归一化摄入 (Omni-Ingestion)
- **五维合一**: 将 **文件上传、目录扫描、文本粘贴、网页抓取、数据库快照** 五大核心入口物理融合。
- **数据库快照 (DB Snapshot)**: 支持 MySQL, Oracle, PostgreSQL 等 9+ 种异构数据库的整表或 **自定义 SQL** 导出。
- **统一物理暂存**: 所有渠道获取的数据（包括数据库查询结果）均转化为标准物理文件汇聚于 `task_staging_dir`，支持混合组装与统一构建。

### 💬 纯对话模式深度解耦 (Decoupled Pure Chat)
- **文件系统零依赖**: 纯对话模式现已彻底脱离知识库文件夹，无需创建任何物理索引，运行更轻、更纯粹。
- **直连流式生成**: 实现了直连大模型（Ollama/OpenAI）的增强型流式通道，支持原生生成器与封装对象的自动兼容。

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
