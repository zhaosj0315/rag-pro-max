"""
自适应限流管理器 - Adaptive Throttling Manager
分级限流 + 内存泄漏检测 + 动态工作线程调整
"""

import psutil
import logging
import numpy as np
from typing import Dict, List
from collections import deque
import gc
import torch

logger = logging.getLogger(__name__)


class AdaptiveThrottling:
    """自适应限流管理器"""
    
    # 限流等级定义
    THROTTLE_LEVELS = {
        0: {'name': '正常', 'threshold': 70, 'actions': []},
        1: {'name': '预警', 'threshold': 80, 'actions': ['log_warning']},
        2: {'name': '限流', 'threshold': 90, 'actions': ['reduce_batch', 'reduce_workers']},
        3: {'name': '停止', 'threshold': 100, 'actions': ['pause_tasks']},
    }
    
    def __init__(self, history_size: int = 20):
        self.throttle_level = 0
        self.history_size = history_size
        self.memory_history = deque(maxlen=history_size)
        self.cpu_history = deque(maxlen=history_size)
        self.gpu_history = deque(maxlen=history_size)
        self.warning_sent = False
        self.leak_detected = False
    
    def check_and_throttle(self, cpu: float, mem: float, gpu: float) -> Dict:
        """
        检查资源并返回限流动作
        
        Args:
            cpu: CPU占用率 (0-100)
            mem: 内存占用率 (0-100)
            gpu: GPU占用率 (0-100)
        
        Returns:
            限流动作字典
        """
        # 记录历史
        self.memory_history.append(mem)
        self.cpu_history.append(cpu)
        self.gpu_history.append(gpu)
        
        # 获取最大占用率
        max_usage = max(cpu, mem, gpu)
        
        # 确定限流等级
        old_level = self.throttle_level
        for level in range(4):
            if max_usage < self.THROTTLE_LEVELS[level]['threshold']:
                self.throttle_level = level
                break
        
        # 生成动作
        actions = self._get_actions(self.throttle_level, old_level)
        
        # 检测内存泄漏
        if len(self.memory_history) >= self.history_size:
            if self._detect_memory_leak():
                actions['cleanup_memory'] = True
        
        return {
            'throttle_level': self.throttle_level,
            'level_name': self.THROTTLE_LEVELS[self.throttle_level]['name'],
            'max_usage': max_usage,
            'cpu': cpu,
            'mem': mem,
            'gpu': gpu,
            'actions': actions
        }
    
    def _get_actions(self, current_level: int, old_level: int) -> Dict:
        """获取限流动作"""
        actions = {}
        
        # 等级上升时执行动作
        if current_level > old_level:
            for level in range(old_level + 1, current_level + 1):
                for action in self.THROTTLE_LEVELS[level]['actions']:
                    actions[action] = True
        
        # 等级下降时恢复
        if current_level < old_level:
            actions['recover'] = True
        
        return actions
    
    def _detect_memory_leak(self) -> bool:
        """
        检测内存泄漏
        
        Returns:
            bool: 是否检测到泄漏
        """
        if len(self.memory_history) < 10:
            return False
        
        # 计算最近10个数据点的趋势
        recent = list(self.memory_history)[-10:]
        x = np.arange(len(recent))
        
        try:
            # 拟合直线，获取斜率
            coeffs = np.polyfit(x, recent, 1)
            slope = coeffs[0]
            
            # 如果斜率 > 0.5（内存持续增长），可能泄漏
            if slope > 0.5:
                if not self.leak_detected:
                    logger.warning(f"检测到内存泄漏：内存增长趋势 {slope:.2f}%/次")
                    self.leak_detected = True
                return True
            else:
                self.leak_detected = False
                return False
        except:
            return False
    
    def cleanup_memory(self):
        """清理内存"""
        try:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("内存清理完成")
        except Exception as e:
            logger.error(f"内存清理失败: {e}")
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            'throttle_level': self.throttle_level,
            'level_name': self.THROTTLE_LEVELS[self.throttle_level]['name'],
            'memory_trend': self._calculate_trend(self.memory_history),
            'cpu_trend': self._calculate_trend(self.cpu_history),
            'gpu_trend': self._calculate_trend(self.gpu_history),
            'leak_detected': self.leak_detected,
        }
    
    @staticmethod
    def _calculate_trend(history: deque) -> float:
        """计算趋势（斜率）"""
        if len(history) < 2:
            return 0.0
        
        try:
            recent = list(history)[-10:] if len(history) >= 10 else list(history)
            x = np.arange(len(recent))
            coeffs = np.polyfit(x, recent, 1)
            return float(coeffs[0])
        except:
            return 0.0


