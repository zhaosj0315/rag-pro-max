"""
智能资源调度器
基于历史数据和实时状态优化资源分配
"""

import json
import os
import time
import psutil
from datetime import datetime
from typing import Dict, List
from enum import Enum
import logging  # 允许使用 - 智能调度专用

class TaskType(Enum):
    """任务类型枚举"""
    CPU_INTENSIVE = "cpu_intensive"
    GPU_INTENSIVE = "gpu_intensive" 
    IO_INTENSIVE = "io_intensive"
    GENERAL = "general"

class SmartScheduler:
    def __init__(self):
        self.history_file = "config/scheduler_history.json"
        self.config_file = "config/scheduler_config.json"
        self.max_history = 200
        self.learning_rate = 0.1
        
        # 默认配置
        self.default_config = {
            'cpu_thresholds': {'low': 40, 'medium': 75, 'high': 92},
            'memory_thresholds': {'low': 40, 'medium': 75, 'high': 90},
            'worker_configs': {
                'low_load': {'cpu_workers': 10, 'io_workers': 5},
                'medium_load': {'cpu_workers': 6, 'io_workers': 3},
                'high_load': {'cpu_workers': 4, 'io_workers': 2}
            },
            'adaptive_enabled': True,
            'learning_enabled': True
        }
        
        self.load_config()
    
    def load_config(self):
        """加载调度配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """保存调度配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_system_load(self) -> Dict:
        """获取系统负载"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        # 分类负载等级
        cpu_level = self._classify_load(cpu_percent, self.config['cpu_thresholds'])
        memory_level = self._classify_load(memory_percent, self.config['memory_thresholds'])
        
        # 综合负载等级（取较高者）
        load_levels = ['low', 'medium', 'high']
        cpu_idx = load_levels.index(cpu_level) if cpu_level in load_levels else 1
        memory_idx = load_levels.index(memory_level) if memory_level in load_levels else 1
        overall_level = load_levels[max(cpu_idx, memory_idx)]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'cpu_level': cpu_level,
            'memory_level': memory_level,
            'overall_level': overall_level
        }
    
    def _classify_load(self, value: float, thresholds: Dict) -> str:
        """分类负载等级"""
        if value < thresholds['low']:
            return 'low'
        elif value < thresholds['medium']:
            return 'medium'
        else:
            return 'high'
    
    def get_optimal_workers(self, task_type: str = 'general') -> Dict:
        """获取最优工作线程配置"""
        load = self.get_system_load()
        level = load['overall_level']
        
        # 映射负载等级到配置键
        level_mapping = {
            'low': 'low_load',
            'medium': 'medium_load', 
            'high': 'high_load'
        }
        
        config_key = level_mapping.get(level, 'medium_load')
        base_config = self.config['worker_configs'][config_key].copy()
        
        # 如果启用自适应学习
        if self.config['adaptive_enabled']:
            base_config = self._apply_adaptive_adjustment(base_config, load, task_type)
        
        # 记录决策历史
        self._record_decision(load, base_config, task_type)
        
        return {
            'cpu_workers': base_config['cpu_workers'],
            'io_workers': base_config['io_workers'],
            'load_level': level,
            'reasoning': f"系统负载: {level}, CPU: {load['cpu_percent']:.1f}%, 内存: {load['memory_percent']:.1f}%"
        }
    
    def _apply_adaptive_adjustment(self, base_config: Dict, load: Dict, task_type: str) -> Dict:
        """应用自适应调整"""
        if not self.config['learning_enabled']:
            return base_config
        
        # 基于历史性能调整
        history = self._load_history()
        if len(history) < 10:  # 历史数据不足
            return base_config
        
        # 分析相似场景的历史表现
        similar_scenarios = [
            h for h in history[-50:] 
            if abs(h['load']['cpu_percent'] - load['cpu_percent']) < 10
            and abs(h['load']['memory_percent'] - load['memory_percent']) < 10
            and h.get('task_type') == task_type
        ]
        
        if len(similar_scenarios) < 3:
            return base_config
        
        # 计算平均性能
        avg_performance = sum(s.get('performance_score', 0.5) for s in similar_scenarios) / len(similar_scenarios)
        
        # 如果历史性能不佳，调整配置
        if avg_performance < 0.6:
            base_config['cpu_workers'] = max(1, int(base_config['cpu_workers'] * 0.8))
            base_config['io_workers'] = max(1, int(base_config['io_workers'] * 0.8))
        elif avg_performance > 0.8:
            base_config['cpu_workers'] = min(12, int(base_config['cpu_workers'] * 1.2))
            base_config['io_workers'] = min(6, int(base_config['io_workers'] * 1.2))
        
        return base_config
    
    def _record_decision(self, load: Dict, config: Dict, task_type: str):
        """记录调度决策"""
        decision = {
            'timestamp': datetime.now().isoformat(),
            'load': load,
            'config': config,
            'task_type': task_type
        }
        
        history = self._load_history()
        history.append(decision)
        
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        
        self._save_history(history)
    
    def record_performance(self, task_type: str, duration: float, success: bool, cpu_usage: float = None):
        """记录任务性能"""
        self.history.append({
            'task_type': task_type,
            'duration': duration,
            'success': success,
            'cpu_usage': cpu_usage,
            'timestamp': time.time()
        })
        
        # 限制历史记录数量
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
            
        # 自动保存
        if len(self.history) % 10 == 0:
            self.save_history()

    def shutdown(self):
        """关闭调度器并释放资源"""
        try:
            self.save_config()
        except:
            pass
    
    def _load_history(self) -> List:
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self, history: List):
        """保存历史记录"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(history, f)
    
    def get_recommendations(self) -> Dict:
        """获取优化建议"""
        load = self.get_system_load()
        history = self._load_history()
        
        recommendations = []
        
        # 基于当前负载的建议
        if load['cpu_percent'] > 85:
            recommendations.append("⚠️ CPU使用率过高，建议减少并行任务")
        elif load['cpu_percent'] < 20:
            recommendations.append("💡 CPU使用率较低，可以增加并行度")
        
        if load['memory_percent'] > 90:
            recommendations.append("🚨 内存使用率危险，建议立即清理缓存")
        elif load['memory_percent'] > 80:
            recommendations.append("⚠️ 内存使用率较高，建议减少内存密集型任务")
        
        # 基于历史数据的建议
        if len(history) > 20:
            recent_performance = [h.get('performance_score', 0.5) for h in history[-20:]]
            avg_performance = sum(recent_performance) / len(recent_performance)
            
            if avg_performance < 0.5:
                recommendations.append("📉 最近性能表现不佳，建议检查系统配置")
            elif avg_performance > 0.8:
                recommendations.append("📈 系统性能良好，当前配置较为合适")
        
        return {
            'current_load': load,
            'recommendations': recommendations,
            'optimal_config': self.get_optimal_workers()
        }

# 全局调度器实例
_scheduler = None

def get_smart_scheduler() -> SmartScheduler:
    """获取智能调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SmartScheduler()
    return _scheduler
