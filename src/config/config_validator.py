"""
配置验证器
Stage 8.2 - 配置验证和检查
"""

from typing import Dict, List, Tuple, Any
import os
import requests


class ConfigValidator:
    """配置验证器 - 验证配置的有效性"""
    
    @staticmethod
    def validate_llm_config(config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证 LLM 配置
        
        Args:
            config: LLM 配置字典
        
        Returns:
            (是否有效, 错误信息)
        """
        provider = config.get('provider', '')
        
        if not provider:
            return False, "未指定 LLM 提供商"
        
        if provider == 'Ollama':
            url = config.get('url', '')
            if not url:
                return False, "Ollama URL 不能为空"
            
            # 检查 Ollama 服务是否可用
            try:
                response = requests.get(f"{url}/api/tags", timeout=2)
                if response.status_code != 200:
                    return False, f"Ollama 服务不可用 (状态码: {response.status_code})"
            except Exception as e:
                return False, f"无法连接到 Ollama 服务: {str(e)}"
            
            model = config.get('model', '')
            if not model:
                return False, "Ollama 模型不能为空"
        
        elif provider == 'OpenAI':
            url = config.get('url', '')
            key = config.get('key', '')
            model = config.get('model', '')
            
            if not url:
                return False, "OpenAI URL 不能为空"
            if not key:
                return False, "OpenAI API Key 不能为空"
            if not model:
                return False, "OpenAI 模型不能为空"
        
        else:
            return False, f"不支持的 LLM 提供商: {provider}"
        
        return True, ""
    
    @staticmethod
    def validate_embed_config(config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证嵌入模型配置
        
        Args:
            config: 嵌入模型配置字典
        
        Returns:
            (是否有效, 错误信息)
        """
        provider = config.get('provider', '')
        
        if not provider:
            return False, "未指定嵌入模型提供商"
        
        if provider == 'HuggingFace':
            model = config.get('model', '')
            if not model:
                return False, "HuggingFace 模型不能为空"
        
        elif provider == 'Ollama':
            url = config.get('url', '')
            model = config.get('model', '')
            
            if not url:
                return False, "Ollama URL 不能为空"
            if not model:
                return False, "Ollama 嵌入模型不能为空"
            
            # 检查 Ollama 服务
            try:
                response = requests.get(f"{url}/api/tags", timeout=2)
                if response.status_code != 200:
                    return False, f"Ollama 服务不可用 (状态码: {response.status_code})"
            except Exception as e:
                return False, f"无法连接到 Ollama 服务: {str(e)}"
        
        elif provider == 'OpenAI':
            url = config.get('url', '')
            key = config.get('key', '')
            model = config.get('model', '')
            
            if not url:
                return False, "OpenAI URL 不能为空"
            if not key:
                return False, "OpenAI API Key 不能为空"
            if not model:
                return False, "OpenAI 嵌入模型不能为空"
        
        else:
            return False, f"不支持的嵌入模型提供商: {provider}"
        
        return True, ""
    
    @staticmethod
    def validate_path(path: str) -> Tuple[bool, str]:
        """
        验证文件/文件夹路径
        
        Args:
            path: 路径
        
        Returns:
            (是否有效, 错误信息)
        """
        if not path:
            return False, "路径不能为空"
        
        if not os.path.exists(path):
            return False, f"路径不存在: {path}"
        
        return True, ""
    
    @staticmethod
    def validate_kb_name(name: str) -> Tuple[bool, str]:
        """
        验证知识库名称
        
        Args:
            name: 知识库名称
        
        Returns:
            (是否有效, 错误信息)
        """
        if not name:
            return False, "知识库名称不能为空"
        
        if len(name) > 50:
            return False, "知识库名称过长（最多50字符）"
        
        # 检查非法字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in name:
                return False, f"知识库名称包含非法字符: {char}"
        
        return True, ""
    
    @staticmethod
    def validate_temperature(temp: float) -> Tuple[bool, str]:
        """
        验证温度参数
        
        Args:
            temp: 温度值
        
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(temp, (int, float)):
            return False, "温度必须是数字"
        
        if temp < 0 or temp > 2:
            return False, "温度必须在 0-2 之间"
        
        return True, ""
    
    @staticmethod
    def check_ollama_service(url: str) -> Tuple[bool, List[str]]:
        """
        检查 Ollama 服务并获取可用模型
        
        Args:
            url: Ollama URL
        
        Returns:
            (是否可用, 模型列表)
        """
        try:
            response = requests.get(f"{url}/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return True, models
            return False, []
        except Exception:
            return False, []
