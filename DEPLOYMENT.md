# RAG Pro Max v6.9.5 企业级部署指南 (Flagship Purified Edition)

**版本**: v6.9.5  
**更新日期**: 2026-01-19  
**核心特性**: 架构深度净化、个体安全调节舱、全合规自动巡检

---

## 🏢 环境要求与依赖

### 1. 软件环境
- **Python**: 3.10+ (推荐)
- **数据库**: SQLite 3.x (系统内置)
- **MCP 扩展支持**: 若需使用 GitHub、Exa 等扩展，需安装 `gemini-cli` 环境。

### 2. 关键依赖安装
```bash
pip install -r requirements.txt

# 验证数据分析核心组件
python -c "import pandas, plotly, sqlite3; print('✅ Data Analytics Stack Ready')"
```

---

## 🚀 部署流程

### 1. 初始化配置文件
复制并编辑 `.env` 文件。v6.7.0 建议在此集中管理扩展密钥：

```bash
# 基础配置
STREAM_PORT=8501

# GitHub 扩展配置 (可选)
# 必须使用 export 关键字，否则 MCP 进程可能无法读取
export GITHUB_PERSONAL_ACCESS_TOKEN=your_pat_token
export GITHUB_TOKEN=your_pat_token

# Exa 搜索配置 (可选)
export EXA_API_KEY=your_exa_key
```

### 2. 启动服务
```bash
# 推荐方式 (自动加载 .env)
source .env && ./start.sh

# Docker 方式
docker-compose up -d --build
```

---

## 🐳 Docker 镜像说明
v6.9.5 官方镜像标签为 `ragpromax/rag-pro-max:v6.9.5`。
请在 `docker-compose.yml` 中确保更新版本号。

---

## 🛠️ 运维与资产维护

### 1. 物理目录结构
- **知识库数据**: `vector_db_storage/` (包含物理数据库与向量索引)
- **对话历史**: `chat_histories/`
- **运行日志**: `app_logs/` (建议定期清理)

### 2. 维护脚本 (v6.7.0 重构路径)
所有维护动作应通过 `scripts/` 目录下的规范化路径执行：
- **全量材料维护**: `./scripts/cleanup_materials.sh`
- **知识库一致性诊断**: `python scripts/maintenance/diagnose_kb.py`
- **故障自动修复**: `python scripts/maintenance/fix_existing_kb.py`

---

## 🛡️ 安全加固

### 1. 权限管理
在多用户 Linux/macOS 环境下，必须确保日志目录可写：
```bash
chmod -R 777 app_logs/
```

### 2. 隐私脱敏
系统导出的全量资产包已自动对 API 密钥进行脱敏处理，但建议在生产环境下禁用 `DEBUG` 模式。

---

## 📑 开发者参考文档
- [📐 架构总纲](ARCHITECTURE.md)
- [💎 核心实现](CORE_FEATURE_IMPLEMENTATION.md)
- [📊 数据分析流程](DATA_ANALYSIS_WORKFLOW.md)
- [📝 文档维护标准](docs/standards/DOCUMENTATION_MAINTENANCE_STANDARD.md)