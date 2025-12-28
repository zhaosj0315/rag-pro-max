# RAG Pro Max v2.7.2 接口汇总

## 📊 统计信息

- **Python模块**: 191个
- **类定义**: 91个
- **函数定义**: 1255个
- **API端点**: 23个
- **配置文件**: 3个
- **统一组件**: 10个
- **测试覆盖率**: 93%

## 🏗️ v2.7.2 模块结构

### 🎨 界面重构 (v2.7.2)
- **src/apppro.py**: 主入口，新增 **管理模式高级选项** (Update Knowledge Base Advanced Options)
- **src/ui/kb_management_ui.py**: 知识库管理界面逻辑优化

### 📂 文件详情与取证 (v2.7.1)
- **src/utils/file_system_utils.py**: 30+项属性挖掘与 macOS 深度集成
- **src/ui/unified_dialogs.py**: 统一文件详情对话框 (Split View 布局)

### 🤖 智能推荐系统 (v2.6.0)
- services/recommendation_service.py
- ui/recommendation_ui.py
- utils/llm_context_generator.py
- utils/deduplication_engine.py

### api/
- api/fastapi_server.py
- api/recommendation_api.py

### app/
- app/__init__.py
- app/app_initializer.py
- app/main_app.py

### app_logging/
- app_logging/__init__.py
- app_logging/log_manager.py
- app_logging/progress_logger.py

### chat/
- chat/__init__.py
- chat/chat_engine.py
- chat/chat_interface.py
- chat/history_manager.py
- chat/suggestion_engine.py
- chat/suggestion_manager.py
- chat/web_suggestion_engine.py

### common/
- common/__init__.py
- common/business.py
- common/config.py
- common/utils.py

### config/
- config/__init__.py
- config/config_interface.py
- config/config_loader.py
- config/config_validator.py
- config/manifest_manager.py
- config/unified_sites.py

### core/
- core/__init__.py
- core/app_config.py
- core/app_main.py
- core/business_logic.py
- core/environment.py
- core/main_controller.py
- core/optimization_manager.py
- core/state_manager.py
- core/v23_integration.py
- core/version.py

### document/
- document/__init__.py
- document/document_manager_ui.py

### documents/
- documents/document_manager.py

### engines/
- engines/__init__.py
- engines/smart_router.py
- engines/sql_engine.py

### kb/
- kb/__init__.py
- kb/document_viewer.py
- kb/enhanced_kb_manager.py
- kb/incremental_updater.py
- kb/kb_interface.py
- kb/kb_loader.py
- kb/kb_manager.py
- kb/kb_operations.py
- kb/kb_processor.py

### monitor/
- monitor/__init__.py
- monitor/system_monitor_ui.py

### monitoring/
- monitoring/file_watcher.py

### processors/
- processors/__init__.py
- processors/async_web_crawler.py
- processors/concurrent_crawler.py
- processors/content_analyzer.py
- processors/crawl_optimizer.py
- processors/crawl_stats_manager.py
- processors/document_parser.py
- processors/enhanced_upload_handler.py
- processors/enhanced_web_crawler.py
- processors/index_builder.py
- processors/multimodal_processor.py
- processors/multimodal_vectorizer.py
- processors/summary_generator.py
- processors/upload_handler.py
- processors/web_crawler.py
- processors/web_to_kb_processor.py

### query/
- query/query_handler.py
- query/query_processor.py
- query/query_rewriter.py

### queue/
- queue/queue_manager.py

### root/
- __init__.py
- apppro.py
- chat_utils_improved.py
- custom_embeddings.py
- file_processor.py
- logger.py
- metadata_manager.py
- rag_engine.py
- system_monitor.py

### services/
- services/__init__.py
- services/config_service.py
- services/file_service.py
- services/knowledge_base_service.py

### summary/
- summary/auto_summary.py

### ui/
- ui/__init__.py
- ui/advanced_config.py
- ui/enhanced_controls.py
- ui/horizontal_tabs_sidebar.py
- ui/kb_advanced_options.py
- ui/kb_management_ui.py
- ui/knowledge_graph.py
- ui/main_interface.py
- ui/main_kb_interface.py
- ui/message_renderer.py
- ui/model_selectors.py
- ui/monitoring_dashboard.py
- ui/page_style.py
- ui/performance_dashboard_enhanced.py
- ui/performance_monitor.py
- ui/progress_monitor.py
- ui/progress_tracker.py
- ui/responsive_layout.py
- ui/search_ui.py
- ui/sidebar_config.py
- ui/sidebar_manager.py
- ui/status_bar.py
- ui/suggestion_panel.py
- ui/tabbed_sidebar.py
- ui/user_experience_enhanced.py
- ui/web_to_kb_interface.py

