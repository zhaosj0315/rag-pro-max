#!/usr/bin/env python3
"""
统一配置服务
整合所有配置保存、加载、验证逻辑
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class UnifiedConfigService:
    """统一配置服务"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
    
    def save_config(self, config_data: Dict[str, Any], config_name: str) -> bool:
        """统一配置保存方法"""
        try:
            config_file = self.config_dir / f"{config_name}.json"
            
            # 确保配置数据是可序列化的
            serializable_data = self._make_serializable(config_data)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存配置失败 {config_name}: {e}")
            return False
    
    def load_config(self, config_name: str, default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """统一配置加载方法"""
        config_file = self.config_dir / f"{config_name}.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败 {config_name}: {e}")
        
        return default_config or {}
    
    def validate_config(self, config_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """验证配置数据"""
        try:
            for key, expected_type in schema.items():
                if key in config_data:
                    if not isinstance(config_data[key], expected_type):
                        return False
            return True
        except Exception:
            return False
    
    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """获取单个配置值"""
        config = self.load_config(config_name)
        return config.get(key, default)
    
    def set_config_value(self, config_name: str, key: str, value: Any) -> bool:
        """设置单个配置值"""
        config = self.load_config(config_name)
        config[key] = value
        return self.save_config(config, config_name)
    
    def _make_serializable(self, obj: Any) -> Any:
        """确保对象可JSON序列化"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

# 全局实例
unified_config_service = UnifiedConfigService()

# 便捷函数
def save_config(config_data: Dict[str, Any], config_name: str) -> bool:
    """保存配置 - 便捷函数"""
    return unified_config_service.save_config(config_data, config_name)

def load_config(config_name: str, default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """加载配置 - 便捷函数"""
    return unified_config_service.load_config(config_name, default_config)

def get_config_value(config_name: str, key: str, default: Any = None) -> Any:
    """获取配置值 - 便捷函数"""
    return unified_config_service.get_config_value(config_name, key, default)

def set_config_value(config_name: str, key: str, value: Any) -> bool:
    """设置配置值 - 便捷函数"""
    return unified_config_service.set_config_value(config_name, key, value)
