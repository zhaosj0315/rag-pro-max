"""
性能监控器 - 实时性能数据收集和分析
"""

import time
import psutil
import threading
from collections import deque
from datetime import datetime
from typing import Dict, List

class PerformanceMonitor:
    def __init__(self, history_size=100):
        self.history_size = history_size
        self.metrics = {
            'cpu': deque(maxlen=history_size),
            'memory': deque(maxlen=history_size),
            'disk': deque(maxlen=history_size),
            'timestamps': deque(maxlen=history_size)
        }
        self.query_stats = {
            'total_queries': 0,
            'avg_response_time': 0,
            'success_rate': 100,
            'recent_queries': deque(maxlen=50)
        }
        self.system_stats = {
            'uptime': time.time(),
            'peak_memory': 0,
            'peak_cpu': 0
        }
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval=5):
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self, interval):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # 记录数据
                timestamp = datetime.now()
                self.metrics['cpu'].append(cpu_percent)
                self.metrics['memory'].append(memory.percent)
                self.metrics['disk'].append(disk.percent)
                self.metrics['timestamps'].append(timestamp)
                
                # 更新峰值
                self.system_stats['peak_cpu'] = max(self.system_stats['peak_cpu'], cpu_percent)
                self.system_stats['peak_memory'] = max(self.system_stats['peak_memory'], memory.percent)
                
                time.sleep(interval)
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(interval)
    
    def record_query(self, query: str, response_time: float, success: bool):
        """记录查询性能"""
        self.query_stats['total_queries'] += 1
        
        # 记录查询详情
        query_record = {
            'query': query[:50] + "..." if len(query) > 50 else query,
            'response_time': response_time,
            'success': success,
            'timestamp': datetime.now()
        }
        self.query_stats['recent_queries'].append(query_record)
        
        # 更新平均响应时间
        recent_times = [q['response_time'] for q in self.query_stats['recent_queries'] if q['success']]
        if recent_times:
            self.query_stats['avg_response_time'] = sum(recent_times) / len(recent_times)
        
        # 更新成功率
        recent_success = [q['success'] for q in self.query_stats['recent_queries']]
        if recent_success:
            self.query_stats['success_rate'] = (sum(recent_success) / len(recent_success)) * 100
    
    def get_current_metrics(self) -> Dict:
        """获取当前性能指标"""
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': cpu,
                'memory': memory.percent,
                'disk': disk.percent,
                'memory_mb': memory.used / 1024 / 1024,
                'memory_total_mb': memory.total / 1024 / 1024,
                'disk_gb': disk.used / 1024 / 1024 / 1024,
                'disk_total_gb': disk.total / 1024 / 1024 / 1024
            }
        except:
            return {'cpu': 0, 'memory': 0, 'disk': 0, 'memory_mb': 0, 'memory_total_mb': 0, 'disk_gb': 0, 'disk_total_gb': 0}
    
    def get_history_data(self) -> Dict:
        """获取历史数据"""
        return {
            'cpu': list(self.metrics['cpu']),
            'memory': list(self.metrics['memory']),
            'disk': list(self.metrics['disk']),
            'timestamps': [t.strftime('%H:%M:%S') for t in self.metrics['timestamps']]
        }
    
    def get_query_stats(self) -> Dict:
        """获取查询统计"""
        return self.query_stats.copy()
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        uptime_seconds = time.time() - self.system_stats['uptime']
        uptime_hours = uptime_seconds / 3600
        
        return {
            'uptime_hours': uptime_hours,
            'peak_cpu': self.system_stats['peak_cpu'],
            'peak_memory': self.system_stats['peak_memory'],
            'cpu_count': psutil.cpu_count(),
            'total_memory_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024
        }
    
    def detect_bottlenecks(self) -> List[str]:
        """检测性能瓶颈"""
        bottlenecks = []
        current = self.get_current_metrics()
        
        if current['cpu'] > 90:
            bottlenecks.append("🔥 CPU使用率过高")
        elif current['cpu'] > 75:
            bottlenecks.append("⚠️ CPU使用率较高")
        
        if current['memory'] > 95:
            bottlenecks.append("🚨 内存即将耗尽")
        elif current['memory'] > 85:
            bottlenecks.append("⚠️ 内存使用率较高")
        
        if current['disk'] > 90:
            bottlenecks.append("💾 磁盘空间不足")
        
        if self.query_stats['avg_response_time'] > 10:
            bottlenecks.append("🐌 查询响应较慢")
        
        if self.query_stats['success_rate'] < 90:
            bottlenecks.append("❌ 查询成功率偏低")
        
        return bottlenecks
    
    def get_performance_score(self) -> int:
        """计算性能评分 (0-100)"""
        current = self.get_current_metrics()
        
        # CPU评分 (30%)
        cpu_score = max(0, 100 - current['cpu']) * 0.3
        
        # 内存评分 (30%)
        memory_score = max(0, 100 - current['memory']) * 0.3
        
        # 查询性能评分 (40%)
        response_score = min(100, max(0, 100 - self.query_stats['avg_response_time'] * 10)) * 0.2
        success_score = self.query_stats['success_rate'] * 0.2
        
        total_score = cpu_score + memory_score + response_score + success_score
        return int(total_score)

# 全局性能监控器
performance_monitor = PerformanceMonitor()
