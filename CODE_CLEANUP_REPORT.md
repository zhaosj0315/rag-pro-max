# 代码清理分析报告

## 📊 分析概览

- **总文件数**: 187
- **未使用函数**: 0 个
- **未使用导入**: 333 个
- **重复函数**: 235 个
- **注释代码**: 0 行
- **过大函数**: 118 个

## 🗑️ 建议清理项目

### 未使用函数

### 未使用导入
- `shutil` in src/chat_utils_improved.py:11
- `datetime` in src/chat_utils_improved.py:15
- `shutil` in src/apppro.py:72
- `requests` in src/apppro.py:74
- `zipfile` in src/apppro.py:89
- `ThreadPoolExecutor` in src/apppro.py:92
- `multiprocessing` in src/apppro.py:93
- `enhanced_ocr_optimizer` in src/apppro.py:100
- `VectorStoreIndex` in src/apppro.py:102
- `SimpleDirectoryReader` in src/apppro.py:102

### 重复函数
- `__init__()` in src/metadata_manager.py, src/apppro.py
- `update_status()` in src/apppro.py, src/apppro.py
- `update_status()` in src/apppro.py, src/apppro.py
- `__init__()` in src/metadata_manager.py, src/logger.py
- `__init__()` in src/metadata_manager.py, src/file_processor.py
- `__init__()` in src/metadata_manager.py, src/rag_engine.py
- `__init__()` in src/metadata_manager.py, src/custom_embeddings.py
- `__init__()` in src/metadata_manager.py, src/ui/monitoring_dashboard.py
- `render_sidebar_widget()` in src/ui/monitoring_dashboard.py, src/ui/monitoring_dashboard.py
- `suggestions_fragment()` in src/apppro.py, src/ui/message_renderer.py
