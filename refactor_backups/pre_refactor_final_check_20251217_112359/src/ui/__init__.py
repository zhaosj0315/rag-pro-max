"""
UI 组件模块
纯展示组件，不修改应用状态
"""

from .display_components import (
    render_message_stats,
    render_source_references,
    get_relevance_label,
    format_time_duration,
    format_token_count
)

from .model_selectors import (
    render_ollama_model_selector,
    render_openai_model_selector,
    render_hf_embedding_selector
)

from .advanced_config import (
    render_rerank_config,
    render_bm25_config,
    render_advanced_features
)

from .config_forms import (
    render_llm_config,
    render_embedding_config,
    render_basic_config
)

__all__ = [
    # Display components
    'render_message_stats',
    'render_source_references',
    'get_relevance_label',
    'format_time_duration',
    'format_token_count',
    # Model selectors
    'render_ollama_model_selector',
    'render_openai_model_selector',
    'render_hf_embedding_selector',
    # Advanced config
    'render_rerank_config',
    'render_bm25_config',
    'render_advanced_features',
    # Config forms
    'render_llm_config',
    'render_embedding_config',
    'render_basic_config'
]
