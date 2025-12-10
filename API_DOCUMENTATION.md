# RAG Pro Max API 文档 v2.0

## 🚀 快速开始

### 启动API服务器
```bash
# v2.0完整服务
./start_v2.sh

# 或单独启动API
python3 src/api/fastapi_server.py
```

### 访问地址
- **API服务**: http://localhost:8000
- **交互式文档**: http://localhost:8000/docs
- **OpenAPI规范**: http://localhost:8000/openapi.json

## 📋 v2.0 新增接口

### 增量更新
```http
POST /incremental-update
Content-Type: application/json

{
  "kb_name": "my_knowledge_base",
  "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.docx"],
  "force_update": false
}
```

### 多模态文件上传
```http
POST /upload-multimodal
Content-Type: multipart/form-data

kb_name: my_knowledge_base
file: [binary file data]
```

### 多模态查询
```http
POST /query-multimodal
Content-Type: application/json

{
  "query": "图片中显示了什么？",
  "kb_name": "my_knowledge_base", 
  "include_images": true,
  "include_tables": true,
  "top_k": 5
}
```

### 增量统计
```http
GET /kb/{kb_name}/incremental-stats
```

### 支持格式查询
```http
GET /multimodal/formats
```

## 📋 v1.8 基础接口

### 智能问答
```http
POST /query
Content-Type: application/json

{
  "query": "你的问题",
  "kb_name": "knowledge_base_name",
  "top_k": 5,
  "use_cache": true
}
```

### 知识库列表
```http
GET /knowledge-bases
```

### 缓存管理
```http
GET /cache/stats
DELETE /cache
```

## 🔧 错误处理

所有接口返回标准HTTP状态码：
- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

## 📚 完整文档

访问 http://localhost:8000/docs 查看完整的交互式API文档。
- **API服务**: http://localhost:8000
- **交互式文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc

## 📡 API端点

### 1. 根路径
```
GET /
```
返回API基本信息和可用端点列表。

### 2. 健康检查
```
GET /api/health
```
检查API服务状态。

### 3. 上传文档
```
POST /api/upload
```

**参数**:
- `files`: 文件列表 (multipart/form-data)
- `kb_name`: 知识库名称 (form field)

**示例**:
```python
import requests

with open("document.pdf", "rb") as f:
    files = {"files": ("document.pdf", f)}
    data = {"kb_name": "my_knowledge_base"}
    
    response = requests.post(
        "http://localhost:8000/api/upload",
        files=files,
        data=data
    )
```

### 4. 查询知识库
```
POST /api/query
```

**请求体**:
```json
{
    "question": "你的问题",
    "kb_name": "知识库名称",
    "top_k": 5
}
```

**响应**:
```json
{
    "answer": "AI生成的答案",
    "sources": [
        {
            "text": "相关文档片段",
            "score": 0.85,
            "metadata": {"file_name": "document.pdf"}
        }
    ],
    "kb_name": "知识库名称",
    "processing_time": 1.23
}
```

### 5. 知识库管理
```
GET /api/kb          # 获取知识库列表
DELETE /api/kb/{name} # 删除知识库
```

## 🐍 Python客户端示例

```python
import requests

class RAGProMaxAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def query(self, question, kb_name, top_k=5):
        response = requests.post(
            f"{self.base_url}/api/query",
            json={
                "question": question,
                "kb_name": kb_name,
                "top_k": top_k
            }
        )
        return response.json()
    
    def upload(self, file_path, kb_name):
        with open(file_path, "rb") as f:
            files = {"files": (file_path, f)}
            data = {"kb_name": kb_name}
            
            response = requests.post(
                f"{self.base_url}/api/upload",
                files=files,
                data=data
            )
        return response.json()

# 使用示例
api = RAGProMaxAPI()

# 上传文档
result = api.upload("document.pdf", "my_kb")
print(result)

# 查询
answer = api.query("什么是人工智能？", "my_kb")
print(answer["answer"])
```

## 🌐 JavaScript/Node.js 示例

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_BASE = 'http://localhost:8000';

// 查询
async function query(question, kbName) {
    const response = await axios.post(`${API_BASE}/api/query`, {
        question: question,
        kb_name: kbName,
        top_k: 5
    });
    return response.data;
}

// 上传文档
async function upload(filePath, kbName) {
    const form = new FormData();
    form.append('files', fs.createReadStream(filePath));
    form.append('kb_name', kbName);
    
    const response = await axios.post(`${API_BASE}/api/upload`, form, {
        headers: form.getHeaders()
    });
    return response.data;
}

// 使用示例
(async () => {
    try {
        // 上传
        const uploadResult = await upload('document.pdf', 'my_kb');
        console.log('上传结果:', uploadResult);
        
        // 查询
        const queryResult = await query('什么是机器学习？', 'my_kb');
        console.log('答案:', queryResult.answer);
    } catch (error) {
        console.error('错误:', error.response?.data || error.message);
    }
})();
```

## 🔧 错误处理

API使用标准HTTP状态码：

- `200`: 成功
- `400`: 请求错误 (文件过大、参数错误等)
- `404`: 资源不存在 (知识库不存在)
- `500`: 服务器内部错误

错误响应格式：
```json
{
    "detail": "错误描述"
}
```

## 📊 性能建议

1. **批量上传**: 一次上传多个文件比单个文件效率更高
2. **合理的top_k**: 建议设置为3-10，过大会影响性能
3. **文件大小**: 单个文件建议不超过50MB
4. **并发查询**: API支持并发查询，但建议控制在10个以内

## 🧪 测试

```bash
# 运行API测试
python test_api.py

# 运行使用示例
python api_examples.py
```
