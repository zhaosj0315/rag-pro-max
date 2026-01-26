"""
知识库工具函数 - 已废弃，请使用 KBNameOptimizer.smart_generate
"""

import os
import warnings


def generate_smart_kb_name(target_path, cnt, file_types, folder_name):
    """
    已废弃的函数 - 请使用 KBNameOptimizer.smart_generate
    为了向后兼容暂时保留，但会发出警告
    """
    warnings.warn(
        "generate_smart_kb_name 已废弃，请使用 KBNameOptimizer.smart_generate",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 重定向到新的统一方法
    from src.utils.kb_name_optimizer import KBNameOptimizer
    return KBNameOptimizer.smart_generate(target_path, "file", "")
