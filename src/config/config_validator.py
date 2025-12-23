"""
配置验证器 - 最小实现
"""

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        pass
    
    def validate_config(self, config):
        """验证配置 - 使用统一服务"""
        from src.services.unified_config_service import unified_config_service
        
        # 基本验证规则
        schema = {
            'chunk_size': int,
            'temperature': (int, float),
            'top_k': int
        }
        
        return unified_config_service.validate_config(config, schema)
