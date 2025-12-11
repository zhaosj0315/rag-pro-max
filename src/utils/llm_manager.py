"""
LLM管理器
提取自 apppro.py 的 get_llm 函数
"""

from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama
from src.app_logging import LogManager


class LLMManager:
    """LLM管理器"""
    
    def __init__(self):
        self.logger = LogManager()
    
    def get_llm(self, provider: str, model: str, key: str, url: str, temp: float = 0.7):
        """
        获取LLM实例
        
        Args:
            provider: 提供商
            model: 模型名称
            key: API密钥
            url: API地址
            temp: 温度参数
            
        Returns:
            LLM实例或None
        """
        try:
            if provider == "Ollama":
                return self._create_ollama_llm(model, url, temp)
            else:
                return self._create_openai_llm(model, key, url, temp)
                
        except Exception as e:
            self.logger.error(f"❌ LLM创建失败: {str(e)}")
            return None
    
    def _create_ollama_llm(self, model: str, url: str, temp: float):
        """创建Ollama LLM"""
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url += '/api'
        
        return Ollama(
            model=model,
            base_url=base_url,
            temperature=temp,
            request_timeout=120.0
        )
    
    def _create_openai_llm(self, model: str, key: str, url: str, temp: float):
        """创建OpenAI兼容LLM"""
        # 清理URL
        clean_url = url.strip()
        if clean_url.endswith('/'):
            clean_url = clean_url[:-1]
        if not clean_url.endswith('/v1'):
            clean_url += '/v1'
        
        return OpenAI(
            model=model,
            api_key=key,
            api_base=clean_url,
            temperature=temp,
            request_timeout=120.0
        )


# 全局实例
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """获取LLM管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

# 兼容性函数
def get_llm(provider: str, model: str, key: str, url: str, temp: float = 0.7):
    """兼容性函数"""
    manager = get_llm_manager()
    return manager.get_llm(provider, model, key, url, temp)
