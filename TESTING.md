# RAG Pro Max 测试指南

## 📊 最新测试结果 (v2.4.7)

**测试时间**: 2025-12-18 14:28:00  
**测试版本**: v2.4.7  
**测试环境**: macOS, Python 3.12.9

```
✅ 通过: 95/97
❌ 失败: 0/97
⏭️ 跳过: 9/97

✅ 所有核心测试通过！v2.4.7 UI交互极致优化版系统稳定。
```

## 🧪 测试覆盖范围

### 出厂测试 (factory_test.py)
- **基础功能**: 环境、配置、模块导入、日志系统
- **核心功能**: 文档处理、向量数据库、LLM连接
- **系统功能**: 存储目录、安全性、性能配置
- **v2.0+功能**: 增量更新、多模态、API扩展、智能启动

### 单元测试 (tests/test_*.py)
- **DocumentManager**: 文档管理逻辑验证
- **KBManager**: 知识库增删改查
- **WebCrawler**: 网页抓取与递归逻辑 (含 v2.4.7 修复)
- **UI Components**: 界面组件渲染逻辑

## 📋 测试概述

`factory_test.py` 是 RAG Pro Max 的全面出厂测试脚本，覆盖所有核心功能。每次代码修改后都应运行此测试，确保没有破坏现有功能。

## 🚀 快速开始

```bash
# 运行完整测试
python3 tests/factory_test.py

# 或使用脚本
./scripts/test.sh
```

## ✅ 详细覆盖清单

### 1. 环境检查 (14 项)
- Python 版本 (3.8+)
- 必需的包：streamlit, llama_index, chromadb, requests, ollama, sentence_transformers, torch
- 必需的文件：src/apppro.py, src/logger.py, src/custom_embeddings.py, src/metadata_manager.py, src/chat_utils_improved.py, requirements.txt

### 2. 配置文件测试 (3 项)
- rag_config.json - RAG 检索参数
- app_config.json - 应用默认配置
- projects_config.json - 项目配置

### 3. 核心模块导入测试 (20+ 项)
- 验证所有 `src/` 下的核心模块均可正确导入
- 检查循环依赖

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

## 📊 测试结果示例

测试完成后会显示：

```
============================================================
  测试结果汇总
============================================================
✅ 通过: 88/88
❌ 失败: 0/96
⏭️  跳过: 8/96

✅ 所有测试通过！系统可以发布。
```

### 退出码

- `0` - 所有测试通过
- `1` - 有测试失败

## 🔧 常见失败及处理

**1. 嵌入模型加载失败**
```
解决方案：确保 hf_cache 目录存在且包含模型文件，或检查网络连接
```

**2. Ollama 连接失败**
```
解决方案：启动 Ollama 服务 (ollama serve)
```

**3. 配置文件格式错误**
```
解决方案：检查 config/*.json 格式是否正确
```

## 🎯 CI/CD 集成

在 GitHub Actions 中使用：

```yaml
- name: Run Factory Tests
  run: python3 tests/factory_test.py
```

---

**最后更新**: 2025-12-18  
**测试版本**: v2.4.7

