# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.2.0] - 2025-12-08

### 🔧 重构 (Stage 3 - UI 组件分离)

#### Stage 3.1: 纯展示组件
- **UI 展示组件**：提取到 `ui/display_components.py` (226行)
  - 消息统计渲染组件
  - 引用来源渲染组件
  - 格式化工具函数（时间、Token）
  - 相关性标签生成
- **代码减少**：apppro.py -21行

#### Phase 3.2.1: 模型选择器组件
- **模型选择器**：提取到 `ui/model_selectors.py` (282行)
  - Ollama 模型选择器
  - OpenAI 模型选择器
  - HuggingFace 嵌入模型选择器
  - 自动模型列表获取
  - 模型下载功能
- **代码减少**：apppro.py -77行

#### Phase 3.2.2: 配置表单组件
- **配置表单**：提取到 `ui/config_forms.py` (180行)
  - LLM 配置表单
  - Embedding 配置表单
  - 完整基础配置区域
- **代码减少**：apppro.py -162行

#### Phase 3.2.3: 高级功能配置
- **高级配置**：提取到 `ui/advanced_config.py` (101行)
  - Re-ranking 配置组件
  - BM25 配置组件
  - 完整高级功能区域
- **代码减少**：apppro.py -42行

### 📊 代码质量
- **apppro.py**：3483 → 3181 行 (-302行, -8.7%)
- **新增模块**：5 个 UI 组件 (911行)
- **新增测试**：2 个测试文件 (203行)
- **模块化提升**：显著
- **可维护性**：大幅提升

### 🐛 修复
- **Ollama 状态检测**：使用正确的 `/api/tags` 端点
- **导入路径**：修复 `utils` → `src.utils` 导入问题
- **配置文件路径**：硬编码绝对路径 → 相对路径

### 🧪 测试
- **出厂测试**：62/67 通过 (92.5%)
- **UI 组件测试**：完整覆盖
- **功能验证**：所有功能正常

---

## [1.1.5] - 2025-12-08

### 🔧 重构 (Stage 2)
- **RAG 核心引擎**：提取到 `rag_engine.py` (286行)
  - RAGEngine 类封装知识库创建、加载、查询
  - 支持检索器、查询引擎、对话引擎获取
  - 统计信息和知识库管理
- **资源监控模块**：提取到 `utils/resource_monitor.py` (114行)
  - CPU/内存/GPU 使用率监控
  - 系统统计信息获取
  - 资源限流判断
- **模型工具模块**：提取到 `utils/model_utils.py` (226行)
  - Ollama 服务状态检查
  - 远程模型列表获取
  - HF 模型存在性检查
  - 知识库维度检测
  - 模型自动切换

### ✨ 新增
- **11 个单元测试**：覆盖新增的 3 个模块
- **完整文档字符串**：所有函数都有详细说明
- **类型注解**：提升代码可读性和 IDE 支持

### 📊 代码质量
- 新增模块：626 行
- apppro.py：3505 → 3492 行 (-13行)
- 测试通过率：64/67 (95.5%)
- 模块化程度：显著提升

---

## [1.1.4] - 2025-12-08

### 🔧 重构
- **模型管理模块化**：将嵌入模型和 LLM 加载逻辑提取到 `utils/model_manager.py`
- **文档处理模块化**：将文档处理函数提取到 `utils/document_processor.py`
- **配置管理模块化**：将配置和清单管理提取到 `utils/config_manager.py`
- **聊天管理模块化**：将对话历史管理提取到 `utils/chat_manager.py`
- **知识库管理模块化**：将知识库操作提取到 `utils/kb_manager.py`
- **代码精简**：主文件 `apppro.py` 减少约 330 行代码
- **单一职责**：各模块职责清晰，易于维护和测试

### 🐛 修复
- **嵌入模型维度不匹配**：修复 OpenAI 默认模型（1536维）干扰本地模型（1024维）的问题
- **环境变量污染**：清理 `OPENAI_API_KEY` 对 LlamaIndex 默认行为的影响
- **模型加载时机**：确保在创建知识库前正确设置嵌入模型

