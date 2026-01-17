# RAG Pro Max v6.7.0 企业级API文档

**版本**: v6.7.0  
**更新日期**: 2026-01-17  
**适用范围**: 企业级API集成  

---

## 🏢 企业级API概述

RAG Pro Max v6.7.0 提供完整的RESTful API接口，支持企业级集成和自动化部署。

### 💎 v6.7.0 新型特性支持
- **归一化附件解析**: 新增 `/parse_attachment` 接口，支持图片 OCR、PDF、CSV 等 20+ 格式的统一解析流。
- **高维资产透视**: `/kb/list` 接口现在返回 `created_at` 与 `last_modified` 元数据，支持按类型过滤。
- **自愈式 SQL 建模**: 建模 API 现在集成表名自愈逻辑，自动修复生成 SQL 中的命名偏差。

### 🔒 企业安全特性
- **本地部署**: 所有API在企业内网运行
- **零数据上传**: API调用不向外部发送数据
- **访问控制**: 支持IP白名单和API密钥认证
- **审计日志**: 完整的API调用记录

### 🌍 多语言支持
- **请求语言**: 支持中英文混合查询
- **响应格式**: 统一JSON格式，支持国际化
- **错误信息**: 中英文双语错误提示
- **文档语言**: 中英文API文档

---

## 🚀 快速开始

### 启动API服务
```bash
# 启动主应用
streamlit run src/apppro.py

# 启动API服务
python src/api/fastapi_server.py
```

### 基础认证
```bash
# 健康检查
curl http://localhost:8000/health

# 带认证的请求 (如果配置了API密钥)
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/query
```

---

## 📋 核心API端点

### 1. 健康检查
```http
GET /health
```

**描述**: 检查API服务状态

**响应示例**:
```json
{
  "status": "healthy",
  "version": "3.2.2",
  "timestamp": "2026-01-03T15:12:00Z",
  "features": {
    "offline_mode": true,
    "multilingual": true,
    "enterprise_ready": true
  }
}
```

### 2. 智能查询
```http
POST /query
```

**描述**: 执行智能文档查询

**请求参数**:
```json
{
  "query": "企业部署要求是什么？",
  "kb_name": "企业文档",
  "options": {
    "enable_web_search": false,
    "enable_deep_think": true,
    "enable_research": true,
    "language": "zh-CN"
  }
}
```

**响应示例**:
```json
{
  "answer": "企业部署要求包括...",
  "sources": [
    {
      "document": "企业部署指南.pdf",
      "page": 1,
      "confidence": 0.95
    }
  ],
  "metadata": {
    "response_time": 2.3,
    "tokens_used": 150,
    "search_enabled": false,
    "research_enabled": true
  }
}
```

### 3. 知识库管理
```http
GET /knowledge-bases
```

**描述**: 获取所有知识库列表

**响应示例**:
```json
{
  "knowledge_bases": [
    {
      "name": "企业文档",
      "description": "企业内部文档库",
      "document_count": 156,
      "created_at": "2026-01-01T00:00:00Z",
      "size_mb": 245.6
    }
  ],
  "total_count": 1
}
```

### 4. 文档上传
```http
POST /upload
```

**描述**: 上传文档到指定知识库

**请求参数** (multipart/form-data):
- `file`: 文档文件
- `kb_name`: 知识库名称
- `options`: 处理选项 (JSON字符串)

**响应示例**:
```json
{
  "success": true,
  "file_id": "doc_123456",
  "message": "文档上传成功",
  "processing_status": "completed",
  "metadata": {
    "filename": "企业手册.pdf",
    "size_mb": 5.2,
    "pages": 45,
    "processing_time": 23.5
  }
}
```

### 5. 文档管理
```http
GET /documents/{kb_name}
DELETE /documents/{kb_name}/{doc_id}
```

**描述**: 管理知识库中的文档

---

## 🔧 高级API功能

### 批量查询
```http
POST /batch-query
```

**请求参数**:
```json
{
  "queries": [
    {
      "id": "q1",
      "query": "企业安全要求",
      "kb_name": "企业文档"
    },
    {
      "id": "q2", 
      "query": "部署架构说明",
      "kb_name": "技术文档"
    }
  ],
  "options": {
    "parallel": true,
    "timeout": 30
  }
}
```

### 文档分析
```http
POST /analyze-document
```

**描述**: 分析单个文档的内容结构

