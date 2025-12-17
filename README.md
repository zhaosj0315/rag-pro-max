# RAG Pro Max - 智能文档问答系统

<div align="center">

![Version](https://img.shields.io/badge/version-v2.4.4-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Docker-lightgrey.svg)

**🔥 开源免费的企业级RAG应用 | 支持本地部署 | 无需联网使用 | 生产就绪**

基于 Streamlit + LlamaIndex 的智能文档问答系统，支持多格式文档上传，提供语义检索和AI问答功能。

**🎯 核心优势**: 本地部署 • 数据安全 • 多模态支持 • GPU加速 • 四层架构 • 生产就绪

</div>

---

## ✨ 核心功能

### 📄 文档处理
- **多格式支持**: PDF、TXT、DOCX、MD、XLSX、PPTX、CSV、HTML、JSON、ZIP
- **OCR识别**: 扫描版PDF自动OCR，GPU加速，CPU保护机制
- **批量上传**: 支持文件夹批量导入，智能目录选择
- **文件验证**: 大小限制100MB，类型安全检查

### 🌐 网页抓取
- **智能抓取**: 自动URL修复，递归深度控制
- **内容分析**: AI自动识别网站类型，推荐最佳参数
- **质量筛选**: 智能内容过滤，去重处理
- **安全机制**: 5万页限制，防止系统崩溃

### 🔍 智能检索
- **语义检索**: 基于向量数据库的智能检索
- **混合检索**: BM25 + 语义双重检索
- **智能重排序**: Cross-Encoder二次排序
- **引用来源**: 显示答案来源和页码信息

### 💬 对话系统
- **多轮对话**: 保持上下文的连续对话
- **流式输出**: 实时生成回答，支持中断
- **追问推荐**: 智能生成相关问题
- **历史管理**: 对话记录自动保存

---

## 🏗️ 系统架构

### 四层架构设计
```
表现层 (UI Layer)     - Streamlit界面组件
    ↓
服务层 (Service)      - 业务逻辑服务
    ↓  
公共层 (Common)       - 通用工具模块
    ↓
工具层 (Utils)        - 底层工具函数
```

### 核心模块
- **apppro.py** - 主应用入口 (5,700+ 行)
- **services/** - 文件服务、知识库服务、配置服务
- **processors/** - 文档处理器、网页爬虫 (23个模块)
- **ui/** - 用户界面组件 (39个模块)
- **utils/** - 工具函数库 (59个模块)

---

## 🚀 快速开始

### 环境要求
- **Python**: 3.8+ (推荐 3.10+)
- **内存**: 4GB+ (推荐 8GB+)
- **磁盘**: 10GB+ (包含模型缓存)
- **GPU**: 可选 (CUDA/MPS支持)

### 安装部署

#### macOS/Linux 自动安装
```bash
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max
./scripts/deploy_linux.sh  # Linux
pip install -r requirements.txt  # macOS
```

#### Windows 自动安装
```cmd
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max
scripts\deploy_windows.bat
```

#### Docker 部署
```bash
./scripts/docker-build.sh
docker-compose up -d
# 访问: http://localhost:8501
```

### 启动应用
```bash
# 推荐方式（含测试）
./start.sh

# 直接启动
streamlit run src/apppro.py
```

---

## ⚙️ 配置说明

### 模型配置
支持多种LLM后端：
- **OpenAI**: GPT-3.5/GPT-4
- **Ollama**: 本地模型 (qwen2.5:7b等)
- **其他**: OpenAI兼容接口

### 核心配置文件
```
config/
├── app_config.json      # 应用配置
├── rag_config.json      # RAG参数
└── scheduler_config.json # 调度配置
```

### 环境变量
```bash
# 禁用详细日志
export PADDLE_LOG_LEVEL=50
export GLOG_minloglevel=3

# 线程控制
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
```

---

## 📊 技术栈

### 核心框架
- **streamlit** ≥1.28.0 - Web界面
- **llama-index** ≥0.9.0 - RAG引擎
- **chromadb** ≥0.4.0 - 向量数据库
- **sentence-transformers** ≥2.2.0 - 嵌入模型

### 文档处理
- **PyMuPDF** - PDF处理
- **python-docx** - Word文档
- **openpyxl** - Excel文档
- **paddleocr** - OCR识别

### AI/ML
- **torch** ≥2.0.0 - 深度学习
- **transformers** ≥4.30.0 - 模型库
- **ollama** ≥0.1.0 - 本地LLM

---

## 🔧 API接口

### RESTful API
```python
# 启动API服务
python src/api/fastapi_server.py

# 主要端点
GET  /health              # 健康检查
POST /query               # 查询接口
GET  /knowledge-bases     # 知识库列表
POST /upload              # 文件上传
```

### 核心类接口
```python
# 文件服务
from src.services.file_service import FileService
file_service = FileService()
result = file_service.validate_file(file_path)

# 知识库服务  
from src.services.knowledge_base_service import KnowledgeBaseService
kb_service = KnowledgeBaseService()
kb_list = kb_service.list_knowledge_bases()

# 配置服务
from src.services.config_service import get_config_service
config = get_config_service()
model = config.get_default_model()
```

---

## 📈 性能基准

### 处理速度
| 文档类型 | 大小 | 处理时间 | GPU加速 |
|---------|------|---------|---------|
| PDF | 10MB | ~45秒 | ✅ 2-5x |
| DOCX | 5MB | ~20秒 | ✅ 自动 |
| 网页 | 100页 | ~2分钟 | ✅ 并行 |

### 系统资源
| 场景 | CPU | GPU | 内存 |
|------|-----|-----|------|
| 空闲 | 5-10% | 0% | 2-3GB |
| 处理 | 60-85% | 99% | 10-15GB |
| 查询 | 10-20% | 50-70% | 5-8GB |

---

## 🧪 测试验证

### 出厂测试
```bash
# 运行完整测试
python tests/factory_test.py

# 测试覆盖: 84/96 通过 (87.5%)
# 测试类别: 环境、配置、模块、文档、向量库等
```

### 功能验证
- ✅ 文档上传和处理
- ✅ 知识库构建
- ✅ 语义检索
- ✅ 多轮对话
- ✅ 网页抓取

---

## 📝 使用指南

### 1. 创建知识库
1. 启动应用后，在侧边栏输入知识库名称
2. 点击"创建新知识库"
3. 知识库创建后自动选中

### 2. 上传文档
- **单文件**: 点击"上传文档"选择文件
- **批量**: 点击"批量上传文件夹"
- **网页**: 输入URL进行内容抓取

### 3. 开始对话
1. 选择已创建的知识库
2. 输入问题
3. 查看答案和引用来源

---

## 🛠️ 开发指南

### 项目结构
```
src/
├── apppro.py           # 主应用 (5,700+ 行)
├── services/           # 业务服务层
├── common/             # 公共工具层  
├── ui/                 # 界面组件
├── processors/         # 文档处理
├── utils/              # 工具函数
└── core/               # 核心控制
```

### 扩展开发
```python
# 添加新的文档处理器
class CustomProcessor:
    def process(self, file_path: str) -> str:
        # 处理逻辑
        return processed_content

# 注册处理器
from src.processors import register_processor
register_processor('.custom', CustomProcessor)
```

---

## 📚 文档资源

- [📋 部署指南](DEPLOYMENT.md)
- [🧪 测试说明](TESTING.md) 
- [❓ 常见问题](FAQ.md)
- [🤝 贡献指南](CONTRIBUTING.md)
- [📝 更新日志](CHANGELOG.md)
- [🔧 维护标准](DOCUMENTATION_MAINTENANCE_STANDARD.md)
- [🔒 推送规范](NON_ESSENTIAL_PUSH_STANDARD.md)

---

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢以下开源项目：
- [Streamlit](https://streamlit.io/) - Web应用框架
- [LlamaIndex](https://www.llamaindex.ai/) - RAG框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [HuggingFace](https://huggingface.co/) - 模型平台

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by RAG Pro Max Team

</div>
