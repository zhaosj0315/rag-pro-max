# RAG Pro Max 测试指南

## 📊 最新测试结果 (v2.3.1)

**测试时间**: 2025-12-10 23:17:00  
**测试版本: v2.3.1  
**测试环境**: macOS, Python 3.12.9

```
✅ 通过: 67/72 (出厂测试)
❌ 失败: 0/72
⏭️ 跳过: 5/72

✅ 通过: 25/25 (v2.0可行性测试)
✅ 通过: 9/9 (v2.0功能测试)
✅ 通过: 7/7 (v2.1功能测试)

✅ 所有测试通过！v2.1系统可以发布。
```

## 🧪 v2.1 测试覆盖

### 出厂测试 (factory_test.py)
- **基础功能**: 环境、配置、模块导入、日志系统
- **核心功能**: 文档处理、向量数据库、LLM连接
- **系统功能**: 存储目录、安全性、性能配置
- **v2.0功能**: 增量更新、多模态、API扩展、智能启动

### v2.0可行性测试 (test_v2.0_feasibility.py)
- **增量更新**: 文件哈希、变化检测、元数据持久化
- **多模态支持**: 文件类型检测、OCR功能、表格提取
- **API扩展**: 版本检查、路由验证、数据模型
- **集成功能**: 模块初始化、方法检查、智能启动

### v2.0功能测试 (test_v2_features.py)
- **单元测试**: 各模块独立功能测试
- **边界测试**: 异常情况和错误处理
- **模拟测试**: Mock对象和接口测试

## 📋 测试概述

`factory_test.py` 是 RAG Pro Max 的全面出厂测试脚本，覆盖所有核心功能。每次代码修改后都应运行此测试，确保没有破坏现有功能。

## 🚀 快速开始

```bash
# 运行完整测试
python3 tests/factory_test.py

# 或使用脚本
./scripts/test.sh
```

## ✅ 测试覆盖范围

### 1. 环境检查 (14 项)
- Python 版本 (3.8+)
- 必需的包：streamlit, llama_index, chromadb, requests, ollama, sentence_transformers, torch
- 必需的文件：src/apppro.py, src/logger.py, src/custom_embeddings.py, src/metadata_manager.py, src/chat_utils_improved.py, requirements.txt

### 2. 配置文件测试 (3 项)
- rag_config.json - RAG 检索参数 (12个配置项)
- app_config.json - 应用默认配置 (13个配置项)
- projects_config.json - 项目配置

### 3. 核心模块导入测试 (17 项)
- 包括新修复的 src.core.environment 模块
- terminal_logger 模块
- custom_embeddings 模块
- metadata_manager 模块
- chat_utils_improved 模块

### 4. 日志系统测试 (2 项)
- 日志目录创建
- 日志写入功能

### 5. 文档处理测试 (4 项)
- TXT 文件处理
- JSON 文件处理
- MD 文件处理
- 临时文件管理

### 6. 向量数据库测试 (3 项)
- 嵌入模型加载 (BAAI/bge-small-zh-v1.5)
- 文档向量化
- 向量检索

### 7. LLM 连接测试 (2 项)
- Ollama 本地服务连接
- OpenAI API Key 配置

### 8. 存储目录测试 (5 项)
- vector_db_storage - 向量数据库
- chat_histories - 对话历史
- temp_uploads - 临时上传
- hf_cache - HuggingFace 缓存
- app_logs - 应用日志

### 9. 安全性测试 (2 项)
- Subprocess 文件打开漏洞检查
- 安全文件打开方法验证

### 10. 性能配置测试 (3 项)
- CPU 核心数检测
- 多线程支持 (ThreadPoolExecutor)
- 多进程支持 (ProcessPoolExecutor)

## 📊 测试结果

测试完成后会显示：

```
============================================================
  测试结果汇总
============================================================
✅ 通过: 44/44
❌ 失败: 0/67
⏭️  跳过: 3/67

✅ 所有测试通过！系统可以发布。
```

### 退出码

- `0` - 所有测试通过
- `1` - 有测试失败

## 🔧 测试失败处理

如果测试失败，会显示详细的错误信息：

```
失败的测试:
  - 测试名称: 错误详情
```

### 常见问题

**1. 嵌入模型加载失败**
```
解决方案：确保 hf_cache 目录存在且包含模型文件
```

**2. Ollama 连接失败**
```
解决方案：启动 Ollama 服务
ollama serve
```

**3. 配置文件格式错误**
```
解决方案：检查 JSON 格式是否正确
```

## 🎯 集成到开发流程

### Git Pre-commit Hook

创建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash
echo "运行出厂测试..."
python3 tests/factory_test.py
if [ $? -ne 0 ]; then
    echo "❌ 测试失败，提交已取消"
    exit 1
fi
echo "✅ 测试通过，继续提交"
```

### CI/CD 集成

在 GitHub Actions 中使用：

```yaml
- name: Run Factory Tests
  run: python3 tests/factory_test.py
```

## 📝 添加新测试

在 `tests/factory_test.py` 中添加新的测试函数：

```python
def test_new_feature():
    print_header("11. 新功能测试")
    
    try:
        # 测试逻辑
        print_test("新功能", "PASS", "测试通过")
    except Exception as e:
        print_test("新功能", "FAIL", str(e))
```

然后在 `main()` 函数中调用：

```python
def main():
    # ... 其他测试
    test_new_feature()
```

## 🚨 注意事项

1. **离线模式**：测试使用离线模式，不会连接 HuggingFace
2. **本地缓存**：需要预先下载嵌入模型到 `hf_cache` 目录
3. **Ollama 可选**：如果 Ollama 未启动，相关测试会跳过
4. **临时文件**：测试会自动清理临时文件

## 📈 性能基准

测试运行时间（M4 Max）：

- 完整测试：~15-20 秒
- 环境检查：~1 秒
- 向量数据库测试：~10 秒（首次加载模型）
- 其他测试：~5 秒

## 🔄 持续改进

测试脚本会随着项目发展不断更新：

- ✅ v1.0 - 基础功能测试（44 项）
- 🔜 v1.1 - Re-ranking 功能测试
- 🔜 v1.2 - BM25 混合检索测试
- 🔜 v1.3 - 性能基准测试

---

**最后更新**: 2025-12-07  
**测试版本**: v1.0  
**测试项目**: 44 项
