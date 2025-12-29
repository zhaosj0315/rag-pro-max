# RAG Pro Max 接口汇总

## 📊 统计信息

- **Python模块**: 177个
- **类定义**: 160个  
- **函数定义**: 1370个
- **API端点**: 11个
- **配置文件**: 3个

## 🏗️ 模块结构

### api/
- api/fastapi_server.py

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
- chat/suggestion_manager.py
- chat/unified_suggestion_engine.py

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
- config/prompt_manager.py
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
- monitoring/unified_monitoring_system.py

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
- processors/unified_document_processor.py
- processors/upload_handler.py
- processors/web_crawler.py
- processors/web_to_kb_processor.py

### query/
- query/multi_kb_query_engine.py
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
- services/configurable_industry_service.py
- services/file_service.py
- services/knowledge_base_service.py
- services/unified_config_service.py

### summary/
- summary/auto_summary.py

### ui/
- ui/__init__.py
- ui/advanced_config.py
- ui/complete_sidebar.py
- ui/config_forms.py
- ui/crawl_progress.py
- ui/display_components.py
- ui/document_preview.py
- ui/enhanced_controls.py
- ui/horizontal_tabs_sidebar.py
- ui/industry_config_interface.py
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
- ui/tabbed_sidebar.py
- ui/unified_config_components.py
- ui/unified_dialogs.py
- ui/unified_display_components.py
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

- `DELETE /cache`
- `GET /`
- `GET /cache/stats`
- `GET /health`
- `GET /kb/{kb_name}/incremental-stats`
- `GET /knowledge-bases`
- `GET /multimodal/formats`
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
- `target_path`: /Users/zhaosj/Documents/rag-pro-max/temp_uploads/batch_1766974677
- `output_path`: /Users/zhaosj/Documents/rag-pro-max/vector_db_storage
- `llm_type_idx`: 1
- `llm_url_ollama`: http://localhost:11434
- `llm_model_ollama`: gpt-oss:20b
- `llm_url_openai`: https://cn.gptapi.asia/v1
- `llm_key`: sk-nWYfVnuZMkPnLFsR5d02Af5b6c31478889C12520775f8f12
- `llm_model_openai`: chatgpt-4o-latest
- `embed_provider_idx`: 0
- `embed_model_hf`: sentence-transformers/all-MiniLM-L6-v2
- `embed_url_ollama`: 
- `embed_model_ollama`: 
- `llm_provider`: Ollama
- `llm_url_other`: https://cn.gptapi.asia/v1
- `llm_key_other`: sk-nWYfVnuZMkPnLFsR5d02Af5b6c31478889C12520775f8f12
- `llm_model_other`: chatgpt-4o-latest
- `llm_provider_label`: Ollama (本地)
- `llm_url`: https://cn.gptapi.asia/v1
- `llm_model`: chatgpt-4o-latest

### rag_config.json
- `target_path`: rag_storage
- `llm_provider`: Ollama
- `llm_model`: qwen2.5:7b
- `embed_provider`: HuggingFace (本地/极速)
- `embed_model`: sentence-transformers/all-MiniLM-L6-v2


## 📝 生成时间

Mon Dec 29 10:22:19 CST 2025

---

*此文档由 `scripts/align_docs_with_code.py` 自动生成*