### upload/
- upload/__init__.py
- upload/upload_interface.py

### utils/
- utils/__init__.py
- utils/adaptive_scheduler.py
- utils/adaptive_throttling.py
- utils/aggressive_ocr_config.py
- utils/alert_system.py
- utils/app_utils.py
- utils/async_pipeline.py
- utils/batch_ocr_processor.py
- utils/batch_operations.py
- utils/concurrency_manager.py
- utils/concurrency_monitor.py
- utils/cpu_monitor.py
- utils/cpu_throttle.py
- utils/directory_selector.py
- utils/document_processor.py
- utils/dynamic_batch.py
- utils/enhanced_cache.py
- utils/enhanced_logger.py
- utils/enhanced_ocr_optimizer.py
- utils/error_handler_enhanced.py
- utils/export_manager.py
- utils/file_system_utils.py
- utils/gpu_ocr_accelerator.py
- utils/gpu_optimizer.py
- utils/kb_name_optimizer.py
- utils/kb_utils.py
- utils/llm_manager.py
- utils/log_analyzer.py
- utils/memory.py
- utils/memory_manager_enhanced.py
- utils/memory_optimizer.py
- utils/model_manager.py
- utils/model_utils.py
- utils/ocr_optimizer.py
- utils/offline_embeddings.py
- utils/offline_query_engine.py
- utils/optimized_ocr_processor.py
- utils/parallel_executor.py
- utils/parallel_ocr_processor.py
- utils/parallel_tasks.py
- utils/pdf_page_reader.py
- utils/performance_monitor.py
- utils/query_cache.py
- utils/resource_monitor.py
- utils/safe_parallel_tasks.py
- utils/search_engine.py
- utils/smart_scheduler.py
- utils/task_scheduler.py
- utils/terminal_progress.py
- utils/vectorization_wrapper.py

## 🔌 API端点

- `DELETE /api/kb/{kb_name}`
- `DELETE /cache`
- `GET /`
- `GET /`
- `GET /api/health`
- `GET /api/kb`
- `GET /cache/stats`
- `GET /health`
- `GET /kb/{kb_name}/incremental-stats`
- `GET /knowledge-bases`
- `GET /multimodal/formats`
- `POST /api/query`
- `POST /api/upload`
- `POST /incremental-update`
- `POST /query`
- `POST /query-multimodal`
- `POST /upload-multimodal`

## ⚙️ 配置文件

### config/app_config.json
- `llm`: {'provider': 'OpenAI', 'model': 'gpt-3.5-turbo', 'api_base': 'https://api.openai.com/v1', 'api_key': '', 'temperature': 0.7}
- `embedding`: {'provider': 'HuggingFace', 'model': 'sentence-transformers/all-MiniLM-L6-v2', 'device': 'auto'}
- `rag`: {'chunk_size': 500, 'chunk_overlap': 50, 'top_k': 5, 'similarity_threshold': 0.7}
- `system`: {'max_file_size': 104857600, 'temp_cleanup_hours': 24, 'max_concurrent_tasks': 4}
- `llm_model_ollama`: gpt-oss:20b

### config/rag_config.json
- `output_base`: ./vector_db_storage
- `target_path`: /Users/zhaosj/Documents/用所选项目新建的文件夹/temp_uploads/batch_1765164435
- `llm_type_idx`: 0
- `embed_idx`: 0
- `output_path`: /Users/zhaosj/Documents/用所选项目新建的文件夹/vector_db_storage
- `llm_url_ollama`: http://localhost:11434
- `llm_model_ollama`: gpt-oss:20b
- `llm_url_openai`: 
- `llm_key`: 
- `llm_model_openai`: 
- `embed_provider_idx`: 0
- `embed_model_hf`: BAAI/bge-large-zh-v1.5
- `embed_url_ollama`: 
- `embed_model_ollama`: 
- `chunk_size`: 512
- `top_k`: 3
- `rerank_enabled`: True
- `rerank_model`: BAAI/bge-reranker-base
- `parallel_workers`: 20
- `llm_provider`: Ollama

### rag_config.json
- `target_path`: rag_storage
- `llm_provider`: Ollama
- `llm_model`: qwen2.5:7b
- `embed_provider`: HuggingFace (本地/极速)
- `embed_model`: sentence-transformers/all-MiniLM-L6-v2


## 📝 生成时间

Sun Dec 28 07:47:51 CST 2025

---

*此文档由 `scripts/align_docs_with_code.py` 自动生成*