class DynamicWorkerAdjuster:
    """动态工作线程调整器"""
    
    def __init__(self, min_workers: int = 2, max_workers: int = 20):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        self.queue_history = deque(maxlen=10)
    
    def adjust_workers(self, queue_size: int) -> int:
        """
        根据队列大小调整工作线程
        
        Args:
            queue_size: 当前队列大小
        
        Returns:
            新的工作线程数
        """
        self.queue_history.append(queue_size)
        
        # 计算平均队列大小
        avg_queue = np.mean(list(self.queue_history))
        
        # 根据队列大小调整
        if avg_queue > 10:
            # 队列堆积，增加工作线程
            new_workers = min(self.current_workers + 2, self.max_workers)
        elif avg_queue < 2:
            # 队列空闲，减少工作线程
            new_workers = max(self.current_workers - 1, self.min_workers)
        else:
            # 队列正常，保持不变
            new_workers = self.current_workers
        
        if new_workers != self.current_workers:
            logger.info(f"工作线程调整: {self.current_workers} → {new_workers} (队列大小: {queue_size})")
            self.current_workers = new_workers
        
        return new_workers
    
    def get_current_workers(self) -> int:
        """获取当前工作线程数"""
        return self.current_workers


class ResourceGuard:
    """资源保护器 - 综合管理限流和工作线程"""
    
    def __init__(self):
        self.throttler = AdaptiveThrottling()
        self.adjusters = {
            'cpu': DynamicWorkerAdjuster(min_workers=2, max_workers=16),
            'gpu': DynamicWorkerAdjuster(min_workers=1, max_workers=8),
            'io': DynamicWorkerAdjuster(min_workers=5, max_workers=30),
        }
    
    def check_resources(self, cpu: float, mem: float, gpu: float,
                       queue_sizes: Dict[str, int] = None) -> Dict:
        """
        检查资源并返回完整的管理建议
        
        Args:
            cpu: CPU占用率
            mem: 内存占用率
            gpu: GPU占用率
            queue_sizes: 各类型队列大小
        
        Returns:
            管理建议字典
        """
        # 检查限流
        throttle_info = self.throttler.check_and_throttle(cpu, mem, gpu)
        
        # 调整工作线程
        worker_adjustments = {}
        if queue_sizes:
            for task_type, queue_size in queue_sizes.items():
                if task_type in self.adjusters:
                    new_workers = self.adjusters[task_type].adjust_workers(queue_size)
                    worker_adjustments[task_type] = new_workers
        
        return {
            'throttle': throttle_info,
            'workers': worker_adjustments,
            'status': self.throttler.get_status(),
        }
    
    def should_pause_new_tasks(self) -> bool:
        """是否应该暂停新任务"""
        return self.throttler.throttle_level >= 3
    
    def should_reduce_batch(self) -> bool:
        """是否应该减少batch size"""
        return self.throttler.throttle_level >= 2
    
    def should_reduce_workers(self) -> bool:
        """是否应该减少工作线程"""
        return self.throttler.throttle_level >= 2


# 全局实例
_resource_guard = None


def get_resource_guard() -> ResourceGuard:
    """获取全局资源保护器"""
    global _resource_guard
    if _resource_guard is None:
        _resource_guard = ResourceGuard()
    return _resource_guard
