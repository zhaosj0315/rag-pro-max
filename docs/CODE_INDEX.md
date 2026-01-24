# 🗺️ RAG Pro Max 代码全典 (Code Index)

> 本文档由脚本自动生成，用于快速索引项目结构与功能。

## 目录结构

### 📄 src/__init__.py

---

### 📄 src/apppro.py
- **⚡ Functions**:
  - `def update_all_model_configs`: 统一更新所有地方的模型配置
  - `def display_user_message_safe`: 显示用户消息，包含附件信息 (Safe Mode)
  - `def enhanced_web_search`: 增强的联网搜索功能
  - `def render_smart_visualization`: [v5.9.3] 业务级全能画板：全局健壮性升级，彻底解决层级图表类型冲突。
  - `def keep_adv_open`: 无描述
  - `def keep_adv_open_update`: 无描述
  - `def jump_to_knowledge_base`: 统一的知识库跳转逻辑
  - `def process_knowledge_base_logic`: 处理知识库逻辑 (Stage 4.2 - 使用 IndexBuilder)
  - `def render_isolated_toggle`: 无描述

---

### 📄 src/chat_utils_improved.py
**📝 描述**: 改进的对话处理工具 - 稳定性优先

- **⚡ Functions**:
  - `def load_chat_history_safe`: 安全加载对话历史
  - `def _extract_keywords`: 提取文本关键词
  - `def _is_similar_question`: 检测两个问题是否相似
  - `def generate_follow_up_questions_safe`: 安全地生成追问（带超时控制和错误处理）

---

### 📄 src/custom_embeddings.py
- **🏗️ Classes**:
  - `class CustomHuggingFaceEmbedding`: 自定义 HuggingFace 嵌入，支持大 batch_size
- **⚡ Functions**:
  - `def create_custom_embedding`: 创建自定义嵌入模型

---

### 📄 src/file_processor.py
- **🏗️ Classes**:
  - `class FileProcessResult`: 无描述
- **⚡ Functions**:
  - `def _ocr_page`: OCR单页处理（用于多进程）
  - `def _load_single_file`: 单个文件加载函数（优化：直接读取文件内容，避免 SimpleDirectoryReader 开销）
  - `def _process_batch`: 批量处理文件（在独立进程中运行）
  - `def scan_directory_safe`: 安全扫描目录，返回成功加载的文档和处理结果（多线程并行）

---

### 📄 src/logger.py

---

### 📄 src/metadata_manager.py
**📝 描述**: 元数据管理模块 - 增强文件属性追踪

- **🏗️ Classes**:
  - `class MetadataManager`: 文件元数据管理器

---

### 📄 src/rag_engine.py
**📝 描述**: RAG Pro Max - RAG 核心引擎

- **🏗️ Classes**:
  - `class RAGEngine`: RAG 核心引擎
- **⚡ Functions**:
  - `def create_rag_engine`: 创建 RAGEngine 实例的工厂函数

---

### 📄 src/system_monitor.py
**📝 描述**: RAG Pro Max 系统监控大屏 v3.0

- **🏗️ Classes**:
  - `class SystemMonitor`: 无描述

---

### 📄 src/ui/__init__.py
**📝 描述**: UI 组件模块


---

### 📄 src/ui/advanced_config.py
**📝 描述**: 高级功能配置组件

- **⚡ Functions**:
  - `def render_rerank_config`: 渲染 Re-ranking 配置
  - `def render_bm25_config`: 渲染 BM25 配置
  - `def render_advanced_features`: 渲染完整的高级功能配置区域

---

### 📄 src/ui/config_forms.py
**📝 描述**: 配置表单组件

- **⚡ Functions**:
  - `def render_llm_config`: 渲染 LLM 配置表单 (v3.2 顶部导航 + 修复数据覆盖 Bug)
  - `def _render_remote_model_selector`: 辅助函数：渲染远程模型选择器 (v2.9.5 自动加载优化)
  - `def _save_and_apply_config`: 辅助函数：保存并应用配置
  - `def render_embedding_config`: 渲染 Embedding 配置表单 (优化版)
  - `def render_basic_config`: 渲染完整的基础配置区域

---

### 📄 src/ui/crawl_progress.py
**📝 描述**: 爬虫进度可视化组件

- **🏗️ Classes**:
  - `class CrawlProgressMonitor`: 无描述
  - `class AsyncCrawlUI`: 异步爬虫UI包装器
- **⚡ Functions**:
  - `def demo_progress_monitor`: 演示进度监控

---

### 📄 src/ui/display_components.py
**📝 描述**: 纯展示组件模块

- **⚡ Functions**:
  - `def get_relevance_label`: 根据相似度分数返回相关性标签
  - `def format_time_duration`: 格式化时间显示
  - `def format_token_count`: 格式化 token 数量显示
  - `def render_message_stats`: 渲染消息统计信息
  - `def render_source_references`: 渲染引用来源 - 卡片式优化版本
  - `def render_kb_info_card`: 渲染知识库信息卡片
  - `def render_system_stats`: 渲染系统资源统计 - 使用统一组件
  - `def render_error_message`: 渲染错误消息
  - `def render_success_message`: 渲染成功消息
  - `def render_warning_message`: 渲染警告消息

---

### 📄 src/ui/document_preview.py
**📝 描述**: 文档预览 UI 组件

- **⚡ Functions**:
  - `def show_upload_preview`: 显示上传预览 - 使用统一组件
  - `def show_file_preview_dialog`: 显示文件预览对话框 - 使用统一组件
  - `def show_kb_documents`: 显示知识库文档列表
  - `def render_document_details`: 渲染文档详情
  - `def confirm_delete_document`: 确认删除文档对话框

---

### 📄 src/ui/document_progress.py
**📝 描述**: 文档处理进度显示组件

- **🏗️ Classes**:
  - `class DocumentProcessingProgress`: 无描述

---

### 📄 src/ui/enhanced_controls.py
**📝 描述**: 增强的控制组件 - OCR选择、摘要控制、聊天控制

- **🏗️ Classes**:
  - `class EnhancedControls`: 增强的控制组件
