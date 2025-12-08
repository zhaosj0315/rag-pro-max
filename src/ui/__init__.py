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

__all__ = [
    'render_message_stats',
    'render_source_references',
    'get_relevance_label',
    'format_time_duration',
    'format_token_count'
]
