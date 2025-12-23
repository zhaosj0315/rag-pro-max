"""
应用配置模块
负责配置文件管理和默认值设置
"""

import json
import os
from src.app_logging import LogManager

logger = LogManager()

CONFIG_FILE = "rag_config.json"
output_base = "vector_db_storage"

def load_config():
    """加载配置文件 - 使用统一服务"""
    from src.services.unified_config_service import load_config as unified_load_config
    
    defaults = {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "top_k": 5,
        "similarity_threshold": 0.7,
        "temperature": 0.7,
        "max_tokens": 2000,
        "llm_provider": "Ollama",
        "llm_url": "http://localhost:11434",
        "llm_model": "gpt-oss:20b",
        "llm_key": "",
        "embed_provider": "HuggingFace (本地/极速)",
        "embed_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embed_url": "",
        "embed_key": ""
    }
    
    return unified_load_config("rag_config", defaults)

def save_config(config):
    """保存配置文件 - 使用统一服务"""
    from src.services.unified_config_service import save_config as unified_save_config
    return unified_save_config(config, "rag_config")

def get_existing_kbs(output_base):
    """获取现有知识库列表"""
    try:
        if not os.path.exists(output_base):
            os.makedirs(output_base)
        return [d for d in os.listdir(output_base) 
                if os.path.isdir(os.path.join(output_base, d)) and not d.startswith('.')]
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        return []