- **⚡ Functions**:
  - `def render_enhanced_sidebar_controls`: 在侧边栏渲染增强控制组件

---

### 📄 src/ui/industry_config_interface.py
**📝 描述**: 行业网站配置界面

- **🏗️ Classes**:
  - `class IndustryConfigInterface`: 行业网站配置界面
- **⚡ Functions**:
  - `def render_industry_config_interface`: 渲染行业配置界面的入口函数

---

### 📄 src/ui/knowledge_graph.py
**📝 描述**: 知识图谱可视化组件

- **🏗️ Classes**:
  - `class KnowledgeGraph`: 知识图谱可视化

---

### 📄 src/ui/message_renderer.py
- **🏗️ Classes**:
  - `class MessageRenderer`: 消息渲染器

---

### 📄 src/ui/mobile_adapter.py
**📝 描述**: 移动端适配器 (Mobile Adapter)

- **🏗️ Classes**:
  - `class MobileAdapter`: 移动端视图适配器

---

### 📄 src/ui/model_selectors.py
- **⚡ Functions**:
  - `def render_ollama_model_selector`: 渲染 Ollama 模型选择器 (不包含刷新按钮，由外部容器提供)
  - `def render_openai_model_selector`: 渲染 OpenAI 兼容模型选择器 (不包含刷新按钮，由外部容器提供)
  - `def render_hf_embedding_selector`: 渲染 HuggingFace 嵌入模型选择器
  - `def _fetch_ollama_models`: 获取 Ollama 模型列表
  - `def _download_hf_model`: 下载 HuggingFace 模型

---

### 📄 src/ui/monitoring_dashboard.py
- **⚡ Functions**:
  - `def render_monitoring_dashboard`: 渲染系统监控仪表盘

---

### 📄 src/ui/page_style.py
**📝 描述**: 页面样式模块

- **🏗️ Classes**:
  - `class PageStyle`: 页面样式管理器

---

### 📄 src/ui/performance_dashboard_enhanced.py
**📝 描述**: 增强的性能监控仪表板

- **🏗️ Classes**:
  - `class PerformanceDashboard`: 实时性能仪表板

---

### 📄 src/ui/performance_monitor.py
**📝 描述**: 性能监控面板

- **🏗️ Classes**:
  - `class PerformanceMonitor`: 性能监控器
- **⚡ Functions**:
  - `def get_monitor`: 获取全局性能监控器

---

### 📄 src/ui/progress_monitor.py
**📝 描述**: 实时进度监控器

- **🏗️ Classes**:
  - `class ProgressInfo`: 进度信息
  - `class ProgressMonitor`: 实时进度监控器

---

### 📄 src/ui/progress_tracker.py
**📝 描述**: 实时进度追踪器

- **🏗️ Classes**:
  - `class ProgressTracker`: 无描述
- **⚡ Functions**:
  - `def get_progress_tracker`: 获取进度追踪器实例
  - `def render_progress_panel`: 渲染进度面板 - 显示系统任务和历史记录

---

### 📄 src/ui/responsive_layout.py
**📝 描述**: 响应式布局管理器

- **🏗️ Classes**:
  - `class ResponsiveLayout`: 无描述

---

### 📄 src/ui/role_manager_ui.py
**📝 描述**: 角色管理界面

- **🏗️ Classes**:
  - `class RoleManagerUI`: 角色管理器 UI

---

### 📄 src/ui/scroll_buttons.py
- **⚡ Functions**:
  - `def inject_scroll_buttons`: 注入悬浮滚动按钮 (回到顶部/直达底部)

---

### 📄 src/ui/search_ui.py
**📝 描述**: 搜索UI组件

- **⚡ Functions**:
  - `def render_search_interface`: 渲染搜索界面
  - `def render_tag_management`: 渲染标签管理界面
  - `def render_search_analytics`: 渲染搜索分析界面

---

### 📄 src/ui/sidebar_config.py
**📝 描述**: 侧边栏配置模块

- **🏗️ Classes**:
  - `class SidebarConfig`: 侧边栏配置管理器

---

### 📄 src/ui/status_bar.py
**📝 描述**: 状态栏组件

- **🏗️ Classes**:
  - `class StatusBar`: 状态栏管理器

---

### 📄 src/ui/tabbed_sidebar.py
**📝 描述**: 多标签页侧边栏组件

- **🏗️ Classes**:
  - `class TabbedSidebar`: 多标签页侧边栏管理器
- **⚡ Functions**:
  - `def create_tabbed_sidebar`: 创建多标签页侧边栏的便捷函数

---

### 📄 src/ui/unified_config_components.py
**📝 描述**: 统一配置组件

- **🏗️ Classes**:
  - `class UnifiedConfigRenderer`: 统一配置渲染器
- **⚡ Functions**:
  - `def render_basic_config`: 渲染基础配置 - 便捷函数
  - `def render_embedding_config`: 渲染嵌入配置 - 便捷函数
  - `def render_config_tab`: 渲染配置标签页 - 便捷函数

---

### 📄 src/ui/unified_dialogs.py
**📝 描述**: 统一UI组件 - 第一步

- **⚡ Functions**:
  - `def show_document_detail_dialog`: 显示文档详情对话框 - 统一版本

---

### 📄 src/ui/unified_display_components.py
**📝 描述**: 统一显示组件

- **🏗️ Classes**:
  - `class UnifiedDisplayRenderer`: 统一显示渲染器
- **⚡ Functions**:
  - `def render_system_stats`: 渲染系统状态 - 便捷函数
  - `def render_file_list`: 渲染文件列表 - 便捷函数
  - `def render_progress_panel`: 渲染进度面板 - 便捷函数

---

### 📄 src/ui/user_experience_enhanced.py
**📝 描述**: 增强的用户体验组件

- **🏗️ Classes**:
  - `class UserExperienceEnhancer`: 用户体验增强器

---

### 📄 src/ui/user_profile_ui.py
- **🏗️ Classes**:
  - `class UserProfileUI`: [v8.7.0] 统一用户中心 UI

---

