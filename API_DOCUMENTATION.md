# RAG Pro Max v8.0.0 企业级API文档

**版本**: v8.0.0 (Flagship Dual-Core Edition)  
**更新日期**: 2026-01-19  
**适用范围**: 企业级API集成  

---

## 🧬 双核联动API概述

RAG Pro Max v8.0.0 标志着 API 从单一的文档检索向 **“语义+逻辑”** 双核驱动的全面跃迁。

### 💎 v8.0.0 Dual-Core API 特性
- **智能数据分析开关**: `/kb/process` 接口新增 `enable_data_analysis` 参数，一键激活 SQL 逻辑增强。
- **混合结果集**: `/query` 接口现在支持返回“数文对照”数据，同时包含 RAG 文本证据与 SQL 计算结果。
- **全合规资产透视**: `/kb/list` 接口增强，实时返回物理索引与影子数据库的健康状态。
- **自愈式 SQL 建模**: 建模 API 集成真数据判定逻辑，自动规避语义型表格的无效建表。

---

## 📋 核心API端点

### 1. 健康检查与双核状态
```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "8.0.0",
  "edition": "Flagship Dual-Core",
  "features": {
    "dual_core_engine": true,
    "sql_assistant": true,
    "gpu_accelerated": true
  }
}
```

### 2. 知识库构建 (双核模式)
```http
POST /kb/process
```

**请求参数**:
```json
{
  "kb_name": "Sales_Report_2025",
  "action_mode": "NEW",
  "options": {
    "use_ocr": true,
    "enable_data_analysis": true,
    "extract_metadata": true,
    "generate_summary": true
  }
}
```

**逻辑说明**:
- 勾选 `enable_data_analysis` 后，系统会在构建向量索引的同时，对 `raw_sources/` 目录下的表格执行物理建表。

### 3. 智能联动查询
```http
POST /query
```

**请求参数**:
```json
{
  "query": "分析去年的销售趋势并给出相关政策说明",
  "kb_name": "Sales_Report_2025",
  "mode": "dual_core"
}
```

**响应示例**:
```json
{
  "answer": "根据数据分析显示，去年销售呈现 15% 的稳步增长。财报第 5 页提到...",
  "data_evidence": {
    "sql": "SELECT SUM(amount) FROM sales...",
    "result_table": [ ... ],
    "chart_type": "line"
  },
  "text_evidence": [
    { "doc": "report.pdf", "text": "销售增长主要由于..." }
  ]
}
```

---

## 🛡️ 企业安全配置

### 权限与配额
- **存储配额**: API 返回包含 `storage_quota_mb` 与 `current_usage` 信息。
- **个体熔断**: 支持通过 API 一键注销特定用户的 JWT 令牌。

---

**🎯 目标**: 为企业提供全能、精准、安全的智能双核API服务
