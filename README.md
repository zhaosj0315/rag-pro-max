# RAG Pro Max

<div align="center">

**Languages:** 
[🇨🇳 中文](README.md) | 
[🇺🇸 English](README.en.md)

</div>

---

# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v6.9.0 (Flagship Governance Edition)  
![Version](https://img.shields.io/badge/version-v6.9.0-blue)

RAG Pro Max 是一款专为企业级复杂场景打造的智能体系统，深度融合了全量文档搬运（RAG）、自动化网页抓取与 **Flagship Governance (旗舰级治理中心)** 的精细化安全管控能力。

---

## 🚀 v6.9.0 核心特性

### 🛡️ 旗舰级治理中心 (Flagship Governance)
- **个体安全调节舱**: 革命性引入“单兵作战”管理，支持为特定用户设置专属 TTL（会话有效期）及定点强制熔断。
- **全合规扫描引擎**: 秒级识别物理存储中的损坏索引、容量超限（>500MB）及长期闲置（>30天）资产。
- **治理决策中枢**: 整合资产过户、物理粉碎、权限翻转与单体资源重命名的完整治理链路。

### 🎨 视觉黄金分割架构 (Visual Alignment)
- **45px 重心优化**: 登录页垂直重心下移 45px，大幅提升大屏显示下的平衡感与人机工程学体验。
- **沉浸式指挥中心**: 95% 全宽布局，移除视觉冗余，确保管理员聚焦核心数据指标。

### 🧠 Strategic Workshop 3.0 (战略分析车间)
- **精准选表引擎**: 采用 LLM 驱动的语义剪枝，从海量表中精准锁定核心业务表，查询初始化速度提升 500%。
- **外科手术式仿真**: 针对逻辑 Schema 实现“按需注入”，只为执行计划命中的字段生成数据，确保逻辑高度一致。
- **领域感知引擎**: 内置对跨境贸易（出口/进口）与财税（销项/进项）的专业语义理解。

### 🛡️ 资源治理矩阵 (Unified Governance)
- **物理透视**: 实时扫描文件系统，展示资产“创建时间”与“最后修改”，治理效率提升 200%。
- **全选式批量操作**: 支持对海量库进行一键物理清理、权限分发或全量快照导出。

### 📎 万能附件解析 (Universal Uploader)
- **逻辑归一化**: 聊天附件与知识库构建共享 100% 相同的底层解析内核，支持 20+ 种格式。
- **即时注入**: 拖入文件后内容立刻作为上下文进入对话，无需预先入库。

### 🕷️ 饱和式抓取引擎
- **1:1 逻辑克隆**: 采用饱和式队列模式，确保大型官网文档 100% 完整抓取。
- **反爬护航**: 智能降速配合随机物理延迟，完美规避云端防火墙。

---

## 📚 文档资源中心

### 📂 核心实现与架构 (开发者必读)
- [📐 **系统架构总纲**](ARCHITECTURE.md) - v6.9.0 旗舰版架构定义
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