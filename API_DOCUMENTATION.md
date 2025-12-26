# RAG Pro Max v2.6.1 API 文档

## 概述

RAG Pro Max v2.6.1 提供了一套完整的 RESTful API 接口，支持知识库查询、管理、界面重构及多模态数据处理。

**服务器信息：**
- **默认端口**: 8502 (由 `start_v2.sh` 启动)
- **OpenAPI 文档**: `http://localhost:8502/docs`
- **版本**: v2.6.1 界面重构版
- **测试覆盖率**: 93%

---

## 核心功能接口

### 1. 界面重构接口 (v2.6.1 新增)

#### 获取数据源布局
`GET /ui/datasource-layout`

获取4x1扁平布局配置信息。

**请求体 (JSON):**
```json
{
  "query": "当前问题",
  "kb_name": "知识库名称",
  "context": "对话上下文",
  "history": ["历史问题1", "历史问题2"],
  "count": 3
}
```

### 2. 问答查询

#### 普通查询
`POST /query`

提交问题并获取基于知识库的回答。

**请求体 (JSON):**
```json
{
  "query": "你的问题",
  "kb_name": "知识库名称",
  "top_k": 5,
  "use_cache": true
}
```

**响应:**
```json
{
  "answer": "AI生成的回答...",
  "sources": [
    {
      "file_name": "source.pdf",
      "score": 0.85,
      "text": "原文片段..."
    }
  ],
  "metadata": { ... }
}
```

#### 多模态查询
`POST /query-multimodal`

支持包含图像或表格分析的复杂查询。

**请求体 (JSON):**
```json
{
  "query": "分析图表中的数据",
  "kb_name": "知识库名称",
  "include_images": true,
  "include_tables": true
}
```

---

### 2. 知识库管理

#### 获取知识库列表
`GET /knowledge-bases`

返回所有可用知识库及其元数据。

#### 获取增量更新统计
`GET /kb/{kb_name}/incremental-stats`

查看指定知识库的文件变更和处理统计。

#### 增量更新
`POST /incremental-update`

触发知识库的增量更新流程。

**请求体 (JSON):**
```json
{
  "kb_name": "知识库名称",
  "file_paths": ["/path/to/new/file.pdf"],
  "force_update": false
}
```

#### 上传多模态文件
`POST /upload-multimodal`

上传并处理图片或复杂文档。

---

### 3. 系统维护

#### 健康检查
`GET /health`

检查 API 服务运行状态。

#### 缓存统计
`GET /cache/stats`

查看当前缓存命中率和占用情况。

#### 清空缓存
`DELETE /cache`

强制清空系统缓存。

---

### 4. 辅助接口

#### 获取支持格式
`GET /multimodal/formats`

返回系统支持的所有文件类型列表。