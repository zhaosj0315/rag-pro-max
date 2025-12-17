# RAG Pro Max API 文档

## 概述

RAG Pro Max 提供完整的 RESTful API 和 Python SDK，支持文档处理、知识库管理、智能问答等核心功能。

## 🚀 快速开始

### 启动API服务
```bash
python src/api/fastapi_server.py
```

默认地址: `http://localhost:8000`

## 📋 核心服务接口

### 1. 文件服务 (FileService)

#### 文件验证
```python
from src.services.file_service import FileService

file_service = FileService()
result = file_service.validate_file(file_path)

# 返回格式
{
    "valid": bool,
    "file_size": int,
    "file_type": str,
    "error": str | None
}
```

#### 支持的文件类型
- **文档**: `.txt`, `.md`, `.pdf`, `.docx`, `.doc`
- **表格**: `.xlsx`, `.xls`, `.csv`
- **演示**: `.pptx`, `.ppt`
- **网页**: `.html`, `.htm`
- **数据**: `.json`
- **压缩**: `.zip`

#### 文件大小限制
- 最大文件大小: **100MB**

### 2. 知识库服务 (KnowledgeBaseService)

#### 初始化服务
```python
from src.services.knowledge_base_service import KnowledgeBaseService

kb_service = KnowledgeBaseService(storage_dir="vector_db_storage")
```

#### 列出知识库
```python
kb_list = kb_service.list_knowledge_bases()

# 返回格式
[
    {
        "name": str,
        "path": str,
        "created_time": str,
        "file_count": int,
        "size": str
    }
]
```

#### 知识库操作
```python
# 创建知识库
kb_service.create_knowledge_base(name)

# 删除知识库
kb_service.delete_knowledge_base(name)

# 获取知识库信息
info = kb_service.get_kb_info(name)
```

### 3. 配置服务 (ConfigService)

#### 获取配置服务
```python
from src.services.config_service import get_config_service

config = get_config_service()
```

#### 模型配置
```python
# 获取默认模型
model = config.get_default_model()

# 更新模型配置
success = config.update_model_config(new_model)

# 获取配置值
value = config.get_config_value(key, default_value)
```

## 🌐 RESTful API 端点

### 健康检查
```http
GET /health
```

**响应**:
```json
{
    "status": "healthy",
    "version": "2.4.4",
    "timestamp": "2025-12-17T21:58:12Z"
}
```

### 查询接口
```http
POST /query
Content-Type: application/json

{
    "question": "你的问题",
    "kb_name": "知识库名称",
    "stream": false
}
```

**响应**:
```json
{
    "answer": "回答内容",
    "sources": [
        {
            "file": "文件名",
            "page": 1,
            "content": "相关内容"
        }
    ],
    "suggestions": ["追问1", "追问2", "追问3"]
}
```

### 知识库列表
```http
GET /knowledge-bases
```

**响应**:
```json
{
    "knowledge_bases": [
        {
            "name": "知识库名称",
            "file_count": 10,
            "created_time": "2025-12-17",
            "size": "50MB"
        }
    ]
}
```

### 文件上传
```http
POST /upload
Content-Type: multipart/form-data

{
    "file": <文件>,
    "kb_name": "知识库名称"
}
```

**响应**:
```json
{
    "success": true,
    "message": "文件上传成功",
    "file_info": {
        "name": "文件名",
        "size": "10MB",
        "type": "pdf"
    }
}
```

## 🔧 高级功能

### 网页抓取
```python
from src.processors.web_crawler import WebCrawler

crawler = WebCrawler()
result = crawler.crawl_url(
    url="https://example.com",
    max_pages=10,
    max_depth=2
)
```

### 批量处理
```python
from src.processors.batch_processor import BatchProcessor

processor = BatchProcessor()
results = processor.process_directory(
    directory_path="/path/to/files",
    kb_name="知识库名称"
)
```

### OCR处理
```python
from src.utils.ocr_optimizer import OCROptimizer

ocr = OCROptimizer()
text = ocr.extract_text_from_pdf(pdf_path)
```

## 📊 性能监控

### 系统监控
```python
from src.utils.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
stats = monitor.get_system_stats()

# 返回格式
{
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "gpu_usage": 23.1,
    "disk_usage": 78.9
}
```

### 资源管理
```python
from src.utils.resource_monitor import ResourceMonitor

resource_monitor = ResourceMonitor()
resource_monitor.start_monitoring()
```

## 🛡️ 错误处理

### 常见错误码
- `400`: 请求参数错误
- `404`: 知识库不存在
- `413`: 文件过大
- `415`: 不支持的文件类型
- `500`: 服务器内部错误

### 错误响应格式
```json
{
    "error": true,
    "code": 400,
    "message": "错误描述",
    "details": "详细信息"
}
```

## 🔐 安全配置

### 环境变量
```bash
# API安全
export API_KEY="your-api-key"
export CORS_ORIGINS="http://localhost:3000"

# 文件安全
export MAX_FILE_SIZE=104857600  # 100MB
export ALLOWED_EXTENSIONS=".pdf,.docx,.txt"
```

### 访问控制
```python
# 在配置文件中设置
{
    "security": {
        "enable_auth": true,
        "api_key_required": true,
        "rate_limit": 100
    }
}
```

## 📚 SDK 示例

### Python SDK 完整示例
```python
from src.services.file_service import FileService
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.config_service import get_config_service

# 初始化服务
file_service = FileService()
kb_service = KnowledgeBaseService()
config_service = get_config_service()

# 创建知识库
kb_name = "我的知识库"
kb_service.create_knowledge_base(kb_name)

# 验证并上传文件
file_path = "/path/to/document.pdf"
validation = file_service.validate_file(file_path)

if validation["valid"]:
    # 处理文件
    result = file_service.process_file(file_path, kb_name)
    print(f"文件处理结果: {result}")
else:
    print(f"文件验证失败: {validation['error']}")

# 查询知识库
kb_list = kb_service.list_knowledge_bases()
print(f"知识库列表: {kb_list}")
```

## 🔄 版本兼容性

- **当前版本**: v2.4.4
- **API版本**: v1
- **最低Python版本**: 3.8+
- **向后兼容**: 支持v2.x所有版本