### 📄 src/ui/web_to_kb_interface.py
**📝 描述**: 网页抓取到知识库的UI界面组件

- **🏗️ Classes**:
  - `class WebToKBInterface`: 网页抓取到知识库的UI界面

---

### 📄 src/monitor/__init__.py
**📝 描述**: 系统监控模块


---

### 📄 src/core/__init__.py
**📝 描述**: Core模块 - 多进程安全版本

- **⚡ Functions**:
  - `def get_state_manager`: 获取状态管理器
  - `def get_main_controller`: 获取主控制器

---

### 📄 src/core/app_config.py
**📝 描述**: 应用配置模块

- **⚡ Functions**:
  - `def load_config`: 加载配置文件 - 使用统一服务
  - `def save_config`: 保存配置文件 - 使用统一服务
  - `def get_existing_kbs`: 获取现有知识库列表

---

### 📄 src/core/environment.py
**📝 描述**: 环境配置模块

- **⚡ Functions**:
  - `def setup_environment`: 设置环境配置
  - `def suppress_warnings`: 屏蔽所有警告和日志
  - `def apply_compatibility_patches`: 应用兼容性补丁
  - `def initialize_environment`: 初始化完整环境

---

### 📄 src/core/state_manager.py
**📝 描述**: 状态管理器 - 多进程安全版本

- **🏗️ Classes**:
  - `class StateManager`: 多进程安全的状态管理器

---

### 📄 src/core/v23_integration.py
**📝 描述**: v2.3.0 功能集成模块

- **🏗️ Classes**:
  - `class V23Integration`: 无描述
- **⚡ Functions**:
  - `def get_v23_integration`: 获取v2.3.0集成实例

---

### 📄 src/core/version.py
**📝 描述**: 统一版本管理模块

- **⚡ Functions**:
  - `def get_version_info`: 获取版本信息
  - `def get_version`: 获取版本号
  - `def get_version_tag`: 获取版本标签
  - `def get_codename`: 获取版本代号
  - `def get_release_date`: 获取发布日期

---

### 📄 src/kb/__init__.py
**📝 描述**: 知识库管理模块


---

### 📄 src/kb/document_viewer.py
- **🏗️ Classes**:
  - `class DocumentInfo`: 文档信息
  - `class DocumentViewer`: 文档查看器

---

### 📄 src/kb/incremental_updater.py
**📝 描述**: 增量更新管理器 - 支持文档增量添加，无需重建整个知识库

- **🏗️ Classes**:
  - `class IncrementalUpdater`: 增量更新管理器

---

### 📄 src/kb/kb_interface.py
**📝 描述**: 知识库界面 - 负责知识库相关的所有UI逻辑

- **🏗️ Classes**:
  - `class KBInterface`: 知识库界面管理器

---

### 📄 src/kb/kb_loader.py
**📝 描述**: 知识库加载器模块

- **🏗️ Classes**:
  - `class KnowledgeBaseLoader`: 知识库加载器

---

### 📄 src/kb/kb_manager.py
**📝 描述**: 知识库管理器 - 高级管理功能

- **🏗️ Classes**:
  - `class KBManager`: 知识库管理器 - 提供高级管理功能

---

### 📄 src/kb/kb_operations.py
- **🏗️ Classes**:
  - `class KBOperations`: 知识库基础操作类

---

### 📄 src/kb/kb_processor.py
**📝 描述**: 知识库处理器 - 负责知识库的创建和处理逻辑

- **🏗️ Classes**:
  - `class KBProcessor`: 知识库处理器

---

### 📄 src/chat/__init__.py
**📝 描述**: 聊天模块


---

### 📄 src/chat/chat_engine.py
**📝 描述**: 聊天引擎

- **🏗️ Classes**:
  - `class ChatEngine`: 聊天引擎 - 处理问答流程

---

### 📄 src/chat/chat_interface.py
**📝 描述**: 聊天界面 - 负责聊天相关的所有UI逻辑

- **🏗️ Classes**:
  - `class ChatInterface`: 聊天界面管理器

---

### 📄 src/chat/history_manager.py
**📝 描述**: 聊天历史管理器

- **🏗️ Classes**:
  - `class HistoryManager`: 聊天历史管理器

---

### 📄 src/chat/share_manager.py
**📝 描述**: 分享管理器 - 负责会话的快照生成与持久化分享

- **🏗️ Classes**:
  - `class ShareManager`: 无描述

---

### 📄 src/chat/suggestion_manager.py
**📝 描述**: 追问建议管理器 - 统一推荐引擎适配器

- **🏗️ Classes**:
  - `class SuggestionManager`: 追问建议管理器 - 统一推荐引擎的适配器

---

### 📄 src/chat/unified_suggestion_engine.py
**📝 描述**: 统一推荐问题生成引擎

- **🏗️ Classes**:
  - `class UnifiedSuggestionEngine`: 统一推荐问题生成引擎
- **⚡ Functions**:
  - `def get_unified_suggestion_engine`: 获取统一推荐引擎实例

---

### 📄 src/config/__init__.py
**📝 描述**: 配置管理模块


---

### 📄 src/config/config_interface.py
**📝 描述**: 配置界面管理器 - 负责配置相关的UI逻辑

- **🏗️ Classes**:
  - `class ConfigInterface`: 配置界面管理器

---

### 📄 src/config/config_loader.py
**📝 描述**: 配置加载器 - 适配 UnifiedConfigService

- **🏗️ Classes**:
  - `class ConfigLoader`: 配置加载器

---

### 📄 src/config/config_validator.py
**📝 描述**: 配置验证器 - 最小实现

- **🏗️ Classes**:
  - `class ConfigValidator`: 配置验证器

---

### 📄 src/config/manifest_manager.py
- **🏗️ Classes**:
  - `class ManifestManager`: 清单管理器

---

### 📄 src/config/prompt_manager.py
**📝 描述**: 系统提示词管理器

- **🏗️ Classes**:
  - `class PromptManager`: 提示词管理器类

---

### 📄 src/config/unified_sites.py
**📝 描述**: 统一网站配置管理

