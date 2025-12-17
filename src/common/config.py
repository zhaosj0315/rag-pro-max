#!/usr/bin/env python3
"""
公共配置管理 - 合并重复的配置函数
"""

import json
import os
from typing import Dict, Any, Optional

DEFAULT_CONFIG_DIR = "config"
DEFAULT_CONFIG_FILE = "app_config.json"

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """统一的配置加载函数"""
    if config_file is None:
        config_file = os.path.join(DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE)
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 返回默认配置
            return get_default_config()
    except Exception:
        return get_default_config()

def save_config(config: Dict[str, Any], config_file: Optional[str] = None) -> bool:
    """统一的配置保存函数"""
    if config_file is None:
        config_file = os.path.join(DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE)
    
    try:
        # 确保配置目录存在
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "llm": {
            "provider": "OpenAI",
            "model": "gpt-3.5-turbo",
            "api_base": "https://api.openai.com/v1",
            "api_key": "",
            "temperature": 0.7
        },
        "embedding": {
            "provider": "HuggingFace",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "auto"
        },
        "rag": {
            "chunk_size": 500,
            "chunk_overlap": 50,
            "top_k": 5,
            "similarity_threshold": 0.7
        },
        "system": {
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "temp_cleanup_hours": 24,
            "max_concurrent_tasks": 4
        }
    }

def get_config_value(key: str, default: Any = None, config: Optional[Dict] = None) -> Any:
    """获取配置值（支持点号分隔的嵌套键）"""
    if config is None:
        config = load_config()
    
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default

def set_config_value(key: str, value: Any, config: Optional[Dict] = None) -> Dict[str, Any]:
    """设置配置值（支持点号分隔的嵌套键）"""
    if config is None:
        config = load_config()
    
    keys = key.split('.')
    current = config
    
    # 导航到目标位置
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # 设置值
    current[keys[-1]] = value
    
    return config
