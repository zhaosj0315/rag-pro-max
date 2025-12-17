"""
智能任务调度器
根据系统资源动态调整并发策略
"""

import os
import psutil
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass


@dataclass
class ResourceStatus:
    """系统资源状态"""
    cpu_percent: float
    memory_percent: float
    gpu_memory_used: float
    gpu_memory_total: float
    available_cores: int


class TaskScheduler:
    """智能任务调度器"""
    
    def __init__(self):
        self.resource_cache = {}
        self.cache_ttl = 5  # 缓存5秒
        
    def get_resource_status(self) -> ResourceStatus:
        """获取系统资源状态（带缓存）"""
        now = time.time()
        if 'timestamp' in self.resource_cache and now - self.resource_cache['timestamp'] < self.cache_ttl:
            return self.resource_cache['status']
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            available_cores = max(1, os.cpu_count() - 1)
            
            # GPU内存检测（简化版）
            gpu_memory_used = 0
            gpu_memory_total = 1
            try:
                import torch
                if torch.backends.mps.is_available():
                    # MPS显存无法直接获取，使用估算
                    gpu_memory_used = 0.5  # 估算50%使用率
                    gpu_memory_total = 1
            except:
                pass
            
            status = ResourceStatus(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                gpu_memory_used=gpu_memory_used,
                gpu_memory_total=gpu_memory_total,
                available_cores=available_cores
            )
            
            # 更新缓存
            self.resource_cache = {
                'timestamp': now,
                'status': status
            }
            
            return status
        except:
            # 降级：返回保守估算
            return ResourceStatus(50, 50, 0.5, 1, max(1, os.cpu_count() - 1))
    
    def get_optimal_workers(self, task_type: str, task_count: int) -> Dict[str, Any]:
        """获取最优工作进程配置"""
        status = self.get_resource_status()
        
        if task_type == "question_validation":
            # 推荐问题验证：轻量级任务，适合多线程
            if status.cpu_percent > 80:
                workers = 2
            elif task_count <= 3:
                workers = min(3, task_count)
            else:
                workers = min(5, task_count)
            
            return {
                'executor_type': 'thread',
                'max_workers': workers,
                'timeout': 10
            }
        
        elif task_type == "document_parsing":
            # 文档解析：CPU密集，适合多进程
            if status.cpu_percent > 85 or status.memory_percent > 85:
                workers = max(2, status.available_cores // 2)
            else:
                workers = min(status.available_cores, max(2, task_count // 5))
            
            return {
                'executor_type': 'process',
                'max_workers': workers,
                'chunksize': max(1, task_count // (workers * 2))
            }
        
        elif task_type == "embedding":
            # 向量化：GPU密集，限制并发
            if status.gpu_memory_used > 0.8:
                workers = 1  # GPU内存不足，串行处理
            else:
                workers = 2  # 适度并行
            
            return {
                'executor_type': 'thread',
                'max_workers': workers,
                'batch_size': 1024 if status.gpu_memory_used < 0.7 else 512
            }
        
        else:
            # 默认配置
            return {
                'executor_type': 'thread',
                'max_workers': min(4, max(2, status.available_cores // 2))
            }
    
    def should_use_parallel(self, task_type: str, task_count: int) -> bool:
        """判断是否应该使用并行处理"""
        status = self.get_resource_status()
        
        # 系统负载过高，避免并行
        if status.cpu_percent > 90 or status.memory_percent > 90:
            return False
        
        # 任务数太少，串行更快
        if task_count < 3:
            return False
        
        # 单核系统，并行无意义
        if status.available_cores <= 1:
            return False
        
        return True


# 全局调度器实例
_scheduler = None

def get_scheduler() -> TaskScheduler:
    """获取全局任务调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
