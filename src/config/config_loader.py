"""
配置加载器
Stage 8.1 - 配置加载和保存
"""

import json
import os
from typing import Dict, Any


class ConfigLoader:
    """配置加载器 - 统一管理配置文件"""
    
    CONFIG_FILE = "rag_config.json"
    
    # 默认配置
    DEFAULT_CONFIG = {
        "llm_provider": "Ollama",
        "llm_url_ollama": "http://localhost:11434",
        "llm_model_ollama": "qwen2.5:7b",
        "llm_url_openai": "https://api.openai.com/v1",
        "llm_key_openai": "",
        "llm_model_openai": "gpt-3.5-turbo",
        "llm_temperature": 0.7,
        "embed_provider_idx": 0,
        "embed_model_hf": "BAAI/bge-small-zh-v1.5",
        "embed_url_ollama": "http://localhost:11434",
        "embed_model_ollama": "nomic-embed-text",
        "embed_url_openai": "https://api.openai.com/v1",
        "embed_key_openai": "",
        "embed_model_openai": "text-embedding-ada-002",
        "target_path": "",
        "enable_metadata": False,
        "enable_bm25": False,
        "enable_rerank": False
    }
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（确保新增字段存在）
                merged = cls.DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
            except Exception as e:
                print(f"⚠️ 配置加载失败: {e}，使用默认配置")
                return cls.DEFAULT_CONFIG.copy()
        return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save(cls, config: Dict[str, Any]) -> bool:
        """
        保存配置文件
        
        Args:
            config: 配置字典
        
        Returns:
            是否保存成功
        """
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
            return False
    
    @classmethod
    def get_default(cls, key: str, default: Any = None) -> Any:
        """
        获取默认配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        """
        return cls.DEFAULT_CONFIG.get(key, default)
    
    @classmethod
    def quick_setup(cls) -> Dict[str, Any]:
        """
        快速配置（一键配置）
        
        Returns:
            配置字典
        """
        config = cls.load()
        
        # 自动配置 Ollama
        config["llm_provider"] = "Ollama"
        config["llm_url_ollama"] = "http://localhost:11434"
        config["llm_model_ollama"] = "qwen2.5:7b"
        
        # 自动配置嵌入模型
        config["embed_provider_idx"] = 0  # HuggingFace
        config["embed_model_hf"] = "BAAI/bge-small-zh-v1.5"
        
        cls.save(config)
        return config
    
    @classmethod
    def reset_to_default(cls) -> Dict[str, Any]:
        """
        重置为默认配置
        
        Returns:
            默认配置字典
        """
        config = cls.DEFAULT_CONFIG.copy()
        cls.save(config)
        return config
    
    @classmethod
    def update(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新配置（部分更新）
        
        Args:
            updates: 要更新的配置项
        
        Returns:
            更新后的完整配置
        """
        config = cls.load()
        config.update(updates)
        cls.save(config)
        return config
    
    @classmethod
    def get_llm_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取 LLM 配置
        
        Args:
            config: 完整配置
        
        Returns:
            LLM 配置字典
        """
        provider = config.get('llm_provider', 'Ollama')
        
        if provider == 'Ollama':
            return {
                'provider': 'Ollama',
                'url': config.get('llm_url_ollama', 'http://localhost:11434'),
                'model': config.get('llm_model_ollama', 'qwen2.5:7b'),
                'key': '',
                'temperature': config.get('llm_temperature', 0.7)
            }
        else:  # OpenAI
            return {
                'provider': 'OpenAI',
                'url': config.get('llm_url_openai', 'https://api.openai.com/v1'),
                'model': config.get('llm_model_openai', 'gpt-3.5-turbo'),
                'key': config.get('llm_key_openai', ''),
                'temperature': config.get('llm_temperature', 0.7)
            }
    
    @classmethod
    def get_embed_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取嵌入模型配置
        
        Args:
            config: 完整配置
        
        Returns:
            嵌入模型配置字典
        """
        provider_idx = config.get('embed_provider_idx', 0)
        providers = ["HuggingFace", "Ollama", "OpenAI"]
        provider = providers[provider_idx] if provider_idx < len(providers) else "HuggingFace"
        
        if provider == 'HuggingFace':
            return {
                'provider': 'HuggingFace',
                'model': config.get('embed_model_hf', 'BAAI/bge-small-zh-v1.5'),
                'url': '',
                'key': ''
            }
        elif provider == 'Ollama':
            return {
                'provider': 'Ollama',
                'model': config.get('embed_model_ollama', 'nomic-embed-text'),
                'url': config.get('embed_url_ollama', 'http://localhost:11434'),
                'key': ''
            }
        else:  # OpenAI
            return {
                'provider': 'OpenAI',
                'model': config.get('embed_model_openai', 'text-embedding-ada-002'),
                'url': config.get('embed_url_openai', 'https://api.openai.com/v1'),
                'key': config.get('embed_key_openai', '')
            }
