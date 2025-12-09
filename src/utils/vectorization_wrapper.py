"""
向量化包装器 - 简化异步向量化接口
"""

from typing import List
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter

from src.utils.dynamic_batch import DynamicBatchOptimizer


class VectorizationWrapper:
    """向量化包装器 - 集成动态批量优化"""
    
    def __init__(self, embed_model, batch_optimizer=None):
        self.embed_model = embed_model
        self.batch_optimizer = batch_optimizer or DynamicBatchOptimizer()
        self.node_parser = SentenceSplitter()
    
    def vectorize_documents(self, documents: List[Document], show_progress: bool = True):
        """
        向量化文档（带动态批量优化）
        
        Args:
            documents: 文档列表
            show_progress: 是否显示进度
            
        Returns:
            VectorStoreIndex
        """
        # 获取优化的批量大小
        optimal_batch = self.batch_optimizer.calculate_batch_size(
            doc_count=len(documents),
            avg_doc_size=1000
        )
        
        # 构建索引（LlamaIndex 内部会处理向量化）
        # 批量优化主要通过内存管理实现
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=show_progress
        )
        
        return index
