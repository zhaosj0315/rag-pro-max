# 🔌 API 文档

## 概述

RAG Pro Max v2.3.1 提供完整的 RESTful API 接口，支持程序化调用所有核心功能。

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本: v2.3.1
- **认证方式**: 暂无（本地部署）
- **数据格式**: JSON

## 核心端点

### 1. 知识库管理

#### 创建知识库
```http
POST /api/v1/knowledge-bases
Content-Type: application/json

{
  "name": "my_kb",
  "description": "我的知识库"
}
```

#### 获取知识库列表
```http
GET /api/v1/knowledge-bases
```

#### 删除知识库
```http
DELETE /api/v1/knowledge-bases/{kb_name}
```

### 2. 文档管理

#### 上传文档
```http
POST /api/v1/knowledge-bases/{kb_name}/documents
Content-Type: multipart/form-data

files: [file1.pdf, file2.docx]
```

#### 网页抓取
```http
POST /api/v1/knowledge-bases/{kb_name}/crawl
Content-Type: application/json

{
  "url": "https://python.org",
  "depth": 2,
  "max_pages": 10
}
```

### 3. 问答接口

#### 单次问答
```http
POST /api/v1/knowledge-bases/{kb_name}/query
Content-Type: application/json

{
  "question": "什么是RAG？",
  "top_k": 5,
  "temperature": 0.7
}
```

#### 流式问答
```http
POST /api/v1/knowledge-bases/{kb_name}/stream
Content-Type: application/json

{
  "question": "详细解释RAG的工作原理",
  "stream": true
}
```

### 4. 系统监控

#### 获取系统状态
```http
GET /api/v1/system/status
```

#### 获取性能指标
```http
GET /api/v1/system/metrics
```

## 响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误类型",
  "message": "详细错误信息"
}
```

## 使用示例

### Python 客户端
```python
import requests

# 创建知识库
response = requests.post(
    "http://localhost:8000/api/v1/knowledge-bases",
    json={"name": "test_kb", "description": "测试知识库"}
)

# 问答
response = requests.post(
    "http://localhost:8000/api/v1/knowledge-bases/test_kb/query",
    json={"question": "什么是人工智能？"}
)

print(response.json())
```

### JavaScript 客户端
```javascript
// 问答请求
fetch('http://localhost:8000/api/v1/knowledge-bases/test_kb/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: '什么是机器学习？'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 启动API服务

```bash
# 启动FastAPI服务器
python src/api/fastapi_server.py

# 或使用uvicorn
uvicorn src.api.fastapi_server:app --host 0.0.0.0 --port 8000
```

## 注意事项

1. **本地部署**: API服务仅支持本地访问
2. **并发限制**: 建议同时处理请求数不超过10个
3. **文件大小**: 单个文件最大100MB
4. **超时设置**: 长时间操作建议设置适当超时时间

---

更多详细信息请参考 [完整API文档](./docs/API_REFERENCE.md)
