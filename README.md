# RAG Pro Max - 企业级智能文档问答与数据分析系统

**当前版本**: v8.0.0 (Flagship Dual-Core Edition)  
![Version](https://img.shields.io/badge/version-v8.0.0-purple)

RAG Pro Max v8.0 正式发布！我们彻底重构了系统的底层逻辑，通过 **「双核组装 (Dual-Core Assembly)」** 架构，让每一个知识库同时具备深层语义理解（RAG）与精准数据决策（SQL）能力。

---

## 🚀 v8.0.0 核心特性

### 🧬 双核联动组装 (Dual-Core Integration)
- **从模式切换到能力叠加**: 告别 RAG 和 数据分析的“二选一”时代。现在以 RAG 为全量语义底座，数据分析作为“高级插件”按需挂载。
- **物理闭环固化**: 向量索引与物理数据库在同一个 KBID 目录下完美共存，实现“数文对照”的极致精准。

### 🛡️ 架构鲁棒性加固 (Robustness)
- **全局单例执行器**: 解决大型 Streamlit 应用中的作用域冲突，保障多核推演 100% 成功。
- **监控大盘自愈**: 彻底根治 Pandas 热加载时的 TypeError，支持强制热重载。

### 🛡️ 旗舰级治理中心 (Flagship Governance)
- **个体安全调节舱**: 引入“单兵作战”管理，支持为特定用户设置专属会话有效期及定点强制熔断。
- **全合规扫描引擎**: 秒级识别物理存储中的损坏索引、容量超限（>500MB）及长期闲置资产。

---

## 🛠️ 安装与启动

1. **环境准备**: Python 3.10+ / macOS (推荐) 或 Linux
2. **安装依赖**: `pip install -r requirements.txt`
3. **启动系统**: `streamlit run src/apppro.py`

---

**🎯 目标**: 为企业用户提供最专业、高性能、高稳定的智能双核分析与 RAG 解决方案！