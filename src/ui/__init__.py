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
    'render_hf_embedding_selector'
]
