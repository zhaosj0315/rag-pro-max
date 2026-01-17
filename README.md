# RAG Pro Max

<div align="center">

**Languages:** 
[🇨🇳 中文](README.md) | 
[🇺🇸 English](README.en.md)

</div>

---

# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v6.7.1 (Stable Production Edition)  
![Version](https://img.shields.io/badge/version-v6.7.1-brightgreen)

RAG Pro Max 是一款专为企业级复杂场景打造的智能体系统，深度融合了全量文档搬运（RAG）、自动化网页抓取与物理闭环的数据分析能力。

---

## 🚀 v6.7.0 核心特性

### 🛡️ 资源治理矩阵 (Unified Governance)
- **物理透视**: 实时扫描文件系统，展示资产“创建时间”与“最后修改”，治理效率提升 200%。
- **确定性批量操作**: 彻底解决状态丢失问题，支持对海量库进行一键“全选”物理清理或权限分发。

### 📎 万能附件解析 (Universal Uploader)
- **逻辑归一化**: 聊天附件与知识库构建共享 100% 相同的底层解析内核，支持 20+ 种格式（CSV/Excel/Code）的即时注入。
- **多图 OCR 追加**: 完美适配多轮图片问答场景，自动合并识别内容。

### 🧠 数据分析师 2.0 (Build-First Architecture)
- **构建期物理闭环**: 遵循“构建即就绪”准则。在构建阶段完成从 Schema 提取到物理 DB（SQLite）注入的全过程。
- **无数造数**: 针对逻辑文档自动生成仿真数据，确保“第一句提问”即有实质性响应。
- **下钻分析**: 支持基于前序分析发现的异常点进行连续追问，自动继承 SQL 上下文。

### 🕷️ 饱和式抓取引擎
- **1:1 逻辑克隆**: 采用饱和式队列模式取代 BFS，确保大型文档站 100% 抓取。
- **反爬护航**: 智能降速配合随机物理延迟，完美规避 WAF 防火墙。

---

## 📚 文档资源中心

### 📂 核心实现与架构 (开发者必读)
- [📐 **系统架构总纲**](ARCHITECTURE.md) - v6.7.0 最新架构定义
- [💎 **核心功能实现详述**](CORE_FEATURE_IMPLEMENTATION.md) - 5大主心骨功能底层逻辑 (🆕)
- [📊 **数据分析开发流程**](DATA_ANALYSIS_WORKFLOW.md) - 物理闭环与仿真引擎标准 (🆕)
- [🔧 **API 接口文档**](API_DOCUMENTATION.md) - 后端服务定义

### 📖 用户指南
- [📘 **企业用户手册**](USER_MANUAL.md) - 完整功能操作指引
- [🎭 **虚拟数据生成指南**](docs/MOCK_DATA_GUIDE.md) - 仿真造数全攻略 (🆕)
- [❓ **常见问题 (FAQ)**](FAQ.md) - 疑难杂症快速排除
- [🚀 **快速上手指南**](docs/standards/FIRST_TIME_GUIDE.md) - 5分钟部署运行

### 🛠️ 开发与管理规范
- [🧹 **材料维护执行指南**](docs/standards/MATERIAL_MAINTENANCE_GUIDE.md)
- [📝 **文档维护标准**](docs/standards/DOCUMENTATION_MAINTENANCE_STANDARD.md)
- [🔒 **代码推送规范**](docs/standards/NON_ESSENTIAL_PUSH_STANDARD.md)
- [🧼 **开发清理标准**](docs/standards/DEVELOPMENT_CLEANUP_STANDARD.md)

---

## 🏗️ 系统安装

### 环境要求
- **Python**: 3.10+
- **内存**: 8GB+
- **磁盘**: 10GB+ (用于模型缓存)

### 快速部署
```bash
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max
pip install -r requirements.txt
./start.sh
```

---

## 📊 技术栈
- **RAG 引擎**: LlamaIndex + ChromaDB
- **数据分析**: SQLite + Pandas + Plotly
- **前端交互**: Streamlit (Command Center UI v7.9)
- **OCR**: PaddleOCR / Apple Vision Framework

---

## 📜 许可证
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

<div align="center">

Made with ❤️ by RAG Pro Max Team

</div>