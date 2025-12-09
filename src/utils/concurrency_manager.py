"""
并发优化管理器 - Concurrency Optimization Manager
统一管理所有并发优化功能
"""

from typing import List, Dict, Any, Callable
from .async_pipeline import AsyncPipeline, run_async_pipeline
from .dynamic_batch import DynamicBatchOptimizer
from .smart_scheduler import SmartScheduler, TaskType
import time


class ConcurrencyManager:
    """并发优化管理器"""
    
    def __init__(self, embedding_dim: int = 1024):
        self.batch_optimizer = DynamicBatchOptimizer(embedding_dim=embedding_dim)
        self.scheduler = SmartScheduler()
        self.stats = {
            'total_docs': 0,
            'total_time': 0,
            'throughput': 0
        }
        self._is_shutdown = False
    
    def process_documents_optimized(self, documents: List[Any],
                                    parse_func: Callable,
                                    embed_func: Callable,
                                    store_func: Callable,
                                    use_pipeline: bool = True) -> Dict[str, Any]:
        """
        优化的文档处理
        
        Args:
            documents: 文档列表
            parse_func: 解析函数
            embed_func: 向量化函数
            store_func: 存储函数
            use_pipeline: 是否使用异步管道
        
        Returns:
            处理统计信息
        """
        if self._is_shutdown:
            raise RuntimeError("ConcurrencyManager已关闭")
        
        start_time = time.time()
        doc_count = len(documents)
        
        # 获取最优配置
        config = self.batch_optimizer.get_optimal_config(doc_count)
        
        try:
            if use_pipeline and doc_count > 10:
                # 使用异步管道
                stats = run_async_pipeline(documents, parse_func, embed_func, store_func)
            else:
                # 使用智能调度器
                stats = self._process_with_scheduler(documents, parse_func, embed_func, store_func)
        except Exception as e:
            raise RuntimeError(f"文档处理失败: {e}")
        
        total_time = time.time() - start_time
        
        return {
            'config': config,
            'stats': stats,
            'total_time': total_time,
            'throughput': doc_count / total_time if total_time > 0 else 0
        }
    
    def _process_with_scheduler(self, documents: List[Any],
                                parse_func: Callable,
                                embed_func: Callable,
                                store_func: Callable) -> Dict[str, Any]:
        """使用智能调度器处理"""
        # 解析阶段（CPU密集）
        parsed = self.scheduler.map(TaskType.CPU_INTENSIVE, parse_func, documents)
        
        # 向量化阶段（GPU密集）
        embedded = self.scheduler.map(TaskType.GPU_INTENSIVE, embed_func, parsed)
        
        # 存储阶段（IO密集）
        stored = self.scheduler.map(TaskType.IO_INTENSIVE, store_func, embedded)
        
        return {
            'parsed': len(parsed),
            'embedded': len(embedded),
            'stored': len(stored),
            'scheduler_stats': self.scheduler.get_stats()
        }
    
    def get_optimal_batch_size(self, doc_count: int) -> int:
        """获取最优batch size"""
        return self.batch_optimizer.calculate_batch_size(doc_count)
    
    def shutdown(self):
        """关闭管理器，释放资源"""
        if not self._is_shutdown:
            self.scheduler.shutdown()
            self._is_shutdown = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
    
    def __del__(self):
        """析构时自动清理"""
        if not self._is_shutdown:
            self.shutdown()


# 全局实例
_manager = None


def get_concurrency_manager(embedding_dim: int = 1024) -> ConcurrencyManager:
    """获取全局并发管理器"""
    global _manager
    if _manager is None or _manager._is_shutdown:
        _manager = ConcurrencyManager(embedding_dim=embedding_dim)
    return _manager


def cleanup_concurrency_manager():
    """清理全局管理器"""
    global _manager
    if _manager is not None:
        _manager.shutdown()
        _manager = None
