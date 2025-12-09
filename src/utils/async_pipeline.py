"""
异步向量化管道 - Async Vectorization Pipeline
CPU和GPU流水线并行，提升处理效率
"""

import asyncio
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import logging

logger = logging.getLogger(__name__)


class AsyncPipeline:
    """异步处理管道"""
    
    def __init__(self, max_queue_size: int = 10):
        self.max_queue_size = max_queue_size
        self.parse_queue = asyncio.Queue(maxsize=max_queue_size)
        self.embed_queue = asyncio.Queue(maxsize=max_queue_size)
        self.stats = {
            'parsed': 0,
            'embedded': 0,
            'stored': 0,
            'parse_time': 0,
            'embed_time': 0,
            'store_time': 0,
            'errors': 0
        }
        self.errors = []
    
    async def parse_stage(self, documents: List[Any], parse_func: Callable):
        """解析阶段（CPU密集）"""
        try:
            for doc in documents:
                try:
                    start = time.time()
                    parsed = await asyncio.to_thread(parse_func, doc)
                    self.stats['parse_time'] += time.time() - start
                    self.stats['parsed'] += 1
                    await self.parse_queue.put(parsed)
                except Exception as e:
                    logger.error(f"解析文档失败: {e}")
                    self.stats['errors'] += 1
                    self.errors.append(('parse', str(e)))
        finally:
            # 发送结束信号
            await self.parse_queue.put(None)
    
    async def embed_stage(self, embed_func: Callable):
        """向量化阶段（GPU密集）"""
        try:
            while True:
                parsed = await self.parse_queue.get()
                if parsed is None:
                    await self.embed_queue.put(None)
                    break
                
                try:
                    start = time.time()
                    embedded = await asyncio.to_thread(embed_func, parsed)
                    self.stats['embed_time'] += time.time() - start
                    self.stats['embedded'] += 1
                    await self.embed_queue.put(embedded)
                except Exception as e:
                    logger.error(f"向量化失败: {e}")
                    self.stats['errors'] += 1
                    self.errors.append(('embed', str(e)))
        except Exception as e:
            logger.error(f"向量化阶段异常: {e}")
            await self.embed_queue.put(None)
    
    async def store_stage(self, store_func: Callable):
        """存储阶段（IO密集）"""
        try:
            while True:
                embedded = await self.embed_queue.get()
                if embedded is None:
                    break
                
                try:
                    start = time.time()
                    await asyncio.to_thread(store_func, embedded)
                    self.stats['store_time'] += time.time() - start
                    self.stats['stored'] += 1
                except Exception as e:
                    logger.error(f"存储失败: {e}")
                    self.stats['errors'] += 1
                    self.errors.append(('store', str(e)))
        except Exception as e:
            logger.error(f"存储阶段异常: {e}")
    
    async def run(self, documents: List[Any], parse_func: Callable, 
                  embed_func: Callable, store_func: Callable):
        """运行管道"""
        start_time = time.time()
        
        try:
            # 并行运行三个阶段
            await asyncio.gather(
                self.parse_stage(documents, parse_func),
                self.embed_stage(embed_func),
                self.store_stage(store_func)
            )
        except Exception as e:
            logger.error(f"管道运行异常: {e}")
            self.stats['errors'] += 1
            self.errors.append(('pipeline', str(e)))
        
        total_time = time.time() - start_time
        self.stats['total_time'] = total_time
        
        return self.stats
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'throughput': self.stats['stored'] / self.stats['total_time'] if self.stats['total_time'] > 0 else 0,
            'error_rate': self.stats['errors'] / (self.stats['parsed'] + self.stats['errors']) if (self.stats['parsed'] + self.stats['errors']) > 0 else 0
        }


def run_async_pipeline(documents: List[Any], parse_func: Callable,
                       embed_func: Callable, store_func: Callable) -> Dict[str, Any]:
    """运行异步管道的便捷函数"""
    pipeline = AsyncPipeline()
    return asyncio.run(pipeline.run(documents, parse_func, embed_func, store_func))
