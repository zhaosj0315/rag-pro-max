"""
内存优化器
主动优化内存使用
"""

import gc
import sys
import weakref
from functools import wraps
import streamlit as st

class MemoryOptimizer:
    def __init__(self):
        self.cache_refs = weakref.WeakValueDictionary()
        self.cleanup_callbacks = []
    
    def memory_efficient_cache(self, max_size=100):
        """内存高效的缓存装饰器"""
        def decorator(func):
            cache = {}
            access_order = []
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = str(args) + str(sorted(kwargs.items()))
                
                if key in cache:
                    # 更新访问顺序
                    access_order.remove(key)
                    access_order.append(key)
                    return cache[key]
                
                # 计算结果
                result = func(*args, **kwargs)
                
                # 缓存管理
                if len(cache) >= max_size:
                    # 删除最久未使用的项
                    oldest_key = access_order.pop(0)
                    del cache[oldest_key]
                
                cache[key] = result
                access_order.append(key)
                
                return result
            
            # 添加清理方法
            wrapper.clear_cache = lambda: (cache.clear(), access_order.clear())
            self.cleanup_callbacks.append(wrapper.clear_cache)
            
            return wrapper
        return decorator
    
    def optimize_session_state(self):
        """优化会话状态"""
        if not hasattr(st, 'session_state'):
            return
        
        # 清理空值和None
        keys_to_remove = []
        for key, value in st.session_state.items():
            if value is None or (hasattr(value, '__len__') and len(value) == 0):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        # 压缩大型列表
        self._compress_large_lists()
    
    def _compress_large_lists(self):
        """压缩大型列表"""
        if 'messages' in st.session_state:
            messages = st.session_state.messages
            if len(messages) > 100:
                # 保留最近的消息
                st.session_state.messages = messages[-50:]
        
        if 'suggestions_history' in st.session_state:
            history = st.session_state.suggestions_history
            if len(history) > 50:
                st.session_state.suggestions_history = history[-20:]
    
    def cleanup_all_caches(self):
        """清理所有缓存"""
        # 清理自定义缓存
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"缓存清理失败: {e}")
        
        # 清理Streamlit缓存
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
        
        # 强制垃圾回收
        gc.collect()
    
    def get_memory_usage(self):
        """获取内存使用情况"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def memory_warning_check(self, threshold_percent=80):
        """内存警告检查"""
        try:
            memory_info = self.get_memory_usage()
            if memory_info['percent'] > threshold_percent:
                return True, f"内存使用率过高: {memory_info['percent']:.1f}%"
            return False, None
        except Exception:
            return False, None
    
    def auto_optimize(self):
        """自动优化"""
        warning, message = self.memory_warning_check()
        if warning:
            print(f"⚠️ {message}")
            self.optimize_session_state()
            self.cleanup_all_caches()
            print("🧹 自动内存优化完成")

# 全局内存优化器
memory_optimizer = MemoryOptimizer()