**请求参数**:
```json
{
  "document_id": "doc_123456",
  "analysis_type": ["summary", "keywords", "structure"],
  "language": "zh-CN"
}
```

### 知识库统计
```http
GET /statistics/{kb_name}
```

**描述**: 获取知识库详细统计信息

**响应示例**:
```json
{
  "kb_name": "企业文档",
  "statistics": {
    "total_documents": 156,
    "total_size_mb": 245.6,
    "document_types": {
      "pdf": 89,
      "docx": 45,
      "txt": 22
    },
    "query_statistics": {
      "total_queries": 1250,
      "avg_response_time": 2.1,
      "success_rate": 0.98
    }
  }
}
```

---

## 🛡️ 企业安全配置

### API密钥认证
```bash
# 配置API密钥
export RAG_API_KEY="your-secure-api-key"

# 使用API密钥
curl -H "Authorization: Bearer your-secure-api-key" \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}' \
     http://localhost:8000/query
```

### IP白名单
```json
{
  "security": {
    "ip_whitelist": [
      "192.168.1.0/24",
      "10.0.0.0/8"
    ],
    "rate_limiting": {
      "requests_per_minute": 100,
      "burst_size": 20
    }
  }
}
```

### HTTPS配置
```bash
# 使用SSL证书启动
python src/api/fastapi_server.py \
  --ssl-keyfile /path/to/key.pem \
  --ssl-certfile /path/to/cert.pem \
  --port 8443
```

---

## 📊 监控与日志

### API监控端点
```http
GET /metrics
```

**响应示例**:
```json
{
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "disk_usage": 23.1
  },
  "api": {
    "total_requests": 5420,
    "avg_response_time": 2.1,
    "error_rate": 0.02,
    "active_connections": 12
  }
}
```

### 日志配置
```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "/var/log/rag-pro-max/api.log",
    "rotation": "daily",
    "retention": "30d"
  }
}
```

---

## 🔌 SDK与集成

### Python SDK
```python
from rag_pro_max import RAGClient

# 初始化客户端
client = RAGClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 执行查询
result = client.query(
    query="企业部署要求",
    kb_name="企业文档",
    enable_research=True
)

print(result.answer)
```

### JavaScript SDK
```javascript
import { RAGClient } from 'rag-pro-max-js';

const client = new RAGClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

const result = await client.query({
  query: '企业部署要求',
  kbName: '企业文档',
  options: { enableResearch: true }
});

console.log(result.answer);
```

---

## ❌ 错误处理

### 错误响应格式
```json
{
  "error": {
    "code": "INVALID_KB_NAME",
    "message": "指定的知识库不存在",
    "message_en": "Specified knowledge base does not exist",
    "details": {
      "kb_name": "不存在的知识库",
      "available_kbs": ["企业文档", "技术文档"]
    },
    "timestamp": "2026-01-03T15:12:00Z"
  }
}
```

### 常见错误码
| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| `INVALID_KB_NAME` | 404 | 知识库不存在 |
| `INVALID_QUERY` | 400 | 查询参数无效 |
| `RATE_LIMITED` | 429 | 请求频率超限 |
| `UNAUTHORIZED` | 401 | 认证失败 |
| `INTERNAL_ERROR` | 500 | 内部服务错误 |

---

## 📋 企业部署检查清单

### API部署前检查
- [ ] 确认Python 3.8+环境
- [ ] 安装所有依赖包
- [ ] 配置API密钥和安全设置
- [ ] 测试健康检查端点

### 安全配置检查
- [ ] 配置IP白名单
- [ ] 启用HTTPS (生产环境)
- [ ] 设置请求频率限制
- [ ] 配置审计日志

### 性能优化检查
- [ ] 配置适当的并发数
- [ ] 启用响应缓存
- [ ] 监控资源使用情况
- [ ] 设置超时参数

---

## 📞 企业支持

### 技术支持
- **API集成支持**: api-support@rag-pro-max.com
- **企业定制**: enterprise@rag-pro-max.com
- **技术文档**: https://docs.rag-pro-max.com/api

### 社区资源
- **GitHub**: https://github.com/zhaosj0315/rag-pro-max
- **Issues**: 技术问题和Bug报告
- **Discussions**: API使用讨论

---

**🎯 目标**: 为企业提供安全、高效、易集成的API服务

---

*本文档遵循企业文档管理标准，确保API接口的专业性和可靠性*
