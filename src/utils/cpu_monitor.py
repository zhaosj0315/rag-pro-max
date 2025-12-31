"""
CPU使用率监控和限制工具
确保系统资源不超过95%
"""

import psutil
import time
import threading
from typing import Optional, Callable
import logging  # 允许使用 - CPU监控专用
from src.app_logging.log_manager import LogManager

class CPUMonitor:
    """CPU使用率监控器"""
    
    def __init__(self, max_cpu_percent: float = 75.0, check_interval: float = 1.0):
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        
    def add_callback(self, callback: Callable[[float], None]):
        """添加CPU使用率变化回调"""
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=self.check_interval)
                
                # 调用回调函数
                for callback in self.callbacks:
                    try:
                        callback(cpu_percent)
                    except Exception as e:
                        logging.error(f"CPU监控回调错误: {e}")
                
                # 如果CPU使用率过高，记录警告
                if cpu_percent > self.max_cpu_percent:
                    logging.warning(f"CPU使用率过高: {cpu_percent:.1f}%")
                    
            except Exception as e:
                logging.error(f"CPU监控错误: {e}")
                time.sleep(1)
    
    def get_current_cpu(self) -> float:
        """获取当前CPU使用率"""
        return psutil.cpu_percent(interval=0.1)
    
    def is_cpu_high(self) -> bool:
        """检查CPU使用率是否过高"""
        return self.get_current_cpu() > self.max_cpu_percent
    
    def wait_for_cpu_available(self, max_wait: float = 10.0) -> bool:
        """等待CPU使用率降低"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if not self.is_cpu_high():
                return True
            time.sleep(0.5)
        
        return False

class ResourceLimiter:
    """资源限制器"""
    
    def __init__(self, max_cpu_percent: float = 75.0, max_memory_percent: float = 85.0):
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.cpu_monitor = CPUMonitor(max_cpu_percent)
        
    def check_resources(self) -> dict:
        """检查系统资源"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'cpu_high': cpu_percent > self.max_cpu_percent,
            'memory_high': memory.percent > self.max_memory_percent
        }
    
    def get_safe_worker_count(self, default_workers: int) -> int:
        """根据CPU使用率获取安全的工作线程数"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        # 综合考虑CPU和内存使用率
        max_usage = max(cpu_percent, memory_percent)
        
        if max_usage > 70:
            return max(1, default_workers // 4)  # 高负载时减少到1/4
        elif max_usage > 60:
            return max(2, default_workers // 2)  # 中等负载时减少到1/2
        elif max_usage > 50:
            return max(3, default_workers * 3 // 4)  # 轻微负载时减少到3/4
        else:
            return default_workers  # 低负载时使用默认值
    
    def should_throttle(self) -> bool:
        """是否应该限流"""
        resources = self.check_resources()
        return resources['cpu_high'] or resources['memory_high']
    
    def wait_if_needed(self, max_wait: float = 5.0):
        """如果需要则等待资源可用"""
        if self.should_throttle():
            print(f"⚠️ 系统资源紧张，等待资源释放...")
            self.cpu_monitor.wait_for_cpu_available(max_wait)

# 全局资源限制器
_resource_limiter = None

def get_resource_limiter(max_cpu_percent: float = 75.0, max_memory_percent: float = 85.0) -> ResourceLimiter:
    """获取资源限制器实例"""
    global _resource_limiter
    if _resource_limiter is None:
        _resource_limiter = ResourceLimiter(max_cpu_percent, max_memory_percent)
    return _resource_limiter

def check_system_resources() -> dict:
    """检查系统资源状态"""
    limiter = get_resource_limiter()
    return limiter.check_resources()

def get_safe_worker_count(default_workers: int, max_cpu_percent: float = 75.0) -> int:
    """获取安全的工作线程数"""
    limiter = get_resource_limiter(max_cpu_percent)
    return limiter.get_safe_worker_count(default_workers)
