#!/usr/bin/env python3
"""
统一监控日志组件
整合系统监控、日志记录、性能追踪功能
"""

import streamlit as st
import psutil
import time
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

class UnifiedMonitoringSystem:
    """统一监控系统"""
    
    def __init__(self, log_dir: str = "app_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 监控配置
        self.update_interval = 2.0  # 秒
        self.history_limit = 100
        self.last_update = 0
        
        # 性能历史
        self.performance_history = []
        
    def render_monitoring_dashboard(self, show_detailed: bool = True) -> None:
        """渲染统一监控仪表板"""
        st.markdown("##### 📊 系统监控")
        
        # 实时系统状态
        self._render_realtime_metrics()
        
        if show_detailed:
            # 详细监控信息
            col1, col2 = st.columns(2)
            
            with col1:
                self._render_performance_chart()
            
            with col2:
                self._render_system_info()
            
            # 日志查看器
            self._render_log_viewer()
    
    def _render_realtime_metrics(self):
        """渲染实时指标"""
        # 获取系统指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 显示指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🖥️ CPU",
                f"{cpu_percent:.1f}%",
                delta=self._get_cpu_delta()
            )
        
        with col2:
            st.metric(
                "💾 内存",
                f"{memory.percent:.1f}%",
                delta=f"{memory.used / 1024**3:.1f}GB"
            )
        
        with col3:
            st.metric(
                "💿 磁盘",
                f"{disk.percent:.1f}%",
                delta=f"{disk.free / 1024**3:.1f}GB 可用"
            )
        
        with col4:
            # GPU使用率 (如果可用)
            gpu_usage = self._get_gpu_usage()
            st.metric(
                "🎮 GPU",
                f"{gpu_usage:.1f}%" if gpu_usage > 0 else "N/A",
                delta=None
            )
        
        # 保存性能历史
        self._save_performance_data({
            'timestamp': datetime.now().isoformat(),
            'cpu': cpu_percent,
            'memory': memory.percent,
            'disk': disk.percent,
            'gpu': gpu_usage
        })
    
    def _render_performance_chart(self):
        """渲染性能图表"""
        st.write("**📈 性能趋势**")
        
        if len(self.performance_history) > 1:
            # 使用Streamlit的图表功能
            import pandas as pd
            
            df = pd.DataFrame(self.performance_history[-20:])  # 最近20个数据点
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            st.line_chart(df.set_index('timestamp')[['cpu', 'memory', 'disk']])
        else:
            st.info("收集性能数据中...")
    
    def _render_system_info(self):
        """渲染系统信息"""
        st.write("**🔧 系统信息**")
        
        # 基本系统信息
        info = {
            "CPU核心": psutil.cpu_count(),
            "总内存": f"{psutil.virtual_memory().total / 1024**3:.1f}GB",
            "Python版本": f"{psutil.PYTHON_VERSION}",
            "启动时间": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for key, value in info.items():
            st.write(f"• **{key}**: {value}")
    
    def _render_log_viewer(self):
        """渲染紧凑的日志查看器"""
        from src.utils.compact_log_display import compact_log_display
        
        # 使用紧凑日志显示组件
        compact_log_display.render_compact_logs()
    
    def _get_cpu_delta(self) -> Optional[str]:
        """获取CPU使用率变化"""
        if len(self.performance_history) >= 2:
            current = self.performance_history[-1]['cpu']
            previous = self.performance_history[-2]['cpu']
            delta = current - previous
            return f"{delta:+.1f}%" if abs(delta) > 0.1 else None
        return None
    
    def _get_gpu_usage(self) -> float:
        """获取GPU使用率"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].load * 100
        except ImportError:
            pass
        
        # 尝试nvidia-smi
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        
        return 0.0
    
    def _save_performance_data(self, data: Dict[str, Any]):
        """保存性能数据"""
        self.performance_history.append(data)
        
        # 限制历史记录数量
        if len(self.performance_history) > self.history_limit:
            self.performance_history = self.performance_history[-self.history_limit:]
        
        # 定期保存到文件
        if len(self.performance_history) % 10 == 0:
            self._save_performance_to_file()
    
    def _save_performance_to_file(self):
        """保存性能数据到文件"""
        try:
            perf_file = self.log_dir / "performance_history.json"
            with open(perf_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2)
        except Exception:
            pass  # 静默失败
    
    def _read_log_file(self, filename: str, level_filter: str) -> str:
        """读取日志文件"""
        try:
            log_file = self.log_dir / filename
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 过滤日志级别
            if level_filter != "ALL":
                lines = [line for line in lines if level_filter in line]
            
            # 返回最后100行
            return ''.join(lines[-100:])
        
        except Exception as e:
            return f"读取日志失败: {e}"
    
    def log_event(self, level: str, message: str, category: str = "SYSTEM"):
        """记录事件日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level} - {category}: {message}\n"
        
        # 写入日志文件
        log_file = self.log_dir / f"{category.lower()}.log"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass  # 静默失败
    
    def render_sidebar_widget(self):
        """渲染侧边栏监控小组件"""
        with st.sidebar:
            st.write("**📊 系统状态**")
            
            # 简化的系统指标
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 使用进度条显示
            st.write(f"CPU: {cpu:.1f}%")
            st.progress(cpu / 100)
            
            st.write(f"内存: {memory.percent:.1f}%")
            st.progress(memory.percent / 100)
            
            # 状态指示器
            if cpu > 80 or memory.percent > 85:
                st.warning("⚠️ 系统负载较高")
            else:
                st.success("✅ 系统运行正常")

# 全局实例
unified_monitoring_system = UnifiedMonitoringSystem()

# 便捷函数
def render_monitoring_dashboard(show_detailed: bool = True) -> None:
    """渲染监控仪表板 - 便捷函数"""
    return unified_monitoring_system.render_monitoring_dashboard(show_detailed)

def render_sidebar_widget():
    """渲染侧边栏监控组件 - 便捷函数"""
    return unified_monitoring_system.render_sidebar_widget()

def log_event(level: str, message: str, category: str = "SYSTEM"):
    """记录事件日志 - 便捷函数"""
    return unified_monitoring_system.log_event(level, message, category)