- **⚡ Functions**:
  - `def get_industry_list`: 获取所有行业的显示列表
  - `def get_industry_sites`: 根据显示名称获取行业网站
  - `def get_easy_sites`: 获取指定行业中容易爬取的网站

---

### 📄 src/auth/audit_logger.py
- **🏗️ Classes**:
  - `class AuditLogger`: 无描述

---

### 📄 src/auth/connection_manager.py
- **🏗️ Classes**:
  - `class ConnectionManager`: [v8.3.0] 数据库连接管理器

---

### 📄 src/auth/login_page.py
- **⚡ Functions**:
  - `def render_login_page`: 无描述

---

### 📄 src/auth/permission_manager.py
- **🏗️ Classes**:
  - `class PermissionManager`: 无描述

---

### 📄 src/auth/resource_governance.py
- **⚡ Functions**:
  - `def render_resource_governance_v19`: 无描述
  - `def format_size`: 无描述
  - `def get_client_ip`: 无描述

---

### 📄 src/auth/session_manager.py
- **⚡ Functions**:
  - `def load_session_store`: 无描述
  - `def save_session_store`: 无描述
  - `def create_session`: 创建新会话，返回 Token
  - `def validate_session`: 验证 Token 有效性
  - `def revoke_user_sessions`: 注销用户所有会话
  - `def get_session_settings`: 获取会话配置
  - `def set_session_setting`: 设置会话时长
  - `def _cleanup_expired_sessions`: 清理过期会话
  - `def load_sharing_config`: 加载知识库共享配置
  - `def save_sharing_config`: 保存知识库共享配置
  - `def set_kb_public`: 设置知识库是否公开
  - `def get_visible_kbs`: 根据权限过滤可见的知识库
  - `def get_user_storage_usage`: 计算用户名下所有知识库的总物理占用 (Bytes)
  - `def format_size`: 格式化字节数为人类可读格式

---

### 📄 src/auth/user_auth.py
- **⚡ Functions**:
  - `def hash_password`: 无描述
  - `def load_users`: 无描述
  - `def _init_admin`: 初始化默认管理员
  - `def save_users`: 无描述
  - `def register_user`: 无描述
  - `def authenticate_user`: 无描述

---

### 📄 src/utils/__init__.py
**📝 描述**: RAG Pro Max - 工具模块


---

### 📄 src/utils/adaptive_scheduler.py
- **🏗️ Classes**:
  - `class PerformanceRecord`: 性能记录
  - `class AdaptiveScheduler`: 自适应CPU调度器

---

### 📄 src/utils/adaptive_throttling.py
**📝 描述**: 自适应限流管理器 - Adaptive Throttling Manager

- **🏗️ Classes**:
  - `class AdaptiveThrottling`: 自适应限流管理器
  - `class DynamicWorkerAdjuster`: 动态工作线程调整器
  - `class ResourceGuard`: 资源保护器 - 综合管理限流和工作线程
- **⚡ Functions**:
  - `def get_resource_guard`: 获取全局资源保护器

---

### 📄 src/utils/aggressive_ocr_config.py
- **⚡ Functions**:
  - `def get_aggressive_ocr_workers`: 无描述
  - `def force_ocr_all_pdfs`: 无描述

---

### 📄 src/utils/alert_system.py
**📝 描述**: 智能告警系统

- **🏗️ Classes**:
  - `class AlertSystem`: 无描述
- **⚡ Functions**:
  - `def get_alert_system`: 获取告警系统实例

---

### 📄 src/utils/app_utils.py
**📝 描述**: 应用工具函数模块

- **⚡ Functions**:
  - `def get_kb_embedding_dim`: 检测知识库的向量维度
  - `def remove_file_from_manifest`: 从 manifest 中移除文件
  - `def initialize_session_state`: 初始化 session state
  - `def show_first_time_guide`: 显示首次使用引导
  - `def open_file_native`: 使用系统默认程序打开文件 (macOS 原生预览)
  - `def handle_kb_switching`: 处理知识库切换逻辑

---

### 📄 src/utils/async_pipeline.py
**📝 描述**: 异步向量化管道 - Async Vectorization Pipeline

- **🏗️ Classes**:
  - `class AsyncPipeline`: 异步处理管道
- **⚡ Functions**:
  - `def run_async_pipeline`: 运行异步管道的便捷函数

---

### 📄 src/utils/batch_ocr_processor.py
- **🏗️ Classes**:
  - `class BatchOCRProcessor`: 批量OCR处理器
- **⚡ Functions**:
  - `def _batch_ocr_page`: 批量OCR单页处理（模块级函数）

---

### 📄 src/utils/batch_operations.py
**📝 描述**: 批量操作工具 - 文件夹拖拽和批量管理

- **🏗️ Classes**:
  - `class BatchOperations`: 无描述

---

### 📄 src/utils/compact_log_display.py
**📝 描述**: 紧凑日志显示组件

- **🏗️ Classes**:
  - `class CompactLogDisplay`: 紧凑日志显示器
- **⚡ Functions**:
  - `def render_compact_log_management`: 渲染紧凑的日志管理界面
  - `def _clear_all_logs`: 清空所有日志
  - `def _package_all_logs`: 打包所有日志

---

### 📄 src/utils/concurrency_manager.py
**📝 描述**: 并发优化管理器 - Concurrency Optimization Manager

- **🏗️ Classes**:
  - `class ConcurrencyManager`: 并发优化管理器
- **⚡ Functions**:
  - `def get_concurrency_manager`: 获取全局并发管理器
  - `def cleanup_concurrency_manager`: 清理全局管理器

---

### 📄 src/utils/concurrency_monitor.py
**📝 描述**: 并发性能监控

- **🏗️ Classes**:
  - `class TaskMetrics`: 任务性能指标
  - `class ConcurrencyMonitor`: 并发性能监控器
- **⚡ Functions**:
  - `def get_monitor`: 获取全局并发监控器

---

### 📄 src/utils/cpu_monitor.py
**📝 描述**: CPU使用率监控和限制工具

