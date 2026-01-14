# RAG Pro Max

<div align="center">

**Languages:** 
[🇨🇳 中文](README.md) | 
[🇺🇸 English](README.en.md)

</div>

---

# RAG Pro Max - 智能文档问答系统

**版本**: v5.9.4  
![Version](https://img.shields.io/badge/version-v5.9.4-brightgreen)

# 🚀 RAG Pro Max v5.9.4
### 🎨 极致可视化画板与业务看板 (v5.9.4)
- **多态标签页**: 深度集成 Plotly，支持 6 大维度手动切换（AI推荐、业务转化、层级分布等）。
- **指标实时监控**: 顶部自动展示平均值、总计值等核心 KPI 指标卡。
- **高保真绘图**: 支持 **漏斗图 (Funnel)**、**矩形树图 (Treemap)**、**雷达图** 及交互式数据表。

### 🔋 物理级数据主权保护 (v5.9.4)
- **零数据丢失**: 重构了索引构建逻辑，保护原始文献与 SQL 数据库不被误删。
- **真数采样 SQL**: AI 编写脚本前自动采样真实数据样例，错误率降低 90% 以上。
- **语法自动修复**: 全面支持 `ORDER BY` 等复杂语法的后台自动容错与自愈。

### 🔄 会话管理与现场恢复 (v5.6.8)
- **全量对话打捞**: 修正了全量资产包（ZIP）的搜索范围。导出工具现在能从根目录精准识别该库名下的所有历史 JSON 会话，并同步生成人类可读的 MD 纪要。
- **路径深度自愈**: 针对 UI 脱敏导致的挂载失败，实现了模糊前缀匹配算法。系统能自动在磁盘上找回缺失前缀的物理文件夹。

### 🕷️ 高保真网页爬虫 (v5.6.5)
- **阿里云深度适配**: 在 `HtmlToMarkdown` 中集成 `.content-wrapper` 等专有容器选择器，完美剥离文档导航干扰。
- **html2text 引擎**: 引入 `html2text` 作为高保真后端，设置 `body_width=0`，确保长行代码块和复杂技术表格在 Markdown 中不产生错位。
- **无限链路打捞**: 解除了单页 8 链接提取限制，支持针对特定 URL 路径前缀的大规模自动化抓取。

### 📜 工业级日志引擎 (v5.6.5)
- **权限自愈 (CHMOD 666)**: 强制将新生成的 `.jsonl` 日志权限设为 `666`，彻底解决 macOS 下因 Root 启动导致的普通用户“打不开日志”问题。
- **日志显示增强**: 监控面板新增“终端日志”子标签，支持大文件（MB级）末尾快速读取，避免 UI 卡死。

### 📦 数据主权与全量导出 (v5.5.8)
- **终极五福资产包**: 一键导出 01-06 完整结构，包含原始文献、历史对话、战略模型、元数据及索引。

### 🖼️ 图片上传OCR支持 (v3.2.7 新增)
- **智能OCR引擎**: macOS原生OCR优先，识别速度极快，自动回退pytesseract确保兼容
- **多格式支持**: 支持JPG, JPEG, PNG, BMP, TIFF, GIF等主流图片格式
- **中英文识别**: 智能文字提取，支持中英文混合内容识别
- **无缝集成**: 完整集成到现有文档处理流程，零配置即用

### 🔍 联网搜索与质量评估 (v3.2.6 增强)
- **结果持久化**: 联网搜索结果现在会持久显示，不会在回答完成后消失
- **质量评分系统**: 优化了搜索结果的权威性与完整性评分算法
- **专业查询**: 增强了关键词提取能力，支持更精准的专业领域查询
- **信息展示**: 改进了来源信息和关键词的展示界面

### 🎨 用户体验优化 (v3.2.6 新增)
- **友好错误处理**: 提供具体的错误解决建议和用户引导，覆盖知识库加载、上传等关键场景
- **操作成功反馈**: 在文件上传、查询完成等操作后显示清晰的成功提示与统计信息
- **智能操作引导**: 在关键位置提供上下文相关的操作帮助

### 🔬 智能研究与深度分析 (v3.2.2 增强)
- **Deep Research 模式**: 模拟专家级多步分析、事实核查与跨领域知识整合，提供更具深度的严谨回答
- **研究指令注入**: 自动对复杂问题进行多维拆解、证据交叉比对和结论总结
- **状态指示横条**: 实时展示“思考、联网、搜索、研究”四大核心能力的状态

### 🔄 持续优化系统 (v3.2.2 新增)
- **良性循环机制**: 巡查 → 分析 → 计划 → 实施 → 验证的自动化优化流程
- **智能监控**: 自动监控代码质量、性能指标、测试覆盖率、文档完整性
- **自动优化**: 执行清理、重构、性能调优等自动化改进任务
- **可视化仪表板**: 实时展示优化效果和系统健康状态

### 💬 智能对话与推荐 (v3.2.2 升级)
- **极速追问推荐**: 重构推荐引擎面板，支持“换一批”即时刷新，提升连续追问体验
- **多轮对话**: 保持上下文的连续对话，支持流式输出与中断控制
- **追问卡片化**: 采用更醒目的视觉引导，提升用户交互意愿
- **操作成功反馈**: 在文件上传、查询完成等关键操作后显示成功提示，提升用户体验 (v3.2.6 新增)
- **友好错误处理**: 改进错误提示信息，提供具体的解决建议和用户引导 (v3.2.6 新增)

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
- **apppro.py** - 主应用入口 (~5,700 行)
- **services/** - 文件服务、知识库服务、配置服务
- **processors/** - 文档处理器、网页爬虫 (15个模块)
- **ui/** - 用户界面组件 (30个模块)
- **utils/** - 工具函数库 (48个模块)
- **总计**: 180个Python文件，51个测试文件

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

# 测试覆盖: 88/97 通过 (92.8%)
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

### 1. 创建与启动
1. **新建知识库**：在顶部导航栏选择 **"➕ 新建知识库..."**。
2. **选择模式**：支持文件上传、粘贴文本、网址抓取或智能搜索。
3. **即选即用**：选择现有知识库后，系统会**自动静默初始化**底层引擎，无需手动点击启动按钮。

### 2. 上传文档
- **单文件/文件夹**: 在管理面板点击 "📤 添加文档"，支持批量拖拽。
- **高级选项**: 上传时可开启 OCR、元数据提取和自动摘要生成。
- **网页抓取**: 输入URL进行深度内容抓取与清洗。

### 3. 开始对话
1. 确认顶部导航栏已选中目标知识库。
2. 在下方输入框提问。
3. 系统将自动检索并生成回答，支持流式输出与源文档溯源。

---

## 🛠️ 开发指南

### 项目结构
```
src/
├── apppro.py           # 主应用 (3,715 行)
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
from rag_pro_max.processors import register_processor
register_processor('.custom', CustomProcessor)
```

---

## 📚 文档资源

- [📋 部署指南](DEPLOYMENT.md)
- [🧪 测试说明](TESTING.md) 
- [❓ 常见问题](FAQ.md)
- [🤝 贡献指南](CONTRIBUTING.md)
- [📝 更新日志](CHANGELOG.md)
- [🔧 文档维护标准](DOCUMENTATION_MAINTENANCE_STANDARD.md)
- [🔒 推送规范](NON_ESSENTIAL_PUSH_STANDARD.md)
- [🧹 开发清理标准](DEVELOPMENT_CLEANUP_STANDARD.md)
- [⚡ 开发规范标准](DEVELOPMENT_STANDARD.md)

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
