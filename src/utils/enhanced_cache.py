"""
增强查询缓存系统 - 纯内存版本
目标：实现秒级响应，无需外部数据库
"""

import hashlib
import json
import time
import threading
from typing import Dict, Any, Optional, List
from collections import OrderedDict
from src.logging import LogManager

logger = LogManager()

class EnhancedQueryCache:
    """增强查询缓存系统"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self.cleanup_thread.start()
    
    def _generate_key(self, query: str, kb_name: str, **kwargs) -> str:
        """生成缓存键"""
        # 标准化查询
        normalized_query = query.strip().lower()
        
        # 创建缓存键
        key_data = {
            "query": normalized_query,
            "kb_name": kb_name,
            **kwargs
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query: str, kb_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        key = self._generate_key(query, kb_name, **kwargs)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # 检查是否过期
                if time.time() - entry["timestamp"] < self.ttl:
                    # 更新访问时间
                    self.access_times[key] = time.time()
                    # 移到末尾（LRU）
                    self.cache.move_to_end(key)
                    
                    self.hit_count += 1
                    logger.info(f"🎯 缓存命中: {query[:50]}...")
                    return entry["data"]
                else:
                    # 过期删除
                    del self.cache[key]
                    del self.access_times[key]
            
            self.miss_count += 1
            return None
    
    def set(self, query: str, kb_name: str, data: Dict[str, Any], **kwargs):
        """设置缓存"""
        key = self._generate_key(query, kb_name, **kwargs)
        
        with self.lock:
            # 检查容量
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # 存储缓存
            self.cache[key] = {
                "data": data,
                "timestamp": time.time(),
                "query": query[:100],  # 存储查询片段用于调试
                "kb_name": kb_name
            }
            self.access_times[key] = time.time()
            
            logger.info(f"💾 缓存存储: {query[:50]}...")
    
    def _evict_lru(self):
        """淘汰最少使用的缓存"""
        if self.cache:
            # 找到最少访问的键
            lru_key = min(self.access_times.keys(), 
                         key=lambda k: self.access_times[k])
            
            del self.cache[lru_key]
            del self.access_times[lru_key]
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                with self.lock:
                    for key, entry in self.cache.items():
                        if current_time - entry["timestamp"] >= self.ttl:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self.cache[key]
                        del self.access_times[key]
                
                if expired_keys:
                    logger.info(f"🧹 清理过期缓存: {len(expired_keys)}个")
                
                time.sleep(300)  # 5分钟清理一次
                
            except Exception as e:
                logger.error(f"缓存清理失败: {e}")
                time.sleep(60)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl": self.ttl
        }
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.hit_count = 0
            self.miss_count = 0
        
        logger.info("🧹 缓存已清空")
    
    def preload_common_queries(self, kb_name: str, common_queries: List[str]):
        """预加载常用查询"""
        logger.info(f"🔄 预加载常用查询: {len(common_queries)}个")
        
        for query in common_queries:
            # 这里可以预先计算并缓存结果
            # 实际实现时需要调用真实的查询函数
            pass

# 全局缓存实例
enhanced_cache = EnhancedQueryCache()

class SmartCacheManager:
    """智能缓存管理器"""
    
    def __init__(self):
        self.cache = enhanced_cache
        self.query_patterns = {}  # 查询模式分析
    
    def cached_query(self, query_func):
        """缓存装饰器"""
        def wrapper(query: str, kb_name: str, **kwargs):
            # 尝试从缓存获取
            cached_result = self.cache.get(query, kb_name, **kwargs)
            if cached_result:
                return cached_result
            
            # 执行查询
            start_time = time.time()
            result = query_func(query, kb_name, **kwargs)
            query_time = time.time() - start_time
            
            # 存储到缓存
            if result and query_time > 0.5:  # 只缓存耗时查询
                self.cache.set(query, kb_name, result, **kwargs)
            
            return result
        
        return wrapper
    
    def analyze_query_patterns(self, query: str):
        """分析查询模式"""
        # 简单的模式分析
        words = query.lower().split()
        for word in words:
            if len(word) > 3:
                self.query_patterns[word] = self.query_patterns.get(word, 0) + 1

# 全局智能缓存管理器
smart_cache_manager = SmartCacheManager()
