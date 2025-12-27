#!/usr/bin/env python3
"""
配置服务模块 - 统一配置管理逻辑
"""

import os
import json
from typing import Dict, Any, Optional, List
from src.common.config import load_config, save_config, get_default_config

class ConfigService:
    """统一的配置管理服务"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_cache = {}
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def get_config(self, config_name: str = "app_config.json") -> Dict[str, Any]:
        """获取配置"""
        config_path = os.path.join(self.config_dir, config_name)
        
        # 检查缓存
        if config_path in self.config_cache:
            return self.config_cache[config_path]
        
        # 加载配置
        config = load_config(config_path)
        
        # 缓存配置
        self.config_cache[config_path] = config
        
        return config
    
    def set_config(self, config: Dict[str, Any], config_name: str = "app_config.json") -> bool:
        """设置配置"""
        config_path = os.path.join(self.config_dir, config_name)
        
        # 保存配置
        success = save_config(config, config_path)
        
        if success:
            # 更新缓存
            self.config_cache[config_path] = config
        
        return success
    
    def get_config_value(self, key: str, default: Any = None, config_name: str = "app_config.json") -> Any:
        """获取配置值（支持点号分隔的嵌套键）"""
        from src.common.config import get_config_value
        config = self.get_config(config_name)
        return get_config_value(key, default, config)
    
    def set_config_value(self, key: str, value: Any, config_name: str = "app_config.json") -> bool:
        """设置配置值（支持点号分隔的嵌套键）"""
        from src.common.config import set_config_value
        config = self.get_config(config_name)
        updated_config = set_config_value(key, value, config)
        return self.set_config(updated_config, config_name)
    
    def reset_config(self, config_name: str = "app_config.json") -> bool:
        """重置配置为默认值"""
        default_config = get_default_config()
        return self.set_config(default_config, config_name)
    
    def backup_config(self, config_name: str = "app_config.json") -> Optional[str]:
        """备份配置文件"""
        try:
            import time
            config_path = os.path.join(self.config_dir, config_name)
            
            if not os.path.exists(config_path):
                return None
            
            # 创建备份文件名
            timestamp = int(time.time())
            backup_name = f"{config_name}.backup.{timestamp}"
            backup_path = os.path.join(self.config_dir, backup_name)
            
            # 复制文件
            import shutil
            shutil.copy2(config_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            print(f"备份配置失败: {e}")
            return None
    
    def restore_config(self, backup_path: str, config_name: str = "app_config.json") -> bool:
        """从备份恢复配置"""
        try:
            if not os.path.exists(backup_path):
                return False
            
            config_path = os.path.join(self.config_dir, config_name)
            
            # 复制备份文件
            import shutil
            shutil.copy2(backup_path, config_path)
            
            # 清除缓存
            if config_path in self.config_cache:
                del self.config_cache[config_path]
            
            return True
            
        except Exception as e:
            print(f"恢复配置失败: {e}")
            return False
    
    def list_config_files(self) -> List[str]:
        """列出所有配置文件"""
        try:
            if not os.path.exists(self.config_dir):
                return []
            
            config_files = []
            for file in os.listdir(self.config_dir):
                if file.endswith('.json') and not file.startswith('.'):
                    config_files.append(file)
            
            return sorted(config_files)
            
        except Exception:
            return []
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置 - 使用统一服务"""
        from src.services.unified_config_service import unified_config_service
        
        # 基本配置验证规则
        schema = {
            'llm': dict,
            'embedding': dict,
            'rag': dict,
            'system': dict
        }
        
        is_valid = unified_config_service.validate_config(config, schema)
        
        return {
            'valid': is_valid,
            'errors': [] if is_valid else ['配置验证失败'],
            'warnings': [],
            'config': config
        }
        
        # 检查嵌入模型配置
        if 'embedding' in config:
            embedding_config = config['embedding']
            if 'model' not in embedding_config:
                errors.append("嵌入模型配置缺少model字段")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def clear_cache(self):
        """清除配置缓存"""
        self.config_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'cached_configs': len(self.config_cache),
            'cache_keys': list(self.config_cache.keys())
        }

    def get_default_model(self) -> str:
        """获取默认模型 (智能判断供应商)"""
        # 显式读取 rag_config
        config = self.get_config("rag_config")
        
        provider = config.get('llm_provider', 'Ollama')
        
        if provider == 'OpenAI':
            return config.get('llm_model_openai', 'gpt-3.5-turbo')
        elif provider == 'OpenAI-Compatible':
            return config.get('llm_model_other', '')
        elif provider == 'Azure OpenAI':
            return config.get('azure_deployment', '')
        elif provider == 'Anthropic':
            return config.get('config_anthropic_model', '')
        elif provider == 'Moonshot':
            return config.get('config_moonshot_model', '')
        elif provider == 'Gemini':
            return config.get('config_gemini_model', '')
        elif provider == 'Groq':
            return config.get('config_groq_model', '')
            
        # 默认回退到 Ollama
        return config.get('llm_model_ollama', 'gpt-oss:20b')
    
    def update_model_config(self, new_model: str) -> bool:
        """更新模型配置"""
        try:
            # 更新配置
            success = self.set_config_value('llm_model_ollama', new_model)
            
            if success:
                # 更新相关配置
                ollama_url = self.get_config_value('llm_url_ollama', 'http://localhost:11434')
                
                # 这里可以添加更多的配置更新逻辑
                # 比如通知其他组件配置已更新
                
            return success
            
        except Exception as e:
            print(f"配置更新失败: {e}")
            return False

# 全局配置服务实例
_config_service = None

def get_config_service() -> ConfigService:
    """获取配置服务实例"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
