"""
配置加载器 - 适配 UnifiedConfigService
"""
from typing import Dict, Any
from src.services.unified_config_service import load_config, save_config
from src.services.user_config_manager import UserConfigManager

class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load() -> Dict[str, Any]:
        """加载配置 (rag_config)"""
        return load_config("rag_config")

    @staticmethod
    def load_for_user(username: str) -> Dict[str, Any]:
        """为特定用户加载配置"""
        return UserConfigManager.load_user_config(username)
    
    @staticmethod
    def save(config: Dict[str, Any]) -> bool:
        """保存配置 (rag_config)"""
        return save_config(config, "rag_config")

    @staticmethod
    def quick_setup() -> bool:
        """一键配置默认设置"""
        default_config = {
            "llm_provider": "Ollama",
            "llm_url_ollama": "http://localhost:11434",
            "llm_model_ollama": "gpt-oss:20b",
            "llm_provider_label": "🦙 Ollama (本地)",
            "embed_provider_idx": 0,
            "embed_model_hf": "sentence-transformers/all-MiniLM-L6-v2",
            "chat_history_limit": 10,
            "system_prompt": "你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。"
        }
        return ConfigLoader.save(default_config)

    # 兼容旧接口
    def load_config(self):
        return self.load()