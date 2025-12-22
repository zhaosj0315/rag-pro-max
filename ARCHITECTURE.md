# RAG Pro Max 系统架构文档

## 🏗️ 总体架构

RAG Pro Max 采用四层架构设计，确保代码的可维护性、可扩展性和高性能。

```
┌─────────────────────────────────────────┐
│           表现层 (UI Layer)              │
│    Streamlit界面 + Web组件              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          服务层 (Service Layer)          │
│   文件服务 + 知识库服务 + 配置服务        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          公共层 (Common Layer)           │
│     业务逻辑 + 通用工具 + 配置管理        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          工具层 (Utils Layer)            │
│   文档处理 + OCR + 向量化 + 监控         │
└─────────────────────────────────────────┘
```

## 📁 目录结构详解

### 核心应用层
```
src/
├── apppro.py                    # 🚀 主应用入口 (3,715 行)
│   ├── Streamlit配置
│   ├── 页面路由
│   ├── 会话管理
│   └── 全局状态
```

### 服务层 (Service Layer)
```
src/services/
├── file_service.py              # 文件处理服务
│   ├── validate_file()          # 文件验证
│   ├── process_file()           # 文件处理
│   └── SUPPORTED_EXTENSIONS     # 支持格式
├── knowledge_base_service.py    # 知识库管理服务
│   ├── list_knowledge_bases()   # 列出知识库
│   ├── create_knowledge_base()  # 创建知识库
│   └── delete_knowledge_base()  # 删除知识库
└── config_service.py            # 配置管理服务
    ├── get_default_model()      # 获取默认模型
    ├── update_model_config()    # 更新模型配置
    └── get_config_value()       # 获取配置值
```

### 公共层 (Common Layer)
```
src/common/
├── business.py                  # 业务逻辑
├── config.py                    # 配置管理
└── utils.py                     # 通用工具函数
```

### 用户界面层 (UI Layer)
```
src/ui/                          # 39个界面组件
├── config_forms.py              # 配置表单
├── sidebar_config.py            # 侧边栏配置
├── page_style.py                # 页面样式
├── kb_management_ui.py          # 知识库管理界面
├── web_to_kb_interface.py       # 网页抓取界面
├── search_ui.py                 # 搜索界面
├── chat_interface.py            # 聊天界面
├── progress_monitor.py          # 进度监控
├── monitoring_dashboard.py      # 监控面板
└── ...                          # 其他UI组件
```

### 文档处理层 (Processors)
```
src/processors/                  # 23个处理器
├── web_crawler.py               # 网页爬虫
├── async_web_crawler.py         # 异步爬虫
├── concurrent_crawler.py        # 并发爬虫
├── content_analyzer.py          # 内容分析
├── crawl_stats_manager.py       # 爬虫统计
├── index_builder.py             # 索引构建
├── multimodal_processor.py      # 多模态处理
├── upload_handler.py            # 上传处理
└── ...                          # 其他处理器
```

### 工具层 (Utils Layer)
```
src/utils/                       # 60个工具模块
├── model_manager.py             # 模型管理
├── ocr_optimizer.py             # OCR优化
├── gpu_ocr_accelerator.py       # GPU加速OCR
├── performance_monitor.py       # 性能监控
├── memory_optimizer.py          # 内存优化
├── batch_operations.py          # 批量操作
├── search_engine.py             # 搜索引擎
├── export_manager.py            # 导出管理
├── alert_system.py              # 告警系统
└── ...                          # 其他工具
```

### 核心控制层 (Core)
```
src/core/                        # 15个核心模块
├── version.py                   # 版本管理
├── app_config.py                # 应用配置
├── environment.py               # 环境初始化
├── state_manager.py             # 状态管理
├── main_controller.py           # 主控制器
├── optimization_manager.py      # 优化管理
└── ...                          # 其他核心模块
```

## 🔄 数据流架构

### 文档处理流程
```
用户上传文件
    ↓
FileService.validate_file()      # 文件验证
    ↓
文档处理器选择                    # 根据文件类型
    ↓
OCR/文本提取                     # GPU加速处理
    ↓
文本分块                         # 智能分块
    ↓
向量化                          # 嵌入模型
    ↓
存储到ChromaDB                   # 向量数据库
    ↓
更新知识库索引                   # 索引更新
```

### 查询处理流程
```
用户输入问题
    ↓
问题预处理                       # 清理和标准化
    ↓
向量检索                        # 语义相似度
    ↓
BM25检索                        # 关键词匹配
    ↓
混合重排序                      # Cross-Encoder
    ↓
上下文构建                      # 检索增强
    ↓
LLM生成回答                     # 大语言模型
    ↓
后处理和格式化                  # 结果优化
    ↓
返回给用户                      # 流式输出
```