- **🏗️ Classes**:
  - `class CPUMonitor`: CPU使用率监控器
  - `class ResourceLimiter`: 资源限制器
- **⚡ Functions**:
  - `def get_resource_limiter`: 获取资源限制器实例
  - `def check_system_resources`: 检查系统资源状态
  - `def get_safe_worker_count`: 获取安全的工作线程数

---

### 📄 src/utils/cpu_throttle.py
- **🏗️ Classes**:
  - `class CPUThrottle`: CPU 使用率限制器
  - `class SafeThreadPoolExecutor`: 带 CPU 限制的线程池执行器
- **⚡ Functions**:
  - `def safe_parallel_execute`: 安全的并行执行函数，带 CPU 使用率限制
  - `def start_global_cpu_protection`: 启动全局 CPU 保护
  - `def stop_global_cpu_protection`: 停止全局 CPU 保护
  - `def is_cpu_throttling`: 检查是否正在限流
  - `def wait_for_cpu_available`: 等待 CPU 可用

---

### 📄 src/utils/doc_search.py
- **⚡ Functions**:
  - `def search_docs`: 搜索项目根目录下的 Markdown 文档内容

---

### 📄 src/utils/document_processor.py
- **⚡ Functions**:
  - `def get_file_size_str`: 将字节数转换为可读的文件大小字符串
  - `def get_file_type`: 根据文件扩展名返回文件类型和图标
  - `def load_pptx_file`: 加载 PPTX 文件
  - `def get_file_info`: 获取文件的基本信息和元数据
  - `def get_relevance_label`: 根据相关性分数返回标签

---

### 📄 src/utils/document_quality_assessor.py
**📝 描述**: 文档质量评估器

- **🏗️ Classes**:
  - `class DocumentQualityAssessor`: 文档质量评估器
- **⚡ Functions**:
  - `def show_quality_assessment`: 显示文档质量评估结果

---

### 📄 src/utils/dynamic_batch.py
**📝 描述**: 动态批量优化 - Dynamic Batch Optimization

- **🏗️ Classes**:
  - `class DynamicBatchOptimizer`: 动态批量优化器

---

### 📄 src/utils/enhanced_cache.py
**📝 描述**: 增强查询缓存系统 - 纯内存版本

- **🏗️ Classes**:
  - `class EnhancedQueryCache`: 增强查询缓存系统
  - `class SmartCacheManager`: 智能缓存管理器

---

### 📄 src/utils/enhanced_logger.py
- **🏗️ Classes**:
  - `class EnhancedLogger`: 无描述
- **⚡ Functions**:
  - `def demo_usage`: 演示用法

---

### 📄 src/utils/enhanced_ocr_optimizer.py
- **🏗️ Classes**:
  - `class EnhancedOCROptimizer`: 增强OCR优化器
- **⚡ Functions**:
  - `def _process_single_image_global`: 处理单张图片 - 全局函数用于多进程

---

### 📄 src/utils/error_handler_enhanced.py
**📝 描述**: 增强的错误处理机制

- **🏗️ Classes**:
  - `class ErrorHandler`: 全局错误处理器

---

### 📄 src/utils/export_manager.py
**📝 描述**: 导出管理器 - 对话记录和数据导出

- **🏗️ Classes**:
  - `class ExportManager`: 无描述

---

### 📄 src/utils/file_system_utils.py
- **🏗️ Classes**:
  - `class NotesManager`: 管理文件的持久化备注
- **⚡ Functions**:
  - `def get_deep_file_attributes`: 获取工业级深度文件属性(增加取证与RAG指标)
  - `def reveal_in_file_manager`: 在文件管理器中定位并显示文件
  - `def set_where_from_metadata`: 为文件设置 '下载来源' 元数据 (仅限 macOS)

---

### 📄 src/utils/file_upload_handler.py
- **⚡ Functions**:
  - `def process_uploaded_file_content`: 处理 Streamlit 上传的文件，复用 src/file_processor.py 的核心逻辑。

---

### 📄 src/utils/friendly_error_handler.py
**📝 描述**: 改进的用户友好错误处理器

- **🏗️ Classes**:
  - `class FriendlyErrorHandler`: 友好的错误处理器
- **⚡ Functions**:
  - `def friendly_error`: 便捷的友好错误显示函数
  - `def validation_error`: 便捷的验证错误显示函数
  - `def operation_failed`: 便捷的操作失败显示函数

---

### 📄 src/utils/gpu_ocr_accelerator.py
**📝 描述**: GPU OCR加速器

- **🏗️ Classes**:
  - `class GPUOCRAccelerator`: GPU OCR加速器

---

### 📄 src/utils/gpu_optimizer.py
**📝 描述**: GPU利用率优化模块

- **🏗️ Classes**:
  - `class GPUOptimizer`: GPU利用率优化器

---

### 📄 src/utils/html_to_markdown.py
**📝 描述**: HTML 转 Markdown 工具

- **🏗️ Classes**:
  - `class HtmlToMarkdown`: 无描述

---

### 📄 src/utils/kb_name_optimizer.py
**📝 描述**: 知识库名称优化器 - 避免重复名称和时间戳冲突

- **🏗️ Classes**:
  - `class KBNameOptimizer`: 知识库名称优化器

---

### 📄 src/utils/kb_utils.py
**📝 描述**: 知识库工具函数 - 从主文件中提取的工具函数

- **⚡ Functions**:
  - `def generate_smart_kb_name`: 智能生成知识库名称 - 使用优化器确保唯一性

---

### 📄 src/utils/local_refresh_monitor.py
**📝 描述**: 局部刷新监控仪表板

- **🏗️ Classes**:
  - `class LocalRefreshMonitor`: 局部刷新监控器
- **⚡ Functions**:
  - `def show_local_monitor`: 显示局部监控 - 不影响其他区域
  - `def show_monitor_widget`: 显示监控小部件

---

### 📄 src/utils/log_analyzer.py
- **🏗️ Classes**:
  - `class LogAnalyzer`: 无描述
- **⚡ Functions**:
  - `def analyze_current_log`: 分析当前日志

---

