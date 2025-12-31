"""
优化管理器
统一管理所有性能优化
"""

import time
import threading
from typing import Dict, Any
from src.utils.gpu_optimizer import gpu_optimizer
from src.utils.enhanced_cache import enhanced_cache
from src.processors.multimodal_processor import multimodal_processor
from src.app_logging import LogManager

logger = LogManager()

class OptimizationManager:
    """优化管理器"""
    
    def __init__(self):
        self.optimizations_enabled = {
            "gpu": True,
            "cache": True,
            "multimodal": True
        }
        self.stats = {
            "gpu_utilization": 0,
            "cache_hit_rate": 0,
            "query_speed": 0,
            "multimodal_support": True
        }
        
    def initialize_all_optimizations(self):
        """初始化所有优化"""
        logger.info("🚀 初始化性能优化系统...")
        
        try:
            # 1. GPU优化
            if self.optimizations_enabled["gpu"]:
                gpu_optimizer.optimize_gpu_utilization()
                logger.info("✅ GPU优化已启用")
            
            # 2. 缓存优化
            if self.optimizations_enabled["cache"]:
                self._initialize_cache_optimization()
                logger.info("✅ 缓存优化已启用")
            
            # 3. 多模态支持
            if self.optimizations_enabled["multimodal"]:
                self._initialize_multimodal_support()
                logger.info("✅ 多模态支持已启用")
            
            # 启动监控线程
            self._start_monitoring()
            
            logger.info("🎉 所有优化初始化完成")
            
        except Exception as e:
            logger.error(f"优化初始化失败: {e}")
    
    def _initialize_cache_optimization(self):
        """初始化缓存优化"""
        # 预加载常用查询模式
        common_patterns = [
            "什么是",
            "如何",
            "为什么",
            "介绍一下",
            "总结"
        ]
        
        # 设置缓存预热
        enhanced_cache.max_size = 2000  # 增加缓存容量
        enhanced_cache.ttl = 7200  # 2小时TTL
    
    def _initialize_multimodal_support(self):
        """初始化多模态支持"""
        supported_formats = multimodal_processor.get_supported_formats()
        logger.info(f"📄 支持格式: {supported_formats}")
    
    def _start_monitoring(self):
        """启动性能监控"""
        monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        monitor_thread.start()
    
    def _monitor_performance(self):
        """监控性能指标"""
        while True:
            try:
                # 更新统计信息
                self._update_stats()
                
                # 每30秒监控一次
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"性能监控失败: {e}")
                time.sleep(60)
    
    def _update_stats(self):
        """更新性能统计"""
        try:
            # GPU统计
            gpu_stats = gpu_optimizer.get_gpu_stats()
            
            # 缓存统计
            cache_stats = enhanced_cache.get_stats()
            
            # 更新统计信息
            self.stats.update({
                "gpu_device": gpu_stats.get("device", "cpu"),
                "cache_hit_rate": cache_stats.get("hit_rate", "0%"),
                "cache_size": cache_stats.get("size", 0),
                "timestamp": time.time()
            })
            
        except Exception as e:
            logger.error(f"统计更新失败: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """获取优化状态"""
        return {
            "enabled": self.optimizations_enabled,
            "stats": self.stats,
            "version": "3.2.2"
        }
    
    def toggle_optimization(self, optimization_type: str, enabled: bool):
        """切换优化开关"""
        if optimization_type in self.optimizations_enabled:
            self.optimizations_enabled[optimization_type] = enabled
            logger.info(f"🔧 {optimization_type}优化: {'启用' if enabled else '禁用'}")
    
    def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理优化资源...")
        gpu_optimizer.cleanup()
        enhanced_cache.clear()

# 全局优化管理器
optimization_manager = OptimizationManager()