### 网页抓取流程
```
用户输入URL
    ↓
URL验证和修复                   # 智能URL处理
    ↓
网站类型分析                    # AI内容分析
    ↓
参数推荐                       # 最佳抓取参数
    ↓
并发抓取                       # 异步多线程
    ↓
内容质量筛选                   # 智能过滤
    ↓
去重处理                       # 内容去重
    ↓
转换为知识库                   # 自动入库
```

## 🧩 核心组件详解

### 1. 配置管理系统
```python
# 配置服务架构
ConfigService
├── app_config.json              # 应用配置
├── rag_config.json              # RAG参数
├── scheduler_config.json        # 调度配置
└── 环境变量管理                 # 动态配置
```

### 2. 知识库管理系统
```python
# 知识库架构
KnowledgeBase
├── 向量存储 (ChromaDB)
├── 文档存储 (docstore.json)
├── 索引存储 (index_store.json)
├── 元数据管理 (manifest.json)
└── 知识库信息 (.kb_info.json)
```

### 3. 文档处理系统
```python
# 处理器架构
DocumentProcessor
├── PDF处理器 (PyMuPDF + OCR)
├── Word处理器 (python-docx)
├── Excel处理器 (openpyxl)
├── PowerPoint处理器 (python-pptx)
├── 网页处理器 (BeautifulSoup)
└── 通用文本处理器
```

### 4. 向量检索系统
```python
# 检索架构
RetrievalSystem
├── 语义检索 (sentence-transformers)
├── 关键词检索 (BM25)
├── 混合检索 (Hybrid)
├── 重排序 (Cross-Encoder)
└── 结果融合 (RRF)
```

## 🔧 技术栈详解

### 前端技术栈
- **Streamlit** ≥1.28.0 - Web应用框架 (v2.4.8 统一推荐系统))
- **HTML/CSS/JavaScript** - 自定义组件
- **Plotly** - 数据可视化
- **Streamlit-Aggrid** - 表格组件

### 后端技术栈
- **FastAPI** - API服务框架
- **LlamaIndex** ≥0.9.0 - RAG框架
- **ChromaDB** ≥0.4.0 - 向量数据库
- **SQLite** - 元数据存储

### AI/ML技术栈
- **sentence-transformers** ≥2.2.0 - 嵌入模型
- **transformers** ≥4.30.0 - Transformer模型
- **torch** ≥2.0.0 - 深度学习框架
- **ollama** ≥0.1.0 - 本地LLM服务

### 文档处理技术栈
- **PyMuPDF** - PDF处理
- **python-docx** - Word文档
- **openpyxl** - Excel处理
- **python-pptx** - PowerPoint处理
- **paddleocr** - OCR识别
- **BeautifulSoup4** - HTML解析

## 📊 性能优化架构

### 1. 内存管理
```python
# 内存优化策略
MemoryOptimizer
├── 动态批处理大小
├── GPU内存监控
├── 垃圾回收优化
├── 缓存管理
└── 内存泄漏检测
```

### 2. 并发处理
```python
# 并发架构
ConcurrencyManager
├── 异步文档处理
├── 多线程OCR
├── 并发网页抓取
├── 队列管理
└── 资源池管理
```

### 3. 缓存系统
```python
# 缓存架构
CacheSystem
├── 查询结果缓存
├── 向量缓存
├── 模型缓存
├── 文件缓存
└── 会话缓存
```

## 🛡️ 安全架构

### 1. 文件安全
- 文件类型验证
- 文件大小限制 (100MB)
- 恶意文件检测
- 沙箱处理

### 2. 数据安全
- 本地数据存储
- 加密传输
- 访问控制
- 审计日志

### 3. 系统安全
- 资源限制
- 错误处理
- 异常监控
- 自动恢复

## 🔄 扩展性设计

### 1. 插件架构
```python
# 插件系统
PluginSystem
├── 文档处理器插件
├── 检索器插件
├── LLM适配器插件
├── UI组件插件
└── 监控插件
```

### 2. 微服务架构
```python
# 服务拆分
Microservices
├── 文档处理服务
├── 向量检索服务
├── 问答生成服务
├── 配置管理服务
└── 监控服务
```

### 3. 水平扩展
- 分布式向量数据库
- 负载均衡
- 服务发现
- 容器化部署

## 📈 监控和运维

### 1. 系统监控
- CPU/GPU/内存使用率
- 磁盘I/O监控
- 网络流量监控
- 进程监控

### 2. 应用监控
- 请求响应时间
- 错误率统计
- 用户行为分析
- 性能瓶颈识别

### 3. 日志系统
- 结构化日志
- 日志聚合
- 实时告警
- 日志分析

## 🚀 未来架构演进

### 1. 云原生架构
- Kubernetes部署
- 服务网格
- 自动扩缩容
- 多云支持

### 2. AI增强架构
- 自适应参数调优
- 智能资源调度
- 自动故障恢复
- 预测性维护

### 3. 边缘计算架构
- 边缘节点部署
- 本地推理优化
- 离线模式支持
- 数据同步机制