### 📄 src/utils/memory.py
**📝 描述**: 内存和显存管理模块 - 使用公共函数


---

### 📄 src/utils/memory_manager_enhanced.py
**📝 描述**: 增强的内存管理器

- **🏗️ Classes**:
  - `class MemoryManager`: 增强的内存管理器

---

### 📄 src/utils/memory_optimizer.py
- **🏗️ Classes**:
  - `class MemoryOptimizer`: 无描述

---

### 📄 src/utils/model_manager.py
**📝 描述**: 模型管理模块 - 统一管理嵌入模型和 LLM 模型的加载

- **⚡ Functions**:
  - `def clean_proxy`: 清理代理设置，避免本地服务连接问题
  - `def load_embedding_model`: 加载嵌入模型
  - `def load_llm_model`: 加载 LLM 模型
  - `def set_global_embedding_model`: 设置全局嵌入模型（Settings.embed_model）
  - `def set_global_llm_model`: 设置全局 LLM 模型（Settings.llm）

---

### 📄 src/utils/model_utils.py
- **⚡ Functions**:
  - `def check_ollama_status`: 检查 Ollama 服务状态
  - `def fetch_remote_models`: 获取远程模型列表 (OpenAI 兼容接口)
  - `def fetch_ollama_models`: 获取 Ollama 模型列表
  - `def check_hf_model_exists`: 检查 HuggingFace 模型是否已下载到本地
  - `def get_kb_embedding_dim`: 检测知识库的向量维度（带缓存）
  - `def auto_switch_model`: 根据知识库维度自动切换模型
  - `def get_model_dimension`: 获取模型的向量维度

---

### 📄 src/utils/ocr_optimizer.py
- **🏗️ Classes**:
  - `class OCROptimizer`: OCR性能优化器 - 带CPU保护

---

### 📄 src/utils/offline_embeddings.py
- **🏗️ Classes**:
  - `class OfflineEmbeddings`: 离线嵌入模型
- **⚡ Functions**:
  - `def get_offline_embeddings`: 获取离线嵌入模型实例

---

### 📄 src/utils/offline_query_engine.py
- **🏗️ Classes**:
  - `class OfflineQueryEngine`: 离线查询引擎 - 仅文档检索
- **⚡ Functions**:
  - `def create_offline_query_engine_wrapper`: 无描述

---

### 📄 src/utils/optimized_ocr_processor.py
**📝 描述**: 优化OCR处理器 - 解决重复加载模型问题

- **🏗️ Classes**:
  - `class OptimizedOCRProcessor`: 优化的OCR处理器 - 单例模式
- **⚡ Functions**:
  - `def get_ocr_processor`: 获取OCR处理器实例
  - `def process_images_optimized`: 优化的图片处理接口

---

### 📄 src/utils/parallel_executor.py
- **🏗️ Classes**:
  - `class ParallelExecutor`: 统一的并行执行管理器 - 带CPU使用率限制
- **⚡ Functions**:
  - `def get_global_executor`: 获取全局并行执行器（单例模式）
  - `def auto_parallel`: 自动并行装饰器
  - `def parallelize_list`: 便捷函数：对列表中的每个元素应用函数（自动并行）

---

### 📄 src/utils/parallel_ocr_processor.py
- **🏗️ Classes**:
  - `class ParallelOCRProcessor`: 并行OCR处理器
- **⚡ Functions**:
  - `def _get_ocr_instance`: 获取全局OCR实例，只初始化一次
  - `def _ocr_worker_process`: OCR工作进程 - 必须在模块级别定义

---

### 📄 src/utils/parallel_tasks.py
**📝 描述**: 并行任务函数

- **⚡ Functions**:
  - `def extract_metadata_task`: 单个文件的元数据提取任务（多进程安全）
  - `def process_node_worker`: 多进程处理单个节点（问答场景）

---

### 📄 src/utils/pdf_page_reader.py
**📝 描述**: PDF页码读取器 - 支持记录页码信息的PDF处理

- **🏗️ Classes**:
  - `class PDFPageReader`: 支持页码记录的PDF读取器
- **⚡ Functions**:
  - `def read_pdf_with_pages`: 便捷函数：读取PDF并返回包含页码信息的文档列表

---

### 📄 src/utils/performance_monitor.py
- **🏗️ Classes**:
  - `class PerformanceMonitor`: 无描述

---

### 📄 src/utils/query_cache.py
**📝 描述**: 查询缓存模块 - LRU Cache

- **🏗️ Classes**:
  - `class QueryCache`: 查询缓存管理器
- **⚡ Functions**:
  - `def get_cache`: 获取全局缓存

---

### 📄 src/utils/realtime_monitor.py
**📝 描述**: 实时监控组件

- **🏗️ Classes**:
  - `class RealtimeMonitor`: 实时监控器
- **⚡ Functions**:
  - `def render_realtime_monitoring`: 渲染实时监控界面
  - `def render_mini_monitoring`: 渲染迷你监控

---

### 📄 src/utils/resource_monitor.py
**📝 描述**: 资源监控工具

- **⚡ Functions**:
  - `def check_resource_usage`: 检查系统资源使用率
  - `def get_system_stats`: 获取系统统计信息
  - `def should_throttle`: 判断是否需要限流

---

### 📄 src/utils/safe_parallel_tasks.py
**📝 描述**: 多进程安全的工作函数

- **⚡ Functions**:
  - `def safe_process_node_worker`: 多进程安全的节点处理函数
  - `def extract_metadata_task`: 多进程安全的元数据提取函数

---

### 📄 src/utils/search_engine.py
**📝 描述**: 搜索引擎 - 全文搜索和智能过滤

- **🏗️ Classes**:
  - `class SearchEngine`: 无描述

---

### 📄 src/utils/search_quality.py
**📝 描述**: 搜索结果质量评估模块

- **🏗️ Classes**:
  - `class SearchQualityAnalyzer`: 搜索结果质量分析器

---

### 📄 src/utils/smart_scheduler.py
**📝 描述**: 智能资源调度器

- **🏗️ Classes**:
  - `class TaskType`: 任务类型枚举
  - `class SmartScheduler`: 无描述
