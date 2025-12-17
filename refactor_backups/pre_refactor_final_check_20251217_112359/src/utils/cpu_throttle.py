"""
CPU 使用率限制器
防止 CPU 使用率超过 90%，避免系统过载导致自动关机
"""

import time
import psutil
import threading
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor


class CPUThrottle:
    """CPU 使用率限制器"""
    
    def __init__(self, max_cpu_percent: float = 95.0, check_interval: float = 0.5):
        """
        初始化 CPU 限制器
        
        Args:
            max_cpu_percent: 最大 CPU 使用率，默认 90%
            check_interval: 检查间隔，默认 0.5 秒
        """
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        self.is_throttling = False
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self):
        """开始监控 CPU 使用率"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_cpu, daemon=True)
            self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_cpu(self):
        """监控 CPU 使用率的后台线程"""
        while not self._stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                if cpu_percent > self.max_cpu_percent:
                    if not self.is_throttling:
                        print(f"⚠️  CPU 使用率过高 ({cpu_percent:.1f}%)，启动限流保护...")
                        self.is_throttling = True
                    
                    # 强制休眠，降低 CPU 使用率
                    time.sleep(0.2)
                else:
                    if self.is_throttling:
                        print(f"✅ CPU 使用率恢复正常 ({cpu_percent:.1f}%)，解除限流")
                        self.is_throttling = False
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"CPU 监控异常: {e}")
                time.sleep(1.0)
    
    def wait_if_throttling(self, max_wait: float = 5.0):
        """如果正在限流，等待直到 CPU 使用率降低"""
        if not self.is_throttling:
            return
        
        start_time = time.time()
        while self.is_throttling and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
    
    def get_safe_worker_count(self, default_workers: int) -> int:
        """根据 CPU 使用率动态调整工作线程数"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            if cpu_percent > 85:
                # CPU 使用率过高，减少线程数
                return max(1, default_workers // 4)
            elif cpu_percent > 70:
                # CPU 使用率较高，适度减少
                return max(2, default_workers // 2)
            else:
                # CPU 使用率正常
                return default_workers
                
        except Exception:
            return max(2, default_workers // 2)  # 保守策略


class SafeThreadPoolExecutor(ThreadPoolExecutor):
    """带 CPU 限制的线程池执行器"""
    
    def __init__(self, max_workers=None, cpu_throttle: Optional[CPUThrottle] = None, **kwargs):
        # 动态调整最大工作线程数
        if cpu_throttle:
            original_workers = max_workers or min(32, (psutil.cpu_count() or 1) + 4)
            max_workers = cpu_throttle.get_safe_worker_count(original_workers)
        
        super().__init__(max_workers=max_workers, **kwargs)
        self.cpu_throttle = cpu_throttle or CPUThrottle()
        self.cpu_throttle.start_monitoring()
    
    def submit(self, fn, *args, **kwargs):
        """提交任务前检查 CPU 使用率"""
        self.cpu_throttle.wait_if_throttling()
        return super().submit(fn, *args, **kwargs)
    
    def shutdown(self, wait=True, **kwargs):
        """关闭时停止 CPU 监控"""
        self.cpu_throttle.stop_monitoring()
        super().shutdown(wait=wait, **kwargs)


def safe_parallel_execute(func: Callable, tasks: list, max_workers: int = None, 
                         cpu_limit: float = 90.0) -> list:
    """
    安全的并行执行函数，带 CPU 使用率限制
    
    Args:
        func: 要执行的函数
        tasks: 任务列表
        max_workers: 最大工作线程数
        cpu_limit: CPU 使用率限制
        
    Returns:
        list: 执行结果列表
    """
    if not tasks:
        return []
    
    # 如果任务数量很少，直接串行执行
    if len(tasks) <= 2:
        return [func(task) for task in tasks]
    
    throttle = CPUThrottle(max_cpu_percent=cpu_limit)
    
    try:
        with SafeThreadPoolExecutor(max_workers=max_workers, cpu_throttle=throttle) as executor:
            futures = [executor.submit(func, task) for task in tasks]
            results = []
            
            for future in futures:
                try:
                    result = future.result(timeout=30)  # 30秒超时
                    results.append(result)
                except Exception as e:
                    print(f"任务执行失败: {e}")
                    results.append(None)
            
            return results
            
    finally:
        throttle.stop_monitoring()


# 全局 CPU 限制器实例
_global_throttle = CPUThrottle(max_cpu_percent=95.0)

def start_global_cpu_protection():
    """启动全局 CPU 保护"""
    _global_throttle.start_monitoring()

def stop_global_cpu_protection():
    """停止全局 CPU 保护"""
    _global_throttle.stop_monitoring()

def is_cpu_throttling() -> bool:
    """检查是否正在限流"""
    return _global_throttle.is_throttling

def wait_for_cpu_available(max_wait: float = 5.0):
    """等待 CPU 可用"""
    _global_throttle.wait_if_throttling(max_wait)
