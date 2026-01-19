# RAG Pro Max

<div align="center">

**Languages:** 
[🇨🇳 中文](README.md) | 
[🇺🇸 English](README.en.md)

</div>

---

# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v6.9.5 (Flagship Purified Edition)  
![Version](https://img.shields.io/badge/version-v6.9.5-brightgreen)

RAG Pro Max 是一款专为企业级复杂场景打造的智能体系统，深度融合了全量文档搬运（RAG）、自动化网页抓取与 **Flagship Governance (旗舰级治理中心)** 的精细化安全管控能力。

---

## 🚀 v6.9.5 核心特性

### 🧼 架构深度净化 (Codebase Decoupling)
- **25+ 冗余模块切除**: 物理清理所有迭代遗留的“僵尸”代码，实现全系统中业务逻辑的“唯一物理路径”。
- **单兵最终版逻辑**: 废弃所有中间过渡函数定义，核心引擎启动速度提升 15%，彻底消除 `ImportError` 隐患。

### 🛡️ 旗舰级治理中心 (Flagship Governance)
- **个体安全调节舱**: 革命性引入“单兵作战”管理，支持为特定用户设置专属 TTL（会话有效期）及定点强制熔断。
- **全合规扫描引擎**: 秒级识别物理存储中的损坏索引、容量超限（>500MB）及长期闲置（>30天）资产。
- **治理决策中枢**: 整合资产过户、物理粉碎、权限翻转与单体资源重命名的完整治理链路。

### 🎨 视觉黄金分割架构 (Visual Alignment)
- **45px 重心优化**: 登录页垂直重心下移 45px，大幅提升大屏显示下的平衡感与人机工程学体验。
- **沉浸式指挥中心**: 95% 全宽布局，移除视觉冗余，确保管理员聚焦核心数据指标。

---

## 📚 文档资源中心

### 📂 核心实现与架构 (开发者必读)
- [📐 **系统架构总纲**](ARCHITECTURE.md) - v6.9.5 旗舰净化版架构定义
- [💎 **核心功能实现详述**](CORE_FEATURE_IMPLEMENTATION.md)
- [📊 **数据分析开发流程**](DATA_ANALYSIS_WORKFLOW.md)
- [🔧 **API 接口文档**](API_DOCUMENTATION.md) - v6.9.0 旗舰版定义

### 📖 用户指南
- [📘 **企业用户手册**](USER_MANUAL.md) - 旗舰版操作指引
- [🎭 **虚拟数据生成指南**](docs/MOCK_DATA_GUIDE.md)
- [❓ **常见问题 (FAQ)**](FAQ.md)
- [🚀 **快速上手指南**](docs/standards/FIRST_TIME_GUIDE.md)

---

## 🏗️ 系统安装

### 环境要求
- **Python**: 3.10+
- **内存**: 8GB+
- **磁盘**: 10GB+

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