### ✨ 新增
- **模型加载日志**：详细记录模型加载过程和维度信息
- **错误处理增强**：更友好的超时和错误提示
- **出厂测试扩展**：新增 16 项模块测试

### 📦 模块结构
```
utils/
├── memory.py              # 内存管理
├── model_manager.py       # 模型管理 (新增)
├── document_processor.py  # 文档处理 (新增)
├── config_manager.py      # 配置管理 (新增)
├── chat_manager.py        # 聊天历史管理 (新增)
└── kb_manager.py          # 知识库管理 (新增)
```

### 🔍 技术细节

**模型管理 (model_manager.py)**:
- `load_embedding_model()`: 统一的嵌入模型加载接口
- `load_llm_model()`: 统一的 LLM 加载接口
- `set_global_embedding_model()`: 设置全局嵌入模型
- `set_global_llm_model()`: 设置全局 LLM
- `clean_proxy()`: 代理清理

**文档处理 (document_processor.py)**:
- `sanitize_filename()`: 文件名清理
- `get_file_type()`: 文件类型识别
- `get_file_info()`: 文件信息提取
- `get_relevance_label()`: 相关性标签
- `load_pptx_file()`: PPTX 文件加载

**配置管理 (config_manager.py)**:
- `load_config()` / `save_config()`: 应用配置管理
- `load_manifest()` / `update_manifest()`: 知识库清单管理
- `get_config_value()` / `set_config_value()`: 配置项读写

**聊天管理 (chat_manager.py)**:
- `load_chat_history()` / `save_chat_history()`: 对话历史管理
- `clear_chat_history()`: 清空对话历史
- `chat_history_exists()`: 检查历史是否存在

**知识库管理 (kb_manager.py)**:
- `rename_kb()` / `delete_kb()`: 知识库重命名和删除
- `get_existing_kbs()`: 获取知识库列表
- `auto_save_kb_info()` / `get_kb_info()`: 知识库信息管理
- `kb_exists()`: 检查知识库是否存在

---

## [1.1.3] - 2025-12-08

### ✨ 优化
- **GPU利用率优化**：从 29.6% 提升到 80-99%
- **统一内存管理**：`cleanup_memory()` 函数统一管理内存和显存
- **显存自动清理**：支持 CUDA 和 MPS 显存缓存清理
- **torch.compile 加速**：启用 PyTorch 2.0+ 编译优化

### 🧪 测试
- 新增 7 项出厂测试
- 内存管理测试
- GPU 优化测试

---

## [1.1.2] - 2025-12-08

### ✨ 新增
- 效果对比模式
- 使用统计可视化
- 视觉反馈优化
- 重复 key 检查工具

---

## [1.1.1] - 2025-12-07

### ✨ 新增
- ⚡ 一键配置（新手模式）
- 💡 专业术语通俗化
- 📂 侧边栏分组优化

---

## [1.0.0] - 2024-11-30

### ✨ 初始版本
- 📄 支持多种文档格式（PDF、TXT、DOCX、MD、XLSX、PPTX、CSV、HTML、JSON、ZIP）
- 🔍 向量检索功能
- 💬 多轮对话支持
- 📦 macOS 打包支持
- 📊 系统监控面板
- 🔒 文件上传安全验证
- 💻 多核优化（80 线程）

---

## 版本说明

### 版本号格式：主版本.次版本.修订号

- **主版本**：不兼容的 API 修改
- **次版本**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型

- **新增 (Added)**：新功能
- **修改 (Changed)**：现有功能的变更
- **弃用 (Deprecated)**：即将移除的功能
- **移除 (Removed)**：已移除的功能
- **修复 (Fixed)**：Bug 修复
- **安全 (Security)**：安全相关的修复
- **优化 (Optimized)**：性能优化
- **重构 (Refactored)**：代码重构