- **⚡ Functions**:
  - `def get_smart_scheduler`: 获取智能调度器实例

---

### 📄 src/utils/task_scheduler.py
**📝 描述**: 智能任务调度器

- **🏗️ Classes**:
  - `class ResourceStatus`: 系统资源状态
  - `class TaskScheduler`: 智能任务调度器
- **⚡ Functions**:
  - `def get_scheduler`: 获取全局任务调度器

---

### 📄 src/utils/terminal_progress.py
- **🏗️ Classes**:
  - `class TerminalProgress`: 无描述

---

### 📄 src/utils/user_guidance.py
**📝 描述**: 用户引导组件

- **🏗️ Classes**:
  - `class UserGuidance`: 用户引导助手
- **⚡ Functions**:
  - `def show_guidance`: 显示指定类型的用户引导
  - `def contextual_help`: 显示上下文相关帮助

---

### 📄 src/utils/vectorization_wrapper.py
- **🏗️ Classes**:
  - `class VectorizationWrapper`: 向量化包装器 - 集成动态批量优化

---

### 📄 src/document/__init__.py
**📝 描述**: 文档管理模块


---

### 📄 src/document/document_manager_ui.py
**📝 描述**: 文档管理界面 - 负责文档相关的UI逻辑

- **🏗️ Classes**:
  - `class DocumentManagerUI`: 文档管理界面

---

### 📄 src/processors/__init__.py
**📝 描述**: 文档处理器模块


---

### 📄 src/processors/async_web_crawler.py
- **🏗️ Classes**:
  - `class AsyncWebCrawler`: 无描述

---

### 📄 src/processors/concurrent_crawler.py
- **🏗️ Classes**:
  - `class ConcurrentCrawler`: 并发爬取管理器 - 支持多进程和多线程
- **⚡ Functions**:
  - `def fetch_url_worker`: 多进程工作函数

---

### 📄 src/processors/content_analyzer.py
- **🏗️ Classes**:
  - `class ContentQualityAnalyzer`: 内容质量分析器

---

### 📄 src/processors/crawl_optimizer.py
- **🏗️ Classes**:
  - `class CrawlOptimizer`: 智能爬取优化器

---

### 📄 src/processors/crawl_stats_manager.py
- **🏗️ Classes**:
  - `class CrawlStatsManager`: 爬取统计管理器

---

### 📄 src/processors/data_analyst.py
- **🏗️ Classes**:
  - `class DataAnalystEngine`: 无描述

---

### 📄 src/processors/db_ingestor.py
- **🏗️ Classes**:
  - `class DBIngestor`: [v8.3.0] 数据库摄入器

---

### 📄 src/processors/document_parser.py
**📝 描述**: 文档解析器

- **🏗️ Classes**:
  - `class DocumentParser`: 文档解析器
- **⚡ Functions**:
  - `def get_document_parser`: 获取文档解析器实例
  - `def _parse_single_doc`: 兼容性函数
  - `def _parse_batch_docs`: 兼容性函数

---

### 📄 src/processors/enhanced_web_crawler.py
**📝 描述**: 增强版网页爬虫 - 集成异步并发和原有功能

- **🏗️ Classes**:
  - `class EnhancedWebCrawler`: 无描述
- **⚡ Functions**:
  - `def create_crawler`: 创建爬虫实例
  - `def run_async_crawl`: 在同步环境中运行异步爬虫

---

### 📄 src/processors/index_builder.py
**📝 描述**: 索引构建器

- **🏗️ Classes**:
  - `class BuildResult`: 构建结果
  - `class IndexBuilder`: 索引构建器
- **⚡ Functions**:
  - `def _extract_metadata_task`: 元数据提取任务（多进程安全）

---

### 📄 src/processors/multimodal_processor.py
**📝 描述**: 多模态处理器 - 支持图片、表格等多模态内容处理

- **🏗️ Classes**:
  - `class MultimodalProcessor`: 多模态处理器

---

### 📄 src/processors/schema_enhancer.py
- **🏗️ Classes**:
  - `class SchemaEnhancer`: [v8.2.0] Schema 增强引擎

---

### 📄 src/processors/summary_generator.py
**📝 描述**: 摘要生成器

- **🏗️ Classes**:
  - `class SummaryGenerator`: 摘要生成器
- **⚡ Functions**:
  - `def get_summary_generator`: 获取摘要生成器实例
  - `def generate_doc_summary`: 兼容性函数

---

### 📄 src/processors/unified_document_processor.py
**📝 描述**: 统一文档处理组件

- **🏗️ Classes**:
  - `class UnifiedDocumentProcessor`: 统一文档处理器
- **⚡ Functions**:
  - `def render_upload_interface`: 渲染文档上传界面 - 便捷函数
  - `def process_uploaded_files`: 处理上传文件 - 便捷函数
  - `def show_file_preview`: 显示文件预览 - 便捷函数

---

### 📄 src/processors/upload_handler.py
**📝 描述**: 文档上传处理器

- **🏗️ Classes**:
  - `class UploadResult`: 上传结果
  - `class UploadHandler`: 文档上传处理器

---

### 📄 src/processors/web_crawler.py
- **🏗️ Classes**:
  - `class WebCrawler`: 无描述

---

### 📄 src/processors/web_to_kb_processor.py
**📝 描述**: 网页抓取到知识库构建的完整流程处理器

- **🏗️ Classes**:
  - `class WebToKBProcessor`: 网页抓取到知识库构建的完整流程处理器

---

### 📄 src/common/__init__.py
**📝 描述**: 公共模块 - 合并重复函数


---

### 📄 src/common/business.py
**📝 描述**: 公共业务逻辑 - 合并重复的核心业务函数

- **⚡ Functions**:
  - `def update_status`: 统一的状态更新函数
  - `def generate_smart_kb_name`: 统一的智能知识库命名函数
  - `def process_knowledge_base_logic`: 统一的知识库处理逻辑
  - `def status_callback_factory`: 状态回调函数工厂
  - `def export_chat_history`: 统一的对话历史导出函数
  - `def generate_doc_summary`: 统一的文档摘要生成函数
  - `def click_btn`: 点击追问按钮，将问题加入队列（去重）

