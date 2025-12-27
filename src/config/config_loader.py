"""
配置加载器 - 适配 UnifiedConfigService
"""
from typing import Dict, Any
from src.services.unified_config_service import load_config, save_config

class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load() -> Dict[str, Any]:
        """加载配置 (rag_config)"""
        return load_config("rag_config")
    
    @staticmethod
    def save(config: Dict[str, Any]) -> bool:
        """保存配置 (rag_config)"""
        return save_config(config, "rag_config")

    # 兼容旧接口
    def load_config(self):
        return self.load()