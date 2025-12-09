# 使用指南

## 基本流程

### 1. 创建知识库
- 在侧边栏输入知识库名称
- 点击"创建新知识库"
- 知识库创建后自动选中

### 2. 上传文档

**单文件上传：**
- 点击"上传文档"
- 选择支持的文件格式
- 等待处理完成

**批量上传：**
- 点击"批量上传文件夹"
- 选择包含文档的文件夹
- 系统自动处理所有支持的文件

**支持的格式：**
- PDF (.pdf)
- Word (.docx)
- 文本 (.txt)
- Markdown (.md)
- Excel (.xlsx)

### 3. 开始对话
- 选择已创建的知识库
- 在输入框输入问题
- 查看答案和引用来源

## 配置参数

### RAG 检索参数 (`config/rag_config.json`)

```json
{
  "chunk_size": 500,
  "chunk_overlap": 50,
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

- `chunk_size`: 文档分块大小（字符数）
- `chunk_overlap`: 分块重叠长度
- `top_k`: 返回最相关的文档数量
- `similarity_threshold`: 相似度阈值

### 应用配置 (`config/app_config.json`)

```json
{
  "default_model": "gpt-3.5-turbo",
  "api_base": "https://api.openai.com/v1",
  "temperature": 0.7
}
```

## 高级功能

### 多轮对话
- 应用自动保存对话历史
- 支持上下文连续对话
- 历史记录保存在 `chat_histories/` 目录

### 引用来源
- 每个答案都显示相关文档片段
- 点击可查看完整文档内容
- 支持追溯信息来源

### 知识库管理
- 创建多个独立知识库
- 支持知识库切换
- 支持知识库删除和重建

## 常见问题

**Q: 上传文档后没有反应？**
A: 检查文档格式是否支持，查看控制台是否有错误信息。

**Q: 对话没有引用来源？**
A: 确保知识库中有文档，且相似度阈值设置合理。

**Q: 如何使用本地模型？**
A: 安装 Ollama，启动本地模型，配置 API Base 为 `http://localhost:11434`。

**Q: 如何清理缓存？**
A: 删除以下目录：
```bash
rm -rf vector_db_storage/
rm -rf chat_histories/
rm -rf temp_uploads/
rm -rf hf_cache/
```

## 性能优化

### 向量数据库优化
- 调整 `chunk_size` 和 `chunk_overlap`
- 使用更高效的嵌入模型
- 定期清理无用的知识库

### 内存优化
- 限制单次上传文件大小
- 及时清理临时文件
- 使用流式处理大文件

## 日志查看

查看应用日志：
```bash
python view_logs.py
python view_logs.py --date 20241202
python view_logs.py --stage 查询对话
python view_logs.py --stats
```

日志保存在 `app_logs/` 目录。
