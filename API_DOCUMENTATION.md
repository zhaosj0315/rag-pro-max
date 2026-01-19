# RAG Pro Max v6.9.0 企业级API文档

**版本**: v6.9.0 (Flagship Governance Edition)  
**更新日期**: 2026-01-19  
**适用范围**: 企业级API集成  

---

## 🏢 企业级API概述

RAG Pro Max v6.9.0 提供完整的RESTful API接口，支持企业级集成和自动化部署。

### 💎 v6.9.0 Flagship Governance API 特性
- **个体安全策略API**: 新增 `/auth/user_settings` 接口，支持为特定用户配置专属 TTL（会话有效期）
- **定点熔断API**: `/auth/revoke_sessions` 支持按用户名即时切断所有活跃通信链路
- **全合规资产透视**: `/kb/list` 接口增强，实时返回损坏状态、容量警报及活跃度元数据
- **精准选表API**: `/analysis/select_tables` 接口，支持基于语义的智能表选择
- **领域感知配置**: `/analysis/domain_config` 接口，支持配置跨境贸易和财税领域的语义规则
- **自愈式 SQL 建模**: 建模 API 现在集成表名自愈逻辑，自动修复生成 SQL 中的命名偏差

### 🔒 企业安全特性
- **本地部署**: 所有API在企业内网运行，物理隔离安全
- **零数据上传**: API调用不向外部发送数据，数据主权完全掌控
- **访问控制**: 支持IP白名单、JWT Token 校验与账户锁定机制
- **审计日志**: 基于 `LogManager` 的高性能异步审计流水记录

---

## 🚀 快速开始

### 启动API服务
```bash
# 启动主应用 (Streamlit 仪表盘)
streamlit run src/apppro.py

# 启动后端API服务
python src/api/fastapi_server.py
```

---

## 📋 核心API端点

### 1. 健康检查与能力宣告
```http
GET /health
```

**描述**: 检查API服务状态及当前启用的旗舰功能

**响应示例**:
```json
{
  "status": "healthy",
  "version": "6.9.0",
  "edition": "Flagship Governance",
  "timestamp": "2026-01-19T12:00:00Z",
  "features": {
    "individual_ttl": true,
    "compliance_scan": true,
    "gpu_accelerated": true
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
  "query": "旗舰版治理中心的新特性有哪些？",
  "kb_name": "系统文档",
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
  "answer": "旗舰版治理中心引入了个体安全调节舱、全合规扫描引擎等核心特性...",
  "sources": [
    {
      "document": "README.md",
      "page": 1,
      "confidence": 0.98
    }
  ],
  "metadata": {
    "response_time": 1.2,
    "tokens_used": 240,
    "search_enabled": false,
    "research_enabled": true
  }
}
```

### 3. 资产清单 (含合规元数据)
```http
GET /knowledge-bases
```

**描述**: 获取所有知识库及其治理状态

**响应示例**:
```json
{
  "knowledge_bases": [
    {
      "name": "Finance_2025",
      "owner": "admin",
      "compliance_status": "✅ 合规",
      "last_active": "2026-01-19",
      "size_mb": 42.5
    },
    {
      "name": "Temp_Dump",
      "owner": "guest",
      "compliance_status": "⚠️ 容量预警",
      "last_active": "2025-12-01",
      "size_mb": 650.2
    }
  ],
  "total_count": 2
}
```

### 4. 文档上传与解析
```http
POST /upload
```

**描述**: 上传文档并自动触发旗舰级解析流

---

## 🛡️ 企业安全配置

### API密钥认证
```bash
export RAG_API_KEY="your-secure-api-key"
```

### IP白名单
```json
{
  "security": {
    "ip_whitelist": ["192.168.1.0/24"]
  }
}
```

---

## 📊 监控与指标

### 治理指标端点
```http
GET /metrics/governance
```

**响应示例**:
```json
{
  "total_assets": 15,
  "compliance_rate": "93.3%",
  "zombie_assets": 1,
  "large_assets": 2,
  "total_physical_load": "1.2 GB"
}
```

---

## 📞 企业支持

- **API集成支持**: api-support@rag-pro-max.com
- **GitHub**: https://github.com/zhaosj0315/rag-pro-max

---

**🎯 目标**: 为企业提供安全、极简、旗舰级的API服务