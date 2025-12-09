"""
智能任务调度器 - Smart Task Scheduler
根据任务类型动态分配资源
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import Callable, Any, List
from enum import Enum
import os


class TaskType(Enum):
    """任务类型"""
    CPU_INTENSIVE = "cpu"      # CPU密集型（解析、计算）
    GPU_INTENSIVE = "gpu"      # GPU密集型（向量化）
    IO_INTENSIVE = "io"        # IO密集型（读写文件）
    MIXED = "mixed"            # 混合型


class SmartScheduler:
    """智能任务调度器"""
    
    def __init__(self, cpu_workers: int = None, gpu_workers: int = 4, io_workers: int = 20):
        """
        初始化调度器
        
        Args:
            cpu_workers: CPU工作线程数（默认为CPU核心数-1）
            gpu_workers: GPU工作线程数
            io_workers: IO工作线程数
        """
        self.cpu_workers = cpu_workers or max(1, os.cpu_count() - 1)
        self.gpu_workers = gpu_workers
        self.io_workers = io_workers
        
        # 创建线程池（改用线程池避免序列化问题）
        self.cpu_pool = ThreadPoolExecutor(max_workers=self.cpu_workers)
        self.gpu_pool = ThreadPoolExecutor(max_workers=self.gpu_workers)
        self.io_pool = ThreadPoolExecutor(max_workers=self.io_workers)
        
        self.stats = {
            'cpu_tasks': 0,
            'gpu_tasks': 0,
            'io_tasks': 0,
            'mixed_tasks': 0
        }
    
    def submit(self, task_type: TaskType, func: Callable, *args, **kwargs) -> Future:
        """
        提交任务
        
        Args:
            task_type: 任务类型
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            Future对象
        """
        if task_type == TaskType.CPU_INTENSIVE:
            self.stats['cpu_tasks'] += 1
            return self.cpu_pool.submit(func, *args, **kwargs)
        
        elif task_type == TaskType.GPU_INTENSIVE:
            self.stats['gpu_tasks'] += 1
            return self.gpu_pool.submit(func, *args, **kwargs)
        
        elif task_type == TaskType.IO_INTENSIVE:
            self.stats['io_tasks'] += 1
            return self.io_pool.submit(func, *args, **kwargs)
        
        else:  # MIXED
            self.stats['mixed_tasks'] += 1
            # 混合型任务使用CPU池
            return self.cpu_pool.submit(func, *args, **kwargs)
    
    def map(self, task_type: TaskType, func: Callable, items: List[Any]) -> List[Any]:
        """
        批量提交任务
        
        Args:
            task_type: 任务类型
            func: 要执行的函数
            items: 要处理的项目列表
        
        Returns:
            结果列表
        """
        futures = [self.submit(task_type, func, item) for item in items]
        return [f.result() for f in futures]
    
    def shutdown(self, wait: bool = True):
        """关闭调度器"""
        self.cpu_pool.shutdown(wait=wait)
        self.gpu_pool.shutdown(wait=wait)
        self.io_pool.shutdown(wait=wait)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            'cpu_workers': self.cpu_workers,
            'gpu_workers': self.gpu_workers,
            'io_workers': self.io_workers
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
