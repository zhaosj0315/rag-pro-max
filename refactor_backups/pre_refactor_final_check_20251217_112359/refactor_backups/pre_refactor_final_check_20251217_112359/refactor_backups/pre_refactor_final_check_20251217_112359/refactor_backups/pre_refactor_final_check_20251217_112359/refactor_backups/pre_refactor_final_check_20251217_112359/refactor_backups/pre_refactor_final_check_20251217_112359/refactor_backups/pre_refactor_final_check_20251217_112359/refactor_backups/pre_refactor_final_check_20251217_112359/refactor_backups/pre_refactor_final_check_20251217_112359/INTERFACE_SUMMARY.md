# RAG Pro Max 接口汇总

## 📊 统计信息

- **Python模块**: 193个
- **类定义**: 164个  
- **函数定义**: 1367个
- **API端点**: 17个
- **配置文件**: 4个

## 🏗️ 模块结构

### api/
- api/api_server.py
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
- chat/suggestion_engine.py
- chat/suggestion_manager.py
- chat/web_suggestion_engine.py

### config/
- config/__init__.py
- config/config_interface.py
- config/config_loader.py
- config/config_validator.py
- config/force_local_llm.py
- config/industry_sites.py
- config/local_llm_config.py
- config/manifest_manager.py
- config/offline_config.py
- config/top20_sites.py
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
- core/v21_integration.py
- core/v23_integration.py
- core/v2_integration.py
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
- processors/batch_ocr_processor.py
- processors/concurrent_crawler.py
- processors/content_analyzer.py
- processors/crawl_monitor.py
- processors/crawl_optimizer.py
- processors/crawl_stats_manager.py
- processors/document_parser.py
- processors/enhanced_upload_handler.py
- processors/enhanced_web_crawler.py
- processors/index_builder.py
- processors/multimodal_processor.py
- processors/multimodal_vectorizer.py
- processors/summary_generator.py
- processors/table_parser.py
- processors/upload_handler.py
- processors/web_crawler.py
- processors/web_to_kb_processor.py
- processors/web_to_kb_simple.py

### query/
- query/query_handler.py
- query/query_processor.py
- query/query_rewriter.py

### queue/
- queue/queue_manager.py

### root/
- __init__.py
- apppro.py
- apppro_backup.py
- apppro_final.py
- apppro_minimal.py
- apppro_refactored.py
- apppro_ultra.py
- chat_utils_improved.py
- custom_embeddings.py
- file_processor.py
- logger.py
- metadata_manager.py
- rag_engine.py
- system_monitor.py
- web_crawl_integration_patch.py

### summary/
- summary/auto_summary.py

### ui/
- ui/__init__.py
- ui/advanced_config.py
- ui/batch_upload_ui.py
- ui/compact_sidebar.py
- ui/complete_sidebar.py
- ui/config_forms.py
- ui/controls_patch.py
- ui/crawl_progress.py
- ui/display_components.py
- ui/document_preview.py
- ui/enhanced_controls.py
- ui/export_ui.py
- ui/horizontal_tabs_sidebar.py
- ui/integrated_data_analysis_panel.py
- ui/kb_advanced_options.py
- ui/kb_management_ui.py
- ui/knowledge_graph.py
- ui/main_interface.py
- ui/main_kb_interface.py
- ui/message_renderer.py
- ui/mobile_responsive.py
- ui/model_selectors.py
- ui/monitoring_dashboard.py
- ui/page_style.py
- ui/performance_dashboard.py
- ui/performance_dashboard_enhanced.py
- ui/performance_monitor.py
- ui/progress_monitor.py
- ui/progress_tracker.py
- ui/quick_preview.py
- ui/responsive_layout.py
- ui/search_ui.py
- ui/sidebar_config.py
- ui/sidebar_manager.py
- ui/smart_data_analysis_panel.py
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
- utils/document_processor.py
- utils/dynamic_batch.py
- utils/enhanced_cache.py
- utils/enhanced_logger.py
- utils/enhanced_ocr_optimizer.py
- utils/error_handler.py
- utils/error_handler_enhanced.py
- utils/export_manager.py
- utils/force_batch_ocr_trigger.py
- utils/force_ocr_patch.py
- utils/friendly_error_handler.py
- utils/gpu_ocr_accelerator.py
- utils/gpu_optimizer.py
- utils/kb_name_optimizer.py
- utils/kb_utils.py
- utils/llm_manager.py
- utils/log_analyzer.py
- utils/memory.py
- utils/memory_leak_detector.py
- utils/memory_manager_enhanced.py
- utils/memory_optimizer.py
- utils/model_manager.py
- utils/model_utils.py
- utils/ocr_hotfix.py
- utils/ocr_optimizer.py
- utils/offline_patch.py
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
- utils/simple_terminal_logger.py
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
- `target_path`: ./temp_uploads/batch_1765167012
- `output_path`: ./vector_db_storage
- `llm_type_index`: 0
- `llm_url_ollama`: http://127.0.0.1:11434
- `llm_model_ollama`: gpt-oss:20b
- `llm_url_openai`: 
- `llm_key`: 
- `llm_model_openai`: 
- `embed_provider_index`: 0
- `embed_model_hf`: BAAI/bge-large-zh-v1.5
- `llm_type_idx`: 0
- `embed_provider_idx`: 0
- `embed_url_ollama`: 
- `embed_model_ollama`: 
- `skip_ocr`: True
- `version`: 2.2.1
- `last_updated`: 2025-12-11

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
- `target_path`: /Users/zhaosj/Documents/rag-pro-max/temp_uploads/batch_1765770928
- `output_path`: /Users/zhaosj/Documents/rag-pro-max/vector_db_storage
- `llm_type_idx`: 0
- `llm_url_ollama`: http://127.0.0.1:11434
- `llm_model_ollama`: gemma3n:latest
- `llm_url_openai`: 
- `llm_key`: 
- `llm_model_openai`: 
- `embed_provider_idx`: 0
- `embed_model_hf`: BAAI/bge-large-zh-v1.5
- `embed_url_ollama`: 
- `embed_model_ollama`: 

### app_config.json
- `target_path`: /Users/zhaosj/Documents/rag-pro-max/temp_uploads/batch_1765264053
- `output_path`: /Users/zhaosj/Documents/rag-pro-max/vector_db_storage
- `llm_type_idx`: 0
- `llm_url_ollama`: http://localhost:11434
- `llm_model_ollama`: gpt-oss:20b
- `llm_url_openai`: 
- `llm_key`: 
- `llm_model_openai`: 
- `embed_provider_idx`: 0
- `embed_model_hf`: BAAI/bge-small-zh-v1.5
- `embed_url_ollama`: 
- `embed_model_ollama`: 
- `llm_provider`: Ollama
- `default_model`: gpt-oss:20b


## 📝 生成时间

Wed Dec 17 07:16:01 CST 2025

---

*此文档由 `scripts/align_docs_with_code.py` 自动生成*