---

### 📄 src/common/config.py
**📝 描述**: 公共配置管理 - 合并重复的配置函数

- **⚡ Functions**:
  - `def load_config`: 统一的配置加载函数 - 使用统一服务
  - `def save_config`: 统一的配置保存函数 - 使用统一服务
  - `def get_default_config`: 获取默认配置
  - `def get_config_value`: 获取配置值 - 使用统一服务
  - `def set_config_value`: 设置配置值 - 使用统一服务

---

### 📄 src/common/utils.py
**📝 描述**: 公共工具函数 - 合并重复的基础工具函数

- **⚡ Functions**:
  - `def cleanup_memory`: 统一的内存清理函数
  - `def sanitize_filename`: 统一的文件名清理函数
  - `def format_bytes`: 统一的字节格式化函数
  - `def get_memory_stats`: 统一的内存统计函数
  - `def cleanup_temp_files`: 统一的临时文件清理函数
  - `def get_file_stats`: 统一的文件统计函数
  - `def get_client_ip`: 获取客户端真实IP
  - `def save_uploaded_files`: 保存上传的文件到临时目录并返回目录路径

---

### 📄 src/engines/__init__.py
**📝 描述**: 双引擎系统 - RAG + SQL


---

### 📄 src/engines/sql_engine.py
**📝 描述**: Text-to-SQL 引擎 - 最小实现

- **🏗️ Classes**:
  - `class SQLEngine`: 无描述

---

### 📄 src/app_logging/__init__.py
**📝 描述**: 统一日志模块


---

### 📄 src/app_logging/log_manager.py
**📝 描述**: 统一日志管理器 - 整合文件日志和终端日志

- **🏗️ Classes**:
  - `class LogManager`: 统一日志管理器 - 替代 terminal_logger
- **⚡ Functions**:
  - `def get_logger`: 获取全局日志管理器
  - `def set_logger`: 设置全局日志管理器

---

### 📄 src/app_logging/progress_logger.py
- **🏗️ Classes**:
  - `class ProgressLogger`: 无描述

---

### 📄 src/queue/queue_manager.py
**📝 描述**: 队列管理器模块

- **🏗️ Classes**:
  - `class QueueManager`: 队列管理器

---

### 📄 src/api/fastapi_server.py
**📝 描述**: FastAPI服务器

- **🏗️ Classes**:
  - `class QueryRequest`: 无描述
  - `class QueryResponse`: 无描述
  - `class KnowledgeBaseInfo`: 无描述
  - `class IncrementalUpdateRequest`: 无描述
  - `class IncrementalUpdateResponse`: 无描述
  - `class MultimodalQueryRequest`: 无描述
- **⚡ Functions**:
  - `def start_api_server`: 启动API服务器

---

### 📄 src/documents/document_manager.py
**📝 描述**: 文档管理器模块

- **🏗️ Classes**:
  - `class DocumentManager`: 文档管理器

---

### 📄 src/query/multi_kb_query_engine.py
**📝 描述**: 多知识库联合问答系统 - 多进程优化版

- **🏗️ Classes**:
  - `class MultiKBQueryEngine`: 多知识库联合查询引擎 - 多进程优化版
  - `class MultiKBInterface`: 多知识库问答界面
- **⚡ Functions**:
  - `def query_single_kb_worker`: 单个知识库查询工作函数 - 用于多进程
  - `def render_multi_kb_query`: 渲染多知识库查询界面 - 便捷函数

---

### 📄 src/query/query_handler.py
**📝 描述**: 查询处理器

- **🏗️ Classes**:
  - `class QueryHandler`: 查询处理器

---

### 📄 src/query/query_processor.py
**📝 描述**: 查询处理器模块

- **🏗️ Classes**:
  - `class QueryProcessor`: 查询处理器
- **⚡ Functions**:
  - `def process_node_worker`: 处理单个节点的工作函数

---

### 📄 src/query/query_rewriter.py
**📝 描述**: 查询改写器模块

- **🏗️ Classes**:
  - `class QueryRewriter`: 查询改写器

---

### 📄 src/services/__init__.py
**📝 描述**: 服务模块 - 核心业务逻辑服务


---

### 📄 src/services/config_service.py
- **🏗️ Classes**:
  - `class ConfigService`: 统一的配置管理服务
- **⚡ Functions**:
  - `def get_config_service`: 获取配置服务实例

---

### 📄 src/services/configurable_industry_service.py
- **🏗️ Classes**:
  - `class ConfigurableIndustryService`: 可配置的行业网站服务
- **⚡ Functions**:
  - `def get_configurable_industry_service`: 获取可配置行业服务实例

---

### 📄 src/services/file_service.py
- **🏗️ Classes**:
  - `class FileService`: 无描述
- **⚡ Functions**:
  - `def get_file_service`: 无描述

---

### 📄 src/services/knowledge_base_service.py
- **🏗️ Classes**:
  - `class KnowledgeBaseService`: 无描述
- **⚡ Functions**:
  - `def get_knowledge_base_service`: 无描述

---

### 📄 src/services/unified_config_service.py
- **🏗️ Classes**:
  - `class UnifiedConfigService`: 统一配置服务
- **⚡ Functions**:
  - `def save_config`: 保存配置 - 便捷函数
  - `def load_config`: 加载配置 - 便捷函数
  - `def get_config_value`: 获取配置值 - 便捷函数
  - `def set_config_value`: 设置配置值 - 便捷函数

---

### 📄 src/summary/auto_summary.py
**📝 描述**: 自动摘要模块

- **🏗️ Classes**:
  - `class AutoSummaryGenerator`: 自动摘要生成器

---

### 📄 src/upload/__init__.py
**📝 描述**: 文件上传模块


---

### 📄 src/upload/upload_interface.py
**📝 描述**: 文件上传界面管理器 - 负责文件上传相关的UI逻辑

- **🏗️ Classes**:
  - `class UploadInterface`: 文件上传界面管理器

---

