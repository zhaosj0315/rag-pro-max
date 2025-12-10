"""
知识库处理器
提取自 apppro.py 的 process_knowledge_base_logic 函数
"""

import os
import time
import psutil
from datetime import datetime
from llama_index.core import Settings

from src.logging import LogManager
from src.utils.model_manager import load_embedding_model
from src.utils.adaptive_throttling import get_resource_guard
from src.processors.index_builder import IndexBuilder


class KnowledgeBaseProcessor:
    """知识库处理器"""
    
    def __init__(self):
        self.logger = LogManager()
        self.resource_guard = get_resource_guard()
    
    def process_knowledge_base(self, final_kb_name: str, output_base: str, 
                             embed_provider: str, embed_model: str, 
                             embed_key: str, embed_url: str,
                             status_callback=None) -> bool:
        """
        处理知识库逻辑
        
        Args:
            final_kb_name: 知识库名称
            output_base: 输出基础路径
            embed_provider: 嵌入模型提供商
            embed_model: 嵌入模型名称
            embed_key: API密钥
            embed_url: API地址
            status_callback: 状态回调函数
            
        Returns:
            bool: 处理是否成功
        """
        persist_dir = os.path.join(output_base, final_kb_name)
        start_time = time.time()
        
        try:
            # 资源保护检查
            if not self._check_resources():
                return False
            
            # 设置嵌入模型
            if not self._setup_embedding_model(embed_provider, embed_model, embed_key, embed_url):
                return False
            
            self.logger.log("INFO", f"开始处理知识库: {final_kb_name}", stage="知识库处理")
            
            # 使用 IndexBuilder 处理
            builder = IndexBuilder(
                persist_dir=persist_dir,
                logger=self.logger,
                callback=status_callback
            )
            
            success = builder.build_index()
            
            if success:
                elapsed = time.time() - start_time
                self.logger.success(f"✅ 知识库 '{final_kb_name}' 处理完成")
                self.logger.info(f"⏱️  耗时: {elapsed:.1f} 秒")
                return True
            else:
                self.logger.error(f"❌ 知识库处理失败: {final_kb_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 知识库处理异常: {str(e)}")
            return False
    
    def _check_resources(self) -> bool:
        """检查系统资源"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            result = self.resource_guard.check_resources(cpu, mem, 0)
            throttle_info = result.get('throttle', {})
            
            if throttle_info.get('action') == 'reject':
                self.logger.warning(f"资源不足，暂停处理: CPU={cpu}%, MEM={mem}%")
                return False
            return True
        except Exception as e:
            self.logger.warning(f"资源检查失败: {e}")
            return True  # 检查失败时继续处理
    
    def _setup_embedding_model(self, provider: str, model: str, key: str, url: str) -> bool:
        """设置嵌入模型"""
        try:
            self.logger.info(f"🔧 设置嵌入模型: {model} (provider: {provider})")
            embed = load_embedding_model(provider, model, key, url)
            
            if not embed:
                self.logger.error(f"❌ 嵌入模型加载失败: {model}")
                return False
            
            Settings.embed_model = embed
            
            try:
                actual_dim = len(embed._get_text_embedding("test"))
                self.logger.success(f"✅ 嵌入模型已设置: {model} ({actual_dim}维)")
            except:
                self.logger.success(f"✅ 嵌入模型已设置: {model}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 嵌入模型设置失败: {str(e)}")
            return False
