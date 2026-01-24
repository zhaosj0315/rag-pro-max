"""
并发性能监控
监控多进程多线程的性能表现
"""

import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TaskMetrics:
    """任务性能指标"""
    task_type: str
    start_time: float
    end_time: Optional[float] = None
    worker_count: int = 1
    task_count: int = 1
    success_count: int = 0
    error_count: int = 0
    executor_type: str = "thread"  # thread, process, serial
    
    @property
    def duration(self) -> float:
        """任务持续时间"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def throughput(self) -> float:
        """吞吐量（任务/秒）"""
        duration = self.duration
        if duration <= 0:
            return 0
        return self.success_count / duration
    
    @property
    def efficiency(self) -> float:
        """并发效率（实际加速比）"""
        if self.worker_count <= 1:
            return 1.0
        # 理论上N个worker应该有N倍加速，实际效率 = 实际吞吐量 / (单线程基准 * worker数)
        # 这里简化为成功率 * worker利用率的估算
        return min(1.0, self.success_count / (self.task_count * self.worker_count))


class ConcurrencyMonitor:
    """并发性能监控器"""
    
    def __init__(self):
        self.metrics: List[TaskMetrics] = []
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.lock = threading.Lock()
        self.stats = defaultdict(list)
    
    def start_task(self, task_id: str, task_type: str, worker_count: int, 
                   task_count: int, executor_type: str = "thread") -> TaskMetrics:
        """开始监控任务"""
        with self.lock:
            metric = TaskMetrics(
                task_type=task_type,
                start_time=time.time(),
                worker_count=worker_count,
                task_count=task_count,
                executor_type=executor_type
            )
            self.active_tasks[task_id] = metric
            return metric
    
    def finish_task(self, task_id: str, success_count: int, error_count: int):
        """完成任务监控"""
        with self.lock:
            if task_id in self.active_tasks:
                metric = self.active_tasks[task_id]
                metric.end_time = time.time()
                metric.success_count = success_count
                metric.error_count = error_count
                
                # 移到历史记录
                self.metrics.append(metric)
                del self.active_tasks[task_id]
                
                # 更新统计
                self.stats[metric.task_type].append(metric)
    
    def get_performance_summary(self) -> Dict[str, Dict]:
        """获取性能摘要"""
        with self.lock:
            summary = {}
            
            for task_type, metrics_list in self.stats.items():
                if not metrics_list:
                    continue
                
                # 计算平均指标
                avg_duration = sum(m.duration for m in metrics_list) / len(metrics_list)
                avg_throughput = sum(m.throughput for m in metrics_list) / len(metrics_list)
                avg_efficiency = sum(m.efficiency for m in metrics_list) / len(metrics_list)
                
                # 并发vs串行对比
                parallel_metrics = [m for m in metrics_list if m.worker_count > 1]
                serial_metrics = [m for m in metrics_list if m.worker_count == 1]
                
                speedup = 1.0
                if serial_metrics and parallel_metrics:
                    avg_serial_time = sum(m.duration for m in serial_metrics) / len(serial_metrics)
                    avg_parallel_time = sum(m.duration for m in parallel_metrics) / len(parallel_metrics)
                    if avg_parallel_time > 0:
                        speedup = avg_serial_time / avg_parallel_time
                
                summary[task_type] = {
                    'total_tasks': len(metrics_list),
                    'avg_duration': avg_duration,
                    'avg_throughput': avg_throughput,
                    'avg_efficiency': avg_efficiency,
                    'speedup': speedup,
                    'parallel_tasks': len(parallel_metrics),
                    'serial_tasks': len(serial_metrics)
                }
            
            return summary
    
    def get_recommendations(self) -> List[str]:
        """获取性能优化建议"""
        summary = self.get_performance_summary()
        recommendations = []
        
        for task_type, stats in summary.items():
            if stats['avg_efficiency'] < 0.5:
                recommendations.append(f"⚠️ {task_type}: 并发效率低({stats['avg_efficiency']:.1%})，建议减少worker数量")
            
            if stats['speedup'] < 1.2 and stats['parallel_tasks'] > 0:
                recommendations.append(f"💡 {task_type}: 并行加速比低({stats['speedup']:.1f}x)，考虑串行处理")
            
            if stats['avg_throughput'] < 1.0:
                recommendations.append(f"🐌 {task_type}: 吞吐量低({stats['avg_throughput']:.1f}/s)，检查任务复杂度")
        
        if not recommendations:
            recommendations.append("✅ 并发性能良好，无需优化")
        
        return recommendations


# 全局监控器实例
_monitor = None

def get_monitor() -> ConcurrencyMonitor:
    """获取全局并发监控器"""
    global _monitor
    if _monitor is None:
        _monitor = ConcurrencyMonitor()
    return _monitor
