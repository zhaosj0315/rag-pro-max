"""
自适应CPU调度器
基于历史性能数据和系统状态智能调整处理策略
"""

import json
import time
import psutil
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PerformanceRecord:
    """性能记录"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    workers: int
    pages_processed: int
    processing_time: float
    success_rate: float

class AdaptiveScheduler:
    """自适应CPU调度器"""
    
    def __init__(self):
        self.history_file = Path("config/performance_history.json")
        self.performance_history: List[PerformanceRecord] = []
        self.load_history()
        
        # 学习参数
        self.learning_rate = 0.1
        self.min_samples = 5
        self.max_history = 100
        
    def load_history(self):
        """加载历史性能数据"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.performance_history = [
                        PerformanceRecord(**record) for record in data
                    ]
            except Exception as e:
                print(f"⚠️  加载性能历史失败: {e}")
                self.performance_history = []
    
    def save_history(self):
        """保存性能历史"""
        try:
            self.history_file.parent.mkdir(exist_ok=True)
            data = [record.__dict__ for record in self.performance_history[-self.max_history:]]
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  保存性能历史失败: {e}")
    
    def record_performance(self, workers: int, pages: int, processing_time: float, success: bool):
        """记录性能数据"""
        try:
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            record = PerformanceRecord(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                workers=workers,
                pages_processed=pages,
                processing_time=processing_time,
                success_rate=1.0 if success else 0.0
            )
            
            self.performance_history.append(record)
            self.save_history()
            
        except Exception as e:
            print(f"⚠️  记录性能数据失败: {e}")
    
    def get_optimal_strategy(self, pages: int) -> Tuple[int, str, float]:
        """
        基于历史数据获取最优策略
        
        Returns:
            (workers, strategy_name, confidence)
        """
        current_cpu = psutil.cpu_percent(interval=0.1)
        current_memory = psutil.virtual_memory().percent
        
        # 如果历史数据不足，使用基础策略
        if len(self.performance_history) < self.min_samples:
            return self._get_basic_strategy(current_cpu, pages)
        
        # 分析历史数据
        best_strategy = self._analyze_history(current_cpu, current_memory, pages)
        
        return best_strategy
    
    def _get_basic_strategy(self, cpu_usage: float, pages: int) -> Tuple[int, str, float]:
        """基础策略（无历史数据时使用）"""
        if cpu_usage > 85:
            return 1, "基础保护模式", 0.5
        elif cpu_usage > 70:
            return 2, "基础保守模式", 0.6
        elif cpu_usage > 50:
            return 3, "基础平衡模式", 0.7
        else:
            return min(4, max(1, pages // 5)), "基础高效模式", 0.8
    
    def _analyze_history(self, cpu: float, memory: float, pages: int) -> Tuple[int, str, float]:
        """分析历史数据获取最优策略"""
        # 筛选相似条件的历史记录
        similar_records = []
        for record in self.performance_history[-50:]:  # 最近50条记录
            cpu_diff = abs(record.cpu_usage - cpu)
            memory_diff = abs(record.memory_usage - memory)
            pages_diff = abs(record.pages_processed - pages)
            
            # 相似度判断
            if cpu_diff < 20 and memory_diff < 20 and pages_diff < pages * 0.5:
                similar_records.append(record)
        
        if not similar_records:
            return self._get_basic_strategy(cpu, pages)
        
        # 计算不同worker数的平均性能
        worker_performance = {}
        for record in similar_records:
            workers = record.workers
            if workers not in worker_performance:
                worker_performance[workers] = []
            
            # 计算性能分数 (页数/时间 * 成功率 / CPU使用率)
            if record.processing_time > 0:
                score = (record.pages_processed / record.processing_time) * record.success_rate / (record.cpu_usage / 100)
                worker_performance[workers].append(score)
        
        # 选择平均性能最好的worker数
        best_workers = 1
        best_score = 0
        confidence = 0.5
        
        for workers, scores in worker_performance.items():
            if len(scores) >= 2:  # 至少2个样本
                avg_score = sum(scores) / len(scores)
                if avg_score > best_score:
                    best_score = avg_score
                    best_workers = workers
                    confidence = min(0.9, 0.5 + len(scores) * 0.1)
        
        strategy_name = f"学习优化模式(样本:{len(similar_records)})"
        
        return best_workers, strategy_name, confidence
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        if not self.performance_history:
            return {"message": "暂无性能数据"}
        
        recent_records = self.performance_history[-20:]
        
        avg_cpu = sum(r.cpu_usage for r in recent_records) / len(recent_records)
        avg_memory = sum(r.memory_usage for r in recent_records) / len(recent_records)
        avg_success = sum(r.success_rate for r in recent_records) / len(recent_records)
        
        # 计算平均处理速度
        total_pages = sum(r.pages_processed for r in recent_records)
        total_time = sum(r.processing_time for r in recent_records)
        avg_speed = total_pages / total_time if total_time > 0 else 0
        
        return {
            "总记录数": len(self.performance_history),
            "最近20次平均CPU": f"{avg_cpu:.1f}%",
            "最近20次平均内存": f"{avg_memory:.1f}%",
            "最近20次成功率": f"{avg_success:.1%}",
            "平均处理速度": f"{avg_speed:.2f}页/秒",
            "学习状态": "充分" if len(self.performance_history) >= 20 else "学习中"
        }

# 全局实例
adaptive_scheduler = AdaptiveScheduler()
