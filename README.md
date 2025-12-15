# RAG Pro Max - 智能文档问答系统 | AI知识库 | 本地部署RAG应用

<div align="center">

![Version](https://img.shields.io/badge/version-v2.3.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Docker-lightgrey.svg)

**🔥 开源免费的企业级RAG应用 | 支持本地部署 | 无需联网使用**

基于 Streamlit + LlamaIndex 的智能文档问答系统，支持PDF/Word/Excel等多格式文档上传，提供语义检索和AI问答功能。适合企业知识库、学术研究、个人文档管理。

**🎯 核心优势**: 本地部署 • 数据安全 • 多模态支持 • GPU加速 • 一键部署

</div>

---

## ✨ 功能特性

### 🚀 v2.3.1 新增功能
- 🕷️ **网页爬虫层级修复** - 真正按递归深度层级爬取，支持深度递归抓取
- 📊 **增强爬取日志** - 清晰显示每层爬取进度和统计信息
- 🛑 **安全熔断机制** - 网页抓取限制5万页（硬编码），防止系统崩溃
- 🧹 **自动清理机制** - 启动时自动清理24小时以上临时文件（仅temp_uploads目录）
- ⏹ **停止按钮功能** - 支持中断流式对话生成（仅限response_gen循环）
- 📄 **引用页码显示** - PDF文档显示页码信息（需要PyMuPDF/PyPDF2支持）
- 📊 **实时监控仪表板** - 基础系统监控功能
- 🤖 **智能资源调度** - 简单的资源分配逻辑
- 🚨 **智能告警系统** - 基础告警功能
- 📈 **实时进度追踪** - 文件处理进度显示

### 核心功能
- 📄 **多格式支持**：PDF、TXT、DOCX、MD、XLSX、PPTX、CSV、HTML、JSON、ZIP
- 🌐 **网页抓取**：智能网页内容抓取，自动URL修复
- 🔍 **OCR识别**：扫描版PDF自动OCR，**GPU加速**，**CPU保护机制**
- 🔍 **语义检索**：基于向量数据库的智能检索
- 🎯 **智能重排序 (Re-ranking)**：Cross-Encoder 二次排序功能
- 🔍 **关键词增强 (BM25)**：关键词 + 语义双重检索
- 💬 **多轮对话**：保持上下文的连续对话
- 🎯 **引用来源**：显示答案来源和相关文档片段

### 配置与管理
- ⚙️ **灵活配置**：支持 OpenAI、Ollama 等多种 LLM
- 📦 **批量上传**：支持文件夹批量导入
- 💾 **持久化存储**：向量数据库和对话历史自动保存
- 🔒 **文件安全**：文件大小和类型验证（最大 100MB）

### 监控与工具
- 📊 **系统监控**：实时监控 CPU/GPU/内存/磁盘使用情况
- 🛡️ **CPU保护**：智能OCR进程控制，防止系统死机 ⭐ **v2.0新增**
- 📈 **性能统计**：学习型性能分析和优化建议 ⭐ **v2.1新增**
- 💻 **命令行工具**：kbllama - 终端中的知识库问答
- 🐳 **Docker 支持**：一键部署，开箱即用
- 📦 **macOS 打包**：独立应用，无需 Python 环境

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 4GB+ 内存
- 10GB+ 磁盘空间（包含模型缓存）

### 平台支持

- ✅ macOS (M1/M2/M3/M4, Intel)
- ✅ Linux (Ubuntu, CentOS, Debian)
- ✅ Windows (10/11)
- ✅ Docker (跨平台)

---

## 📦 安装部署

### macOS / Linux

#### 方式 1: 自动部署（推荐）

```bash
# 克隆项目
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max

# Linux 自动部署
chmod +x scripts/deploy_linux.sh
./scripts/deploy_linux.sh

# macOS 直接安装
pip install -r requirements.txt
```

#### 方式 2: 手动安装

```bash
# 1. 克隆项目
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max

# 2. 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir -p vector_db_storage chat_histories temp_uploads hf_cache app_logs suggestion_history
```

#### 启动应用

```bash
# 推荐方式（自动测试）
./start.sh

# 直接启动
streamlit run src/apppro.py
```

---

### Windows

#### 方式 1: 自动部署（推荐）

1. 下载项目：
   ```cmd
   git clone https://github.com/zhaosj0315/rag-pro-max.git
   cd rag-pro-max
   ```

2. 双击运行 `scripts\deploy_windows.bat`

3. 按提示完成部署

#### 方式 2: 手动安装

```cmd
# 1. 克隆项目
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max

# 2. 创建虚拟环境（可选）
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir vector_db_storage chat_histories temp_uploads hf_cache app_logs suggestion_history
```

#### 启动应用

```cmd
# 方式 1: 双击运行
start_windows.bat

# 方式 2: 命令行
streamlit run src/apppro.py
```

#### 创建桌面快捷方式

1. 右键 `start_windows.bat`
2. 发送到 → 桌面快捷方式
3. 双击快捷方式启动

---

### Docker 部署（跨平台）

#### 快速开始

```bash
# 1. 构建镜像
./scripts/docker-build.sh

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
# 浏览器打开：http://localhost:8501
```

#### Docker 管理

```bash
# 查看日志
docker logs -f rag-pro-max

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker exec -it rag-pro-max bash
```

---

## 🔧 部署验证

### 验证清单

运行以下命令验证部署：

```bash
# 1. 检查 Python 版本
python --version  # 应该 >= 3.8

# 2. 检查依赖
pip list | grep streamlit

# 3. 运行测试
python tests/factory_test.py

# 4. 测试启动
streamlit run src/apppro.py --server.headless=true
```

### 常见问题

#### Linux 特定问题

**问题**: `ModuleNotFoundError: No module named 'tkinter'`

**解决**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter
```

**问题**: 权限不足

**解决**:
```bash
chmod +x start.sh scripts/*.sh
```

#### Windows 特定问题

**问题**: `'python' 不是内部或外部命令`

**解决**:
1. 重新安装 Python
2. 勾选 "Add Python to PATH"
3. 重启命令提示符

**问题**: 端口被占用

**解决**:
```cmd
# 查看占用端口的进程
netstat -ano | findstr :8501

# 使用其他端口
streamlit run src/apppro.py --server.port 8502
```

---

## 🌐 访问应用

应用启动后会自动打开浏览器，或手动访问：

- **本地**: http://localhost:8501
- **局域网**: http://YOUR_IP:8501

### 局域网访问配置

编辑 `.streamlit/config.toml`（如不存在则创建）：

```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
```

---

### 本地运行

**推荐方式（自动测试）：**

```bash
./start.sh
```

这会先运行出厂测试，确保代码无误后再启动应用。

**直接启动（跳过测试）：**

```bash
streamlit run src/apppro.py
```

应用将在浏览器自动打开 http://localhost:8501

---

## 📖 使用指南

### 1. 快速开始 (推荐新手)

**最快方式 - 一键配置**:

1. 启动应用: `./scripts/start.sh`
2. 点击侧边栏顶部的 **"⚡ 一键配置（推荐新手）"** 按钮
3. 系统自动配置默认设置（Ollama + HuggingFace）
4. 创建知识库 → 上传文档 → 开始对话

**前提条件**: 需要先安装 Ollama
```bash
# macOS
brew install ollama
ollama serve

# 下载模型
ollama pull qwen2.5:7b
```

---

### 2. 手动配置 (高级用户)

在侧边栏 **"⚙️ 基础配置"** 中手动配置：

**OpenAI 配置：**
```
API Base URL: https://api.openai.com/v1
API Key: sk-your-api-key-here
模型: gpt-3.5-turbo 或 gpt-4
```

**Ollama 配置（本地模型）：**
```
API Base URL: http://localhost:11434
模型: qwen2.5:7b 或其他本地模型
```

---

### 3. 创建知识库

1. 在侧边栏输入知识库名称
2. 点击"创建新知识库"
3. 知识库创建后自动选中

### 4. 上传文档

**单文件上传：**
- 点击"上传文档"
- 选择文件（支持 PDF、DOCX、TXT、MD、XLSX、PPTX、CSV、HTML、JSON、ZIP）
- 等待处理完成

**批量上传：**
- 点击"批量上传文件夹"
- 选择包含文档的文件夹
- 系统自动处理所有支持的文件

### 4. 开始对话

1. 选择已创建的知识库
2. 在输入框输入问题
3. 查看答案和引用来源

### 5. 系统监控

在侧边栏点击 **📊 系统监控** 查看：
- CPU/内存/磁盘使用率
- GPU 状态（简化版）
- 当前进程信息
- 勾选"🔄 自动刷新"开启实时监控

**查看详细 GPU 信息**：
```bash
sudo python3 system_monitor.py
```

---

## 🛠️ KBLlama - 命令行知识库工具

### 安装

```bash
# 创建软链接到系统路径
sudo ln -s $(pwd)/kbllama /usr/local/bin/kbllama
```

### 使用示例

```bash
# 列出所有知识库
kbllama list

# 交互式对话
kbllama run my_knowledge_base
>>> 你的问题

# 单次查询
kbllama run my_knowledge_base "什么是 RAG？"

# 查看知识库信息
kbllama show my_knowledge_base
```

### 命令说明

| 命令 | 说明 |
|------|------|
| `kbllama list` | 列出所有可用的知识库 |
| `kbllama run <name> [query]` | 运行知识库问答 |
| `kbllama show <name>` | 显示知识库详细信息 |

---

## 🐳 Docker 部署（推荐）

### 快速开始

```bash
# 1. 构建镜像
./scripts/docker-build.sh

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
# 浏览器打开：http://localhost:8501
```

### Docker 管理

```bash
# 查看日志
docker logs -f rag-pro-max

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker exec -it rag-pro-max bash
```

### 资源配置

在 `docker-compose.yml` 中调整资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '12'      # 最大CPU核心数
      memory: 48G     # 最大内存
```

### 注意事项

- 镜像大小约 2.6GB
- 首次运行需要下载嵌入模型
- M4 Max GPU 不支持 Docker 透传，容器内只能使用 CPU
- 如需 GPU 加速，建议直接在 macOS 上运行

---

## 📦 macOS 打包

### 准备环境

```bash
pip install pyinstaller
pip install -r requirements.txt
```

### 执行打包

```bash
# 使用打包脚本（推荐）
chmod +x scripts/build_mac.sh
./scripts/build_mac.sh

# 或直接使用 PyInstaller
pyinstaller RAG_Pro_Max.spec --clean --noconfirm
```

### 输出位置

```
dist/RAG_Pro_Max.app
```

### 测试应用

```bash
open dist/RAG_Pro_Max.app
```

---

## 📊 性能基准

### 处理速度

| 文档类型 | 文档大小 | 处理时间 | 向量化速度 | CPU保护 |
|---------|---------|---------|-----------|---------|
| PDF | 10MB (100页) | ~45秒 | ~2页/秒 | ✅ 85%限制 |
| DOCX | 5MB (50页) | ~20秒 | ~2.5页/秒 | ✅ 自动调节 |
| TXT | 1MB | ~5秒 | ~200KB/秒 | ✅ 轻量处理 |

*测试环境：M4 Max (14核CPU + 32核GPU), 36GB 内存，CPU保护启用*

### 检索性能

| 知识库大小 | 文档数量 | 查询延迟 | 准确率 | CPU使用率 |
|-----------|---------|---------|--------|-----------|
| 小型 | <100 | <1秒 | 85-90% | <30% |
| 中型 | 100-1000 | 1-2秒 | 80-85% | <50% |
| 大型 | >1000 | 2-3秒 | 75-80% | <70% |

*v2.0.1优化: CPU保护机制确保系统稳定，查询性能稳定*

### 资源占用

| 场景 | CPU | GPU | 内存 | 系统稳定性 |
|------|-----|-----|------|------------|
| 空闲 | 5-10% | 0% | 2-3GB | ✅ 优秀 |
| 文档处理 | 60-85% | 99% | 10-15GB | ✅ 稳定 |
| 对话查询 | 10-20% | 50-70% | 5-8GB | ✅ 流畅 |

*v2.0.1: CPU使用率严格控制在85%以下，防止系统死机*

---

## 🏗️ 项目结构

```
.
├── src/                      # 源代码目录 (142个Python文件)
│   ├── apppro.py             # 主应用 (127K行)
│   ├── apppro_final.py       # 终极精简版 (40行) ⭐
│   ├── apppro_ultra.py       # 超精简版 (1958行)
│   ├── apppro_minimal.py     # 最小版 (2723行)
│   ├── rag_engine.py         # RAG 核心引擎 ⭐
│   ├── system_monitor.py     # 系统监控工具
│   ├── file_processor.py     # 文档处理模块
│   ├── metadata_manager.py   # 元数据管理
│   ├── chat_utils_improved.py # 聊天工具
│   ├── custom_embeddings.py  # 自定义嵌入
│   ├── api/                  # API接口 ⭐ (1个文件)
│   │   └── fastapi_server.py # FastAPI服务器 ⭐
│   ├── core/                 # 核心模块 ⭐ (16个文件)
│   │   ├── state_manager.py  # 状态管理
│   │   ├── main_controller.py # 主控制器 ⭐
│   │   ├── environment.py    # 环境配置 ⭐
│   │   ├── optimization_manager.py # 优化管理器 ⭐
│   │   ├── app_config.py     # 应用配置
│   │   ├── app_main.py       # 应用主体
│   │   └── business_logic.py # 业务逻辑
│   ├── ui/                   # UI 组件 ⭐ (26个文件)
│   │   ├── complete_sidebar.py # 完整侧边栏 ⭐
│   │   ├── main_interface.py # 主界面
│   │   ├── page_style.py     # 页面样式 ⭐
│   │   ├── message_renderer.py # 消息渲染器 ⭐
│   │   ├── performance_dashboard.py # 性能监控面板 ⭐
│   │   ├── sidebar_config.py # 侧边栏配置
│   │   ├── display_components.py # 展示组件
│   │   ├── model_selectors.py # 模型选择器
│   │   ├── config_forms.py   # 配置表单
│   │   ├── advanced_config.py # 高级配置
│   │   ├── document_preview.py # 文档预览
│   │   ├── performance_monitor.py # 性能监控
│   │   └── suggestion_panel.py # 建议面板
│   ├── processors/           # 文档处理器 ⭐ (12个文件)
│   │   ├── upload_handler.py # 上传处理
│   │   ├── enhanced_upload_handler.py # 增强上传处理 ⭐
│   │   ├── multimodal_processor.py # 多模态处理器 ⭐
│   │   ├── web_crawler.py    # 网页抓取器 ⭐
│   │   ├── index_builder.py  # 索引构建
│   │   ├── document_parser.py # 文档解析
│   │   └── summary_generator.py # 摘要生成
│   ├── app_logging/          # 日志系统 ⭐ (2个文件)
│   │   └── log_manager.py    # 日志管理器 ⭐
│   ├── config/               # 配置管理 ⭐ (10个文件)
│   │   ├── config_loader.py  # 配置加载器
│   │   ├── config_validator.py # 配置验证器
│   │   └── manifest_manager.py # 清单管理
│   ├── chat/                 # 聊天管理 ⭐ (8个文件)
│   │   ├── chat_engine.py    # 聊天引擎
│   │   ├── suggestion_manager.py # 建议管理
│   │   ├── suggestion_engine.py # 建议引擎
│   │   └── history_manager.py # 历史管理
│   ├── kb/                   # 知识库管理 ⭐ (11个文件)
│   │   ├── kb_manager.py     # 知识库管理器
│   │   ├── kb_loader.py      # 知识库加载器 ⭐
│   │   ├── kb_processor.py   # 知识库处理器
│   │   ├── kb_operations.py  # 知识库操作
│   │   └── document_viewer.py # 文档查看器
│   ├── query/                # 查询处理 ⭐ (6个文件)
│   │   ├── query_processor.py # 查询处理器 ⭐
│   │   ├── query_rewriter.py # 查询重写器 ⭐
│   │   └── query_handler.py  # 查询处理器
│   ├── queue/                # 队列管理 ⭐ (1个文件)
│   │   └── queue_manager.py  # 队列管理器 ⭐
│   ├── documents/            # 文档管理 ⭐ (1个文件)
│   │   └── document_manager.py # 文档管理器 ⭐
│   ├── summary/              # 摘要系统 ⭐ (1个文件)
│   │   └── auto_summary.py   # 自动摘要 ⭐
│   └── utils/                # 工具模块 (46个文件)
│       ├── memory.py         # 内存管理
│       ├── model_manager.py  # 模型管理 ⭐
│       ├── model_utils.py    # 模型工具 ⭐
│       ├── resource_monitor.py # 资源监控 ⭐
│       ├── gpu_optimizer.py  # GPU优化器 ⭐
│       ├── enhanced_cache.py # 增强缓存 ⭐
│       ├── document_processor.py # 文档处理
│       ├── parallel_executor.py # 并行执行 ⭐
│       ├── parallel_tasks.py # 并行任务
│       ├── query_cache.py    # 查询缓存
│       ├── error_handler.py  # 错误处理
│       ├── app_utils.py      # 应用工具 ⭐
│       ├── task_scheduler.py # 任务调度
│       ├── concurrency_monitor.py # 并发监控
│       ├── concurrency_manager.py # 并发管理
│       ├── smart_scheduler.py # 智能调度
│       ├── dynamic_batch.py  # 动态批量
│       ├── async_pipeline.py # 异步管道
│       ├── adaptive_throttling.py # 自适应限流
│       ├── vectorization_wrapper.py # 向量化包装
│       └── llm_manager.py    # LLM管理
├── tests/                    # 测试文件 (37个)
│   ├── factory_test.py       # 出厂测试 ⭐
│   ├── test_stage14_modules.py # Stage 14模块测试 ⭐
│   ├── test_stage15_modules.py # Stage 15模块测试 ⭐
│   ├── test_stage16_modules.py # Stage 16模块测试 ⭐
│   ├── test_documentation_feasibility.py # 文档可行性测试 ⭐
│   ├── test_chat_modules.py  # 聊天模块测试 ⭐
│   ├── test_config_modules.py # 配置模块测试 ⭐
│   ├── test_kb_modules.py    # 知识库模块测试 ⭐
│   ├── test_logging_module.py # 日志模块测试 ⭐
│   ├── test_v1.7_feasibility.py # v1.7可行性测试
│   ├── test_resource_protection.py # 资源保护测试
│   ├── test_planb_integration.py # 完整优化测试
│   └── ...                   # 其他测试
├── docs/                     # 文档目录 (114个文档)
│   ├── STAGE14_REFACTOR_SUMMARY.md # Stage 14重构总结 ⭐
│   ├── STAGE15_REFACTOR_SUMMARY.md # Stage 15重构总结 ⭐
│   ├── STAGE16_REFACTOR_SUMMARY.md # Stage 16重构总结 ⭐
│   ├── STAGE17_FINAL_OPTIMIZATION.md # Stage 17最终优化 ⭐
│   ├── MAIN_FILE_SIMPLIFICATION.md # 主文件简化 ⭐
│   ├── QUEUE_BLOCKING_FIX.md # 队列阻塞修复
│   ├── V1.7_FEATURES.md      # v1.7功能文档
│   ├── V1.7_MIGRATION_GUIDE.md # v1.7迁移指南
│   └── archive/              # 历史文档存档
├── tools/                    # 工具目录 (5个)
│   ├── test_coverage.py      # 测试覆盖率工具 ⭐
│   └── code_quality.py       # 代码质量工具 ⭐
├── scripts/                  # 脚本文件 (23个)
│   ├── build_mac.sh          # macOS 打包脚本
│   ├── docker-build.sh       # Docker 构建脚本
│   ├── start.sh              # 启动脚本
│   ├── test.sh               # 测试脚本
│   ├── verify_integration.sh # 集成验证脚本
│   └── verify_planb.sh       # 方案B验证脚本
├── config/                   # 配置文件
│   ├── app_config.json       # 应用配置
│   ├── rag_config.json       # RAG 配置
│   └── projects_config.json  # 项目配置
├── kbllama                   # 命令行知识库工具
├── requirements.txt          # Python 依赖
├── RAG_Pro_Max.spec          # PyInstaller 配置
├── Dockerfile                # Docker 镜像配置
├── docker-compose.yml        # Docker 编排配置
├── README.md                 # 项目文档
├── LICENSE                   # 许可证
├── .gitignore                # Git 忽略文件
├── vector_db_storage/        # 向量数据库存储（运行时生成）
├── chat_histories/           # 对话历史（运行时生成）
├── temp_uploads/             # 临时上传文件（运行时生成）
├── hf_cache/                 # HuggingFace 模型缓存（运行时生成）
├── app_logs/                 # 应用日志（运行时生成）
└── dist/                     # 打包输出（构建时生成）
    └── RAG_Pro_Max.app       # macOS 应用
```

### 📊 项目统计

- **总文件数**: 135个Python文件 (清理后精简架构)
- **总代码行数**: 28,500+行 (+2,100行v2.3功能)
- **模块化程度**: 95%+
- **测试覆盖**: 36个测试文件 (+5个v2.3测试)
- **文档数量**: 135个文档文件 (+8个v2.3文档)
- **主文件行数**: 2,411行 (功能完整版)

### 🏗️ 架构特点

- **135模块架构**: 完全模块化设计，单一职责原则
- **4层应用入口**: apppro_final.py (40行) → apppro_ultra.py → apppro_minimal.py → apppro.py
- **12大功能域**: api, core, ui, processors, app_logging, config, chat, kb, query, utils, monitoring, documents
- **完整测试体系**: 36个测试文件，覆盖所有核心模块
- **基础功能完整**: 核心功能实现，需要增强测试覆盖

---

## ⚙️ 配置文件

### rag_config.json

RAG 检索参数配置：

```json
{
  "chunk_size": 500,           // 文档分块大小
  "chunk_overlap": 50,         // 分块重叠长度
  "top_k": 5,                  // 检索文档数量
  "similarity_threshold": 0.7  // 相似度阈值
}
```

### app_config.json

应用默认配置：

```json
{
  "default_model": "gpt-3.5-turbo",
  "api_base": "https://api.openai.com/v1",
  "temperature": 0.7
}
```

---

## 🧪 出厂测试

### 快速测试

每次修改代码后，运行出厂测试确保功能正常：

```bash
# 方式 1：使用快捷脚本
./scripts/test.sh

# 方式 2：直接运行测试
python3 tests/factory_test.py
```

### 测试覆盖

- ✅ **44 项测试**：覆盖所有核心功能
- 🔍 **10 大类别**：环境、配置、模块、日志、文档、向量库、LLM、存储、安全、性能
- ⚡ **15-20 秒**：完整测试运行时间

### 测试结果示例

```
============================================================
  测试结果汇总
============================================================
✅ 通过: 44/44
❌ 失败: 0/44
⏭️  跳过: 0/44

✅ 所有测试通过！系统可以发布。
```

详细说明请查看 [TESTING.md](TESTING.md)

---

## 🔧 技术栈

### 核心框架
- **前端**: Streamlit 1.x
- **向量数据库**: ChromaDB (via LlamaIndex)
- **文档处理**: LlamaIndex Core
- **网页抓取**: BeautifulSoup + Requests
- **OCR引擎**: PaddleOCR (GPU加速)

### 模型支持
- **嵌入模型**: BAAI/bge-small-zh-v1.5 (HuggingFace)
- **LLM**: 
  - OpenAI GPT-3.5/GPT-4
  - Ollama (本地模型)
  - 其他 OpenAI 兼容接口

### 架构特点
- **142个Python模块** - 完全模块化设计
- **12大功能域** - api, core, ui, processors, logging, config, chat, kb, query, utils
- **统一处理流程** - 文件上传和网页抓取共用后端逻辑
- **基础功能完整** - 核心功能实现，需要增强测试覆盖

---

## 🏗️ 项目架构

### 📊 项目统计

- **总文件数**: 266个Python文件 (实际统计)
- **总代码行数**: 52,104行 (实际统计)
- **模块化程度**: 95%+
- **测试覆盖**: 41个测试文件
- **文档数量**: 233个文档文件 (实际统计)
- **主要模块**: 18个功能模块

### 🎯 数据处理流程

```
┌─────────────────┐  ┌─────────────────┐
│   📄 文件上传    │  │   🌐 网页抓取    │
│  • PDF/DOCX     │  │  • HTML解析     │
│  • TXT/MD       │  │  • 内容提取     │
│  • Excel/PPT    │  │  • 保存为TXT    │
└─────────┬───────┘  └─────────┬───────┘
          │                    │
          └──────────┬─────────┘
                     │
          ┌─────────▼─────────┐
          │  📁 统一文件处理   │
          │  file_processor   │
          └─────────┬─────────┘
                    │
          ┌─────────▼─────────┐
          │  🧠 向量化处理    │
          │  index_builder    │
          └─────────┬─────────┘
                    │
          ┌─────────▼─────────┐
          │  🗄️ 向量数据库     │
          │  ChromaDB        │
          └───────────────────┘
```

---

## 🚀 性能优化

### 多核优化
- 线程数：最多 80 线程（根据 CPU 可用率动态调整）
- 进程数：最多 12 进程（元数据提取）
- CPU 阈值：30%（激进使用资源）

### 向量数据库优化
- 调整 `chunk_size` 和 `chunk_overlap`
- 使用更高效的嵌入模型
- 定期清理无用的知识库

### 内存优化
- 限制单次上传文件大小（100MB）
- 及时清理临时文件
- 使用流式处理大文件

---

## 📝 日志系统

### 日志位置

所有日志保存在 `app_logs/` 目录，按日期命名：
```
app_logs/
  └── log_20241207.jsonl
```

### 日志内容

- **模型加载**：嵌入模型和 LLM 加载状态
- **知识库处理**：文件扫描、解析、向量化全流程
- **查询对话**：用户提问、检索、回答生成
- **错误信息**：所有异常和错误详情

### 查看日志

```bash
# 查看今日日志
python show_logs.py

# 详细日志分析
python view_logs.py

# 查看指定日期
python view_logs.py --date 20241201

# 筛选查询对话
python view_logs.py --stage 查询对话

# 查看统计信息
python view_logs.py --stats
```

---

## ❓ 常见问题

<details>
<summary><b>Q: 上传文档后没有反应？</b></summary>

A: 检查文档格式是否支持，查看控制台是否有错误信息。支持的格式：PDF、TXT、DOCX、MD、XLSX、PPTX、CSV、HTML、JSON、ZIP。
</details>

<details>
<summary><b>Q: 对话没有引用来源？</b></summary>

A: 确保知识库中有文档，且相似度阈值设置合理。可以在 `rag_config.json` 中调整 `similarity_threshold`。
</details>

<details>
<summary><b>Q: 如何使用本地模型？</b></summary>

A: 
1. 安装 Ollama: `brew install ollama`
2. 启动本地模型: `ollama run qwen2.5:7b`
3. 配置 API Base 为 `http://localhost:11434`
</details>

<details>
<summary><b>Q: 如何清理缓存？</b></summary>

A: 删除以下目录：
```bash
rm -rf vector_db_storage/
rm -rf chat_histories/
rm -rf temp_uploads/
```
</details>

<details>
<summary><b>Q: 为什么 CPU 只用了 37%？</b></summary>

A: GPU 是瓶颈。向量化任务主要靠 GPU 计算，CPU 只是准备数据。GPU 已经 99% 满载，CPU 再多也无法提升性能。
</details>

<details>
<summary><b>Q: 如何查看 GPU 详细信息？</b></summary>

A: 使用命令 `sudo python3 system_monitor.py`。Streamlit 内置监控只能显示简化信息（无需 sudo）。
</details>

---

## 🗺️ 路线图

### v2.0 (已完成) ✅
- [x] **增量更新** - 智能检测文件变化，无需重建整个知识库 ✅
- [x] **API 接口扩展** - 完整RESTful API，支持程序化调用 ✅
- [x] **多模态支持** - 图片OCR、表格提取 ✅
- [x] **智能启动** - 自动检测功能，向后兼容 ✅

### v1.8 (已完成) ✅
- [x] RESTful API接口 ✅
- [x] 性能监控增强 ✅
- [x] 紧凑UI布局 ✅
- [x] 生产就绪 ✅

### v1.1 (已完成) ✅
- [x] Re-ranking 重排序功能 ✅
- [x] 混合检索（BM25 + 向量）✅
- [x] 知识库搜索/过滤 ✅
- [x] 对话历史管理（导出、统计）✅
- [x] 首次使用引导 ✅
- [x] GPU利用率优化 ✅
- [x] 统一内存管理 ✅

### v1.2 (已完成) ✅
- [x] 增量更新 ✅
- [x] 缓存机制 ✅
- [x] 查询改写 ✅
- [x] 使用统计 ✅
- [x] 质量评估 ✅

### v2.1 (已完成) ✅
- [x] **实时文件监控** - 使用 watchdog 自动检测文件变化 ✅
- [x] **批量 OCR 优化** - 并行处理多个图片 ✅
- [x] **表格智能解析** - 自动识别表格结构和语义 ✅
- [x] **多模态向量化** - 图片和表格的向量表示 ✅
- [x] **查询并行优化** - 节点处理阈值降至2，速度提升30-37% ✅

### v2.2 (规划中)
- [ ] 多用户权限管理
- [ ] 分布式部署支持
- [ ] 企业级安全认证
- [ ] 高级分析仪表板

---

## 📄 更新日志

### v2.3.1 (2025-12-14) - 安全增强版
- 🛑 **安全熔断机制** - 网页抓取限制5万页，防止系统崩溃
- 🧹 **自动清理机制** - 启动时自动清理24小时以上临时文件
- ⏹ **停止按钮功能** - 支持中断对话生成和长时间任务
- 📄 **引用页码显示** - PDF文档显示具体页码信息，精确定位
- 🔧 **PDF页码读取器** - 新增支持页码记录的PDF处理器
- ✅ **完整测试覆盖** - 新增功能验证测试，100%通过
- 📚 **文档完善** - 新增功能实现总结和使用说明

### v2.3.0 (2025-12-12) - 智能监控版
- 📊 **实时监控仪表板** - 可视化CPU/内存使用率和趋势图
- 🤖 **智能资源调度** - 基于历史数据自适应优化资源分配
- 🚨 **智能告警系统** - 多级告警机制和桌面通知
- 📈 **实时进度追踪** - 可视化文件处理进度和任务控制
- 🎨 **交互式图表** - Plotly图表和数据可视化
- 🧠 **机器学习** - 基于性能数据的自动优化

### v2.2.2 (2025-12-12) - 资源保护增强版
- 🛡️ **资源保护优化** - CPU阈值降低至75%，内存阈值85%
- 📊 **OCR日志记录系统** - 详细记录处理文件数量和耗时
- 📈 **处理统计功能** - 实时统计处理速度和效率
- 🔧 **日志查看工具** - view_ocr_logs.py 查看处理日志
- 🚀 **性能监控** - 双重资源监控，防止系统死机
- 📝 **详细追踪** - 记录每个处理步骤和系统状态

### v2.2.1 (2025-12-11) - UI优化版
- 🎨 **界面样式全面优化** - 现代化设计，提升用户体验
- 📱 **标签页显示修复** - 解决标签页被挤压问题
- 🔧 **重复功能清理** - 主页和配置页功能完全分离
- 📏 **空白区域优化** - 紧凑布局，提升空间利用率
- ✨ **交互效果增强** - 悬停动画，按钮反馈优化
- 📐 **响应式设计** - 支持不同屏幕尺寸

### v2.2.1 (2025-12-11) - 标签页迁移版
- 🎯 **配置标签页迁移完成** - 所有配置功能迁移到专门标签页
- ⚙️ **功能完全分离** - 主页专注RAG，配置页专注模型设置
- 🔧 **组件冲突解决** - 修复所有重复key和组件冲突问题
- 🎨 **界面优化** - 配置默认展开，辅助功能默认收起
- 🚀 **自动跳转** - 知识库构建完成后自动切换到新知识库
- ✅ **功能完整性** - 100%保持原有配置功能和默认值
- 📊 **用户体验提升** - 清晰的功能分离和操作流程

### v2.1.0 (2025-12-11) - 智能化增强版
- 🧠 **自适应CPU调度** - 基于历史数据智能调整处理策略
- 📊 **实时进度监控** - 可视化处理状态，支持暂停/继续操作
- 🚀 **GPU OCR加速** - PaddleOCR GPU版本，处理速度提升2-5倍
- 🎛️ **增强OCR优化器** - 统一集成三大智能功能
- 📈 **性能学习系统** - 系统自动学习并优化处理策略
- 🔧 **智能设备检测** - 自动检测CUDA/MPS/CPU并优化配置
- 📱 **用户体验提升** - 实时反馈，可控制处理流程

### v2.0.1 (2025-12-11) - CPU保护增强版
- 🛡️ **CPU保护机制升级** - 防止系统死机，确保稳定运行
- 🚨 **紧急停止机制** - 连续高CPU时自动停止OCR处理
- ⚡ **进程数优化** - 最多4进程，保留更多资源给系统
- 🔥 **CPU阈值降低** - 85%开始保护（原95%），更加安全
- ⏱️ **超时保护** - OCR处理10分钟超时，防止长时间占用
- 🧹 **资源清理** - 自动清理临时文件，防止磁盘占用
- 📊 **实时监控** - 0.5秒间隔监控，快速响应CPU变化
- 🆘 **紧急脚本** - `emergency_cpu_stop.py` 手动停止所有OCR进程

### v2.0.0 (2025-12-10) - 重大功能更新
- ✨ **增量更新** - 智能检测文件变化，无需重建整个知识库
- 🎨 **多模态支持** - 图片OCR识别、表格数据提取
- 🔌 **API接口扩展** - 完整RESTful API，支持程序化调用
- 🚀 **智能启动** - 自动检测v2.0功能，向后兼容v1.8
- 🐛 **队列修复** - 修复问答队列阻塞问题，添加重置功能
- 📖 **摘要优化** - 修复摘要标题截取问题，显示更完整内容
- 🧪 **完整测试** - 9个v2.0功能测试，100%通过
- 📚 **详细文档** - 完整的v2.0功能文档和使用指南

### v2.1.0 (2025-12-10) - 多核优化版本
- 📁 **实时文件监控** - 自动检测文件变化并触发增量更新
- 🔍 **批量OCR优化** - 并行处理多个图片文件，GPU加速OCR识别
- 📊 **表格智能解析** - 自动识别表格结构，语义化表格内容
- 🎯 **多模态向量化** - 图片内容向量表示，跨模态检索支持
- ⚡ **查询并行优化** - 节点处理阈值降至2，查询速度提升30-37%

### v1.8.0 (2025-12-10) - 生产就绪版本
- 🔌 **RESTful API接口** - 完整的API服务，支持程序化调用
- 📊 **性能监控增强** - 实时查询性能和统计信息
- 🎨 **紧凑UI布局** - 优化界面布局，提升用户体验
- ✅ **基础功能完整** - 核心功能实现，测试覆盖需要改进

### v1.7.0 (2025-12-09) - 并发优化（最终版）
- ⚡ **异步向量化管道** - CPU和GPU流水线并行，加速比1.7x
- 📊 **动态批量优化** - 自动调整batch size，内存占用减少33%
- 🎯 **智能任务调度** - 根据任务类型分配资源，利用率提升20-30%
- 🚀 **性能提升** - 处理速度提升40%，GPU利用率提升15%
- 🔧 **错误处理增强** - 完整的异常处理和资源清理机制
- 💾 **GPU显存优化** - 智能检测GPU显存，避免OOM
- 📦 新增 4 个模块（async_pipeline, dynamic_batch, smart_scheduler, concurrency_manager）
- 🧪 测试：5/5 可行性测试通过
- 📚 完整文档（功能文档、可行性报告、迁移指南）
- ✅ 专家审查：10位专家审查，6个高优先级问题已修复

### v1.6.0 (2025-12-09) - 最终版
- ✨ **查询改写 (Query Rewriting)** - 自动优化用户查询，提升检索准确率 5-10%
- ✨ **文档预览 (Document Preview)** - 上传前/后预览文档，带翻页功能（每页10个）
- ✨ **智能命名 (Smart Naming)** - 自动生成有意义的知识库名称
- 🔧 **队列处理优化** - 自动处理队列中的问题，避免中断
- 🔧 **知识库切换保护** - 处理问题时禁止切换，避免对话中断
- 📦 新增 3 个模块（query_rewriter, document_viewer, document_preview）
- 🧪 测试：2/2 单元测试通过
- 📚 完整功能文档（docs/V1.6_FEATURES.md）

### v1.5.1 (2025-12-09)
- ✨ **性能监控面板** - 实时查看查询性能和统计信息
- ✨ **推荐问题优化** - 自定义推荐和历史管理
- ✨ **错误恢复机制** - 自动重试和友好提示
- 📦 新增 3 个模块（+500 行代码）
- 🧪 测试：6/6 可行性测试通过，58/63 出厂测试通过

### v1.5.0 (2025-12-09)
- 🚀 **查询缓存系统** - 提升重复查询速度 80%+
- 📦 新增 3 个独立模块（query_cache, suggestion_engine, error_handler）
- ✨ **扩展 LogManager** - 新增 10+ 个日志方法
- 🐛 修复 terminal_logger 引用问题
- 🧪 测试：6/6 可行性测试通过，58/63 出厂测试通过

### v1.4.4 (2025-12-09)
- 🐛 **修复追问推荐按钮导致回答消失的 bug**
- 🐛 **修复队列处理导致回答无法显示的问题**
- ✨ 推荐问题在回答后立即显示（chat_message 块外）
- ✨ 队列处理改为手动触发模式，避免内容丢失
- 📊 推荐问题基于上下文生成，支持知识库验证
- 🎯 用户体验优化：可控制处理节奏，查看每个回答

### v1.4.2 (2025-12-09)
- 🎉 **Stage 10-12 重构完成** - 全部 12 个阶段完成
- 📦 新增 3 大模块系统：logging/、config/、chat/
- 🏗️ 提取 16 个模块，共 2572 行代码
- ✅ 新增 20 个单元测试（100% 通过）
- 🧹 清理旧模块和临时文件
- 📚 完整文档更新
- 🎯 代码质量：⭐⭐⭐⭐⭐（生产就绪）

### v1.4.0 (2025-12-09)
- 🔧 Stage 6 并行执行重构完成
- 📦 提取并行执行模块（ParallelExecutor）
- 🚀 统一并行接口，智能判断串行/并行
- 📊 阈值优化：元数据 100→50，节点 20→10
- 🎯 新增 CPU 负载感知，避免过载
- 📈 中型知识库性能提升 30-40%
- ✅ 代码质量提升 170%（模块化、可测试）
- 📝 新增问题队列机制，支持多问题排队
- 🧪 新增 5 个单元测试
- 📚 完整文档（使用指南、对比分析）

### v1.3.1 (2025-12-09)
- ⚡ Stage 5.3 用户体验优化完成
- 🎯 元数据提取默认关闭（默认快 30%）
- 🚀 问答流程流畅度优化（延迟降低 40-50%）
- 💬 流式输出更流畅（移除频繁资源检查）
- 🔄 缓存维度检测（避免重复检查）
- 📈 累计性能提升 40-50%（Stage 5.1 + 5.2 + 5.3）
- ✅ 向后兼容，功能完整保留

### v1.3.0 (2025-12-09)
- ⚡ Stage 5 性能优化完成（5.1 + 5.2）
- 🚀 元数据提取可选化（可加速 30%）
- 🚀 摘要队列异步化（加速 7.5%）
- 📈 累计性能提升 35%
- ⚙️ 新增性能配置选项
- ✅ 向后兼容，默认启用
- 📊 代码增加 32 行（功能增强）

### v1.2.1 (2025-12-09)
- 🔧 **完整重构完成** - Stage 1-4 全部完成并集成
- 📦 提取 13 个模块，共 2289 行代码
- 🏗️ 主文件减少 **709 行** (-22.1%)
- 📊 代码行数: 3204 → 2495 行
- ✅ 删除重复代码 118 行
- ✅ 出厂测试 61/67 通过
- 📝 完整重构文档（docs/REFACTOR_SUMMARY.md）

### v1.2.0 (2025-12-08)
- 🔧 Stage 3 UI组件重构完成（-299行，-8.6%）
- 📦 提取6个UI模块（display_components, model_selectors, config_forms, advanced_config）
- 🏗️ 新增状态管理系统（state_manager.py, 138行）
- ⚡ 修复OCR多进程调度问题（CPU 100%满载）
- 🚀 移除OCR页数限制（50页→无限制）
- ✅ 新增UI组件单元测试

### v1.1.5 (2025-12-08)
- 🔧 Stage 2 重构完成
- ⭐ 提取 RAG 核心引擎（rag_engine.py, 286行）
- 📊 提取资源监控模块（utils/resource_monitor.py, 114行）
- 🔧 提取模型工具模块（utils/model_utils.py, 226行）
- ✅ 新增 11 个单元测试
- 📦 代码更模块化、可维护、可测试

### v1.1.4 (2025-12-08)
- 🔧 模型管理重构（提取到 utils/model_manager.py）
- 🐛 修复嵌入模型维度不匹配问题（OpenAI 默认模型干扰）
- ✨ 新增模型加载日志和错误处理
- 📦 代码模块化，减少主文件 ~140 行
- 🧪 出厂测试新增模型管理器测试

### v1.1.3 (2025-12-08)
- ✨ GPU利用率优化（29.6% → 80-99%）
- 🧹 统一内存管理（cleanup_memory）
- 💾 显存自动清理（CUDA/MPS）
- 🚀 torch.compile 编译加速
- 📊 新增7项出厂测试

### v1.1.2 (2025-12-08)
- ✨ 效果对比模式
- 📊 使用统计可视化
- 🎨 视觉反馈优化
- 🔧 重复key检查工具

### v1.1.1 (2025-12-07)
- ⚡ 一键配置（新手模式）
- 💡 专业术语通俗化
- 📂 侧边栏分组优化

### v1.0.0 (2024-11-30)
- ✨ 初始版本发布
- 📄 支持多种文档格式
- 🔍 向量检索功能
- 💬 多轮对话支持
- 📦 macOS 打包支持
- 📊 系统监控面板
- 🔒 文件上传安全验证
- 💻 多核优化（80 线程）

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork 项目**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **提交 Pull Request**

### 贡献类型

- 🐛 报告 Bug
- 💡 提出新功能
- 📝 改进文档
- 🔧 提交代码
- 🌐 翻译文档

### 开发规范

- 遵循 PEP 8 代码风格
- 添加必要的注释和文档
- 编写单元测试
- 更新 README（如果需要）

---

## 📚 完整文档

### 📖 核心文档
- [📋 文档索引](DOCS_INDEX.md) - 所有文档导航
- [❓ 常见问题](FAQ.md) - FAQ 和故障排除
- [🚀 部署指南](DEPLOYMENT.md) - 各种部署方式
- [🤝 贡献指南](CONTRIBUTING.md) - 如何贡献代码
- [📝 更新日志](CHANGELOG.md) - 版本变更记录

### 🎯 功能文档
- [🎯 Re-ranking](RERANK.md) - 重排序功能详解
- [🔍 BM25 混合检索](BM25.md) - 混合检索说明
- [✨ 用户体验优化](UX_IMPROVEMENTS.md) - UX 功能
- [👋 首次使用引导](FIRST_TIME_GUIDE.md) - 新手指南

### 🧪 测试文档
- [🧪 测试系统](TESTING.md) - 出厂测试说明
- [🔄 自动测试](AUTO_TEST.md) - 自动化测试配置
- [🚀 安全启动](START.md) - 启动前测试

---

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📧 联系方式

- **项目地址**: [https://github.com/yourusername/rag-pro-max](https://github.com/yourusername/rag-pro-max)
- **问题反馈**: [Issues](https://github.com/yourusername/rag-pro-max/issues)
- **讨论交流**: [Discussions](https://github.com/yourusername/rag-pro-max/discussions)

---

## 🙏 致谢

感谢以下开源项目：

- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [LlamaIndex](https://www.llamaindex.ai/) - LLM 应用框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [HuggingFace](https://huggingface.co/) - 模型托管平台

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by [Your Name]

</div>
