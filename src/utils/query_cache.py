"""查询缓存模块 - LRU Cache"""

from functools import lru_cache
from typing import Optional, List, Tuple
import hashlib


class QueryCache:
    """查询缓存管理器"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
    
    def _make_key(self, query: str, kb_name: str, top_k: int) -> str:
        """生成缓存键"""
        data = f"{query}|{kb_name}|{top_k}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, query: str, kb_name: str, top_k: int) -> Optional[Tuple]:
        """获取缓存"""
        key = self._make_key(query, kb_name, top_k)
        
        if key in self.cache:
            # 更新访问顺序
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        
        return None
    
    def set(self, query: str, kb_name: str, top_k: int, result: Tuple):
        """设置缓存"""
        key = self._make_key(query, kb_name, top_k)
        
        # 如果缓存已满，删除最旧的
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = result
        
        if key not in self.access_order:
            self.access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "usage": f"{len(self.cache) / self.max_size * 100:.1f}%"
        }


# 全局缓存实例
_global_cache: Optional[QueryCache] = None


def get_cache() -> QueryCache:
    """获取全局缓存"""
    global _global_cache
    if _global_cache is None:
        _global_cache = QueryCache(max_size=100)
    return _global_cache
