"""
增强的内存管理器
"""

import gc
import psutil
import torch
import streamlit as st
from typing import Dict, Any

class MemoryManager:
    """增强的内存管理器"""
    
    def __init__(self):
        self.memory_threshold = 85  # 内存使用率阈值
        self.gpu_threshold = 90     # GPU内存阈值
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计"""
        memory = psutil.virtual_memory()
        stats = {
            "total_gb": memory.total / (1024**3),
            "used_gb": memory.used / (1024**3),
            "available_gb": memory.available / (1024**3),
            "percent": memory.percent
        }
        
        # GPU内存
        if torch.backends.mps.is_available():
            try:
                stats["gpu_available"] = True
                stats["gpu_memory_gb"] = torch.mps.driver_allocated_memory() / (1024**3)
            except:
                stats["gpu_available"] = False
        else:
            stats["gpu_available"] = False
        
        return stats
    
    def cleanup_memory(self, force: bool = False):
        """清理内存"""
        stats = self.get_memory_stats()
        
        if force or stats["percent"] > self.memory_threshold:
            # Python垃圾回收
            collected = gc.collect()
            
            # GPU内存清理
            if torch.backends.mps.is_available():
                try:
                    torch.mps.empty_cache()
                    torch.mps.synchronize()
                except:
                    pass
            
            # Streamlit缓存清理
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()
            
            return collected
        return 0
    
    def monitor_memory(self) -> bool:
        """监控内存使用"""
        stats = self.get_memory_stats()
        
        if stats["percent"] > self.memory_threshold:
            st.warning(f"⚠️ 内存使用率过高: {stats['percent']:.1f}%")
            self.cleanup_memory()
            return False
        return True
    
    def display_memory_info(self):
        """显示内存信息"""
        stats = self.get_memory_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("内存使用", f"{stats['percent']:.1f}%", 
                     f"{stats['used_gb']:.1f}GB / {stats['total_gb']:.1f}GB")
        
        with col2:
            if stats["gpu_available"]:
                st.metric("GPU内存", f"{stats['gpu_memory_gb']:.1f}GB")
            else:
                st.metric("GPU", "不可用")

# 全局内存管理器
memory_manager = MemoryManager()
