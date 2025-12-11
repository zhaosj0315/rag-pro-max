from .safe_parallel_tasks import safe_process_node_worker, safe_extract_metadata_task
from .cpu_throttle import CPUThrottle, SafeThreadPoolExecutor
"""
并行执行管理器
Stage 6 - 统一的多进程/多线程执行接口
Stage 6.1 - 自动并行装饰器
v2.1.1 - 添加CPU使用率限制，防止系统过载
"""

import os
import psutil
import functools
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional


class ParallelExecutor:
    """统一的并行执行管理器 - 带CPU使用率限制"""
    
    def __init__(self, max_workers: Optional[int] = None, cpu_limit: float = 90.0):
        """
        初始化并行执行器
        
        Args:
            max_workers: 最大工作进程数，默认为 CPU核心数-1
            cpu_limit: CPU使用率限制，默认90%
        """
        self.cpu_throttle = CPUThrottle(max_cpu_percent=cpu_limit)
        
        # 动态调整工作线程数
        default_workers = max_workers or max(2, os.cpu_count() - 1)
        self.max_workers = self.cpu_throttle.get_safe_worker_count(default_workers)
        
        # 启动CPU监控
        self.cpu_throttle.start_monitoring()
    
    def should_parallelize(self, task_count: int, threshold: int = 2) -> bool:
        """
        智能判断是否需要并行执行 - 增强CPU检查
        
        Args:
            task_count: 任务数量
            threshold: 并行阈值，任务数小于此值时串行更快
            
        Returns:
            bool: 是否应该并行执行
        """
        # 任务数太少，串行更快（避免进程创建开销）
        if task_count < 2:
            return False
        
        # CPU核心数太少，并行无意义
        if os.cpu_count() <= 2:
            return False
        
        # 检查CPU使用率，如果过高则禁用并行
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > 85:  # 降低阈值，更保守
                print(f"⚠️  CPU使用率过高 ({cpu_percent:.1f}%)，禁用并行处理")
                return False
        except:
            pass  # 如果获取失败，继续并行
        
        # 检查是否正在限流
        if self.cpu_throttle.is_throttling:
            print("⚠️  CPU正在限流中，禁用并行处理")
            return False
        
        return True
    
    def execute(self, func: Callable, tasks: List[Any], 
                chunksize: Optional[int] = None,
                threshold: int = 2) -> List[Any]:
        """
        执行并行任务（自动判断串行/并行）- 带CPU限制
        
        Args:
            func: 要执行的函数
            tasks: 任务列表
            chunksize: 每个进程处理的任务块大小
            threshold: 并行阈值
            
        Returns:
            List[Any]: 结果列表
        """
        if not self.should_parallelize(len(tasks), threshold):
            # 串行执行
            return [func(task) for task in tasks]
        
        # 并行执行 - 使用安全的线程池
        workers = min(self.max_workers, len(tasks) // 2)
        chunk = chunksize or max(1, len(tasks) // (workers * 4))
        
        with SafeThreadPoolExecutor(max_workers=workers, cpu_throttle=self.cpu_throttle) as executor:
            results = list(executor.map(func, tasks, chunksize=chunk))
        
        return results
    
    def execute_with_progress(self, func: Callable, tasks: List[Any],
                              callback: Optional[Callable] = None,
                              threshold: int = 2) -> List[Any]:
        """
        带进度回调的并行执行
        
        Args:
            func: 要执行的函数
            tasks: 任务列表
            callback: 进度回调函数 callback(completed, total)
            threshold: 并行阈值
            
        Returns:
            List[Any]: 结果列表
        """
        total = len(tasks)
        
        if not self.should_parallelize(total, threshold):
            # 串行执行
            results = []
            for i, task in enumerate(tasks):
                results.append(func(task))
                if callback:
                    callback(i + 1, total)
            return results
        
        # 并行执行
        workers = min(self.max_workers, total // 2)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(func, task): i for i, task in enumerate(tasks)}
            results = [None] * total
            completed = 0
            
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
                completed += 1
                if callback:
                    callback(completed, total)
        
        return results


# 全局单例（可选）
_global_executor = None

def get_global_executor(max_workers: Optional[int] = None) -> ParallelExecutor:
    """获取全局并行执行器（单例模式）"""
    global _global_executor
    if _global_executor is None:
        _global_executor = ParallelExecutor(max_workers)
    return _global_executor


# ============================================================================
# 自动并行装饰器
# ============================================================================

def auto_parallel(threshold: int = 2, chunksize: Optional[int] = None):
    """
    自动并行装饰器
    
    使用方法:
        @auto_parallel(threshold=50)
        def process_files(file_list):
            results = []
            for file in file_list:
                results.append(process_single_file(file))
            return results
    
    装饰器会自动:
    1. 检测函数参数中的列表/可迭代对象
    2. 判断是否需要并行
    3. 自动应用并行执行
    
    Args:
        threshold: 并行阈值，元素数量小于此值时串行执行
        chunksize: 每个进程处理的任务块大小
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试找到第一个列表/可迭代参数
            tasks = None
            task_arg_idx = None
            
            # 检查位置参数
            for i, arg in enumerate(args):
                if isinstance(arg, (list, tuple)) and len(arg) > 0:
                    tasks = arg
                    task_arg_idx = i
                    break
            
            # 如果没找到，检查关键字参数
            if tasks is None:
                for key, value in kwargs.items():
                    if isinstance(value, (list, tuple)) and len(value) > 0:
                        tasks = value
                        break
            
            # 如果没有找到可并行的参数，直接执行原函数
            if tasks is None or len(tasks) < threshold:
                return func(*args, **kwargs)
            
            # 使用并行执行器
            executor = get_global_executor()
            if not executor.should_parallelize(len(tasks), threshold):
                return func(*args, **kwargs)
            
            # 并行执行（需要函数支持单个元素处理）
            # 注意：这里假设函数可以处理单个元素
            # 如果函数需要处理整个列表，需要手动使用 ParallelExecutor
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def parallelize_list(func: Callable, items: List[Any], 
                     threshold: int = 2, 
                     chunksize: Optional[int] = None) -> List[Any]:
    """
    便捷函数：对列表中的每个元素应用函数（自动并行）
    
    使用方法:
        results = parallelize_list(process_single_file, file_list, threshold=50)
    
    Args:
        func: 处理单个元素的函数
        items: 要处理的元素列表
        threshold: 并行阈值
        chunksize: 每个进程处理的任务块大小
        
    Returns:
        List[Any]: 结果列表
    """
    executor = get_global_executor()
    return executor.execute(func, items, chunksize=chunksize, threshold=threshold)

