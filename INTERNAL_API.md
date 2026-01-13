# RAG Pro Max v5.5.8 内部开发 SDK 文档
**版本**: v5.5.8
  
**架构**: 四层统一架构  
**模块数**: 189个  
**测试覆盖率**: 93%

## 🚀 核心服务接口

### 1. 界面重构服务 (UIRefactorService) - v2.6.1 新增

**位置**: `src/services/ui_refactor_service.py`

#### 生成推荐问题
```python
from rag_pro_max.services.recommendation_service import RecommendationService

rec_service = RecommendationService()
recommendations = rec_service.generate_recommendations(
    query="用户问题",
    context="对话上下文",
    kb_name="知识库名称",
    history=["历史问题1", "历史问题2"],
    count=3
)

# 返回格式
{
    "recommendations": [
        {
            "question": str,
            "confidence": float,
            "source": str
        }
    ],
    "deduplication_info": {
        "filtered_count": int,
        "unique_count": int
    }
}
```

### 2. 文件服务 (FileService)

**位置**: `src/services/file_service.py`

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

### 2. 知识库服务 (KnowledgeBaseService)

**位置**: `src/services/knowledge_base_service.py`

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

**位置**: `src/services/config_service.py`

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

---

## 🔧 工具层高级接口

### 原生文件预览 (AppUtils)
```python
from src.utils.app_utils import open_file_native

# 使用系统默认程序或 Quick Look (macOS) 打开预览
# 非阻塞调用
success = open_file_native("/path/to/your/document.pdf")
```

### 网页抓取 (WebCrawler)
```python
from src.processors.web_crawler import WebCrawler

crawler = WebCrawler()
result = crawler.crawl_url(
    url="https://example.com",
    max_pages=10,
    max_depth=2
)
```

### 智能名称生成 (KBUtils)
```python
from src.utils.kb_utils import generate_smart_kb_name

name = generate_smart_kb_name(
    target_path="/tmp/uploads", 
    cnt=5, 
    file_types={'pdf': 5}, 
    folder_name="batch_upload"
)
```

---

## 📚 开发示例

### 完整流程示例
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
    # 处理文件 (需结合 Processor 层)
    pass
else:
    print(f"文件验证失败: {validation['error']}")
```