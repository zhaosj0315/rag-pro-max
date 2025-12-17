"""
增强的性能监控仪表板
"""

import time
import psutil
import torch
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any

class PerformanceDashboard:
    """实时性能仪表板"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 100
        
    def collect_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(percpu=True)
        
        # 内存指标
        memory = psutil.virtual_memory()
        
        # GPU指标
        gpu_metrics = {"available": False}
        if torch.backends.mps.is_available():
            try:
                gpu_metrics = {
                    "available": True,
                    "allocated_mb": torch.mps.driver_allocated_memory() / (1024**2),
                    "cached_mb": torch.mps.driver_allocated_memory() / (1024**2)
                }
            except:
                pass
        
        # 磁盘指标
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": datetime.now(),
            "cpu_percent": cpu_percent,
            "cpu_per_core": cpu_per_core,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "disk_percent": disk.percent,
            "gpu": gpu_metrics
        }
        
        # 保存历史
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        return metrics
    
    def display_realtime_metrics(self):
        """显示实时指标"""
        metrics = self.collect_metrics()
        
        st.subheader("🔥 实时性能监控")
        
        # 主要指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_color = "red" if metrics["cpu_percent"] > 80 else "orange" if metrics["cpu_percent"] > 60 else "green"
            st.metric("CPU使用率", f"{metrics['cpu_percent']:.1f}%", 
                     delta_color=cpu_color)
        
        with col2:
            mem_color = "red" if metrics["memory_percent"] > 85 else "orange" if metrics["memory_percent"] > 70 else "green"
            st.metric("内存使用", f"{metrics['memory_percent']:.1f}%",
                     f"{metrics['memory_used_gb']:.1f}GB")
        
        with col3:
            if metrics["gpu"]["available"]:
                st.metric("GPU内存", f"{metrics['gpu']['allocated_mb']:.0f}MB")
            else:
                st.metric("GPU", "不可用")
        
        with col4:
            disk_color = "red" if metrics["disk_percent"] > 90 else "orange" if metrics["disk_percent"] > 80 else "green"
            st.metric("磁盘使用", f"{metrics['disk_percent']:.1f}%")
        
        # CPU核心详情
        if st.checkbox("显示CPU核心详情"):
            st.write("**CPU核心使用率:**")
            cores_per_row = 4
            for i in range(0, len(metrics["cpu_per_core"]), cores_per_row):
                cols = st.columns(cores_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(metrics["cpu_per_core"]):
                        core_usage = metrics["cpu_per_core"][i + j]
                        col.metric(f"核心 {i+j}", f"{core_usage:.1f}%")
    
    def display_performance_trends(self):
        """显示性能趋势"""
        if len(self.metrics_history) < 2:
            st.info("收集数据中，请稍候...")
            return
        
        st.subheader("📈 性能趋势")
        
        # 准备数据
        timestamps = [m["timestamp"] for m in self.metrics_history[-20:]]
        cpu_data = [m["cpu_percent"] for m in self.metrics_history[-20:]]
        memory_data = [m["memory_percent"] for m in self.metrics_history[-20:]]
        
        # 简单的文本图表
        st.write("**最近20次采样:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("CPU使用率趋势:")
            for i, (ts, cpu) in enumerate(zip(timestamps[-5:], cpu_data[-5:])):
                bar_length = int(cpu / 5)  # 缩放到20字符
                bar = "█" * bar_length + "░" * (20 - bar_length)
                st.text(f"{ts.strftime('%H:%M:%S')} {bar} {cpu:.1f}%")
        
        with col2:
            st.write("内存使用率趋势:")
            for i, (ts, mem) in enumerate(zip(timestamps[-5:], memory_data[-5:])):
                bar_length = int(mem / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                st.text(f"{ts.strftime('%H:%M:%S')} {bar} {mem:.1f}%")
    
    def display_benchmark_results(self):
        """显示基准测试结果"""
        st.subheader("🏃 性能基准")
        
        if st.button("运行基准测试"):
            with st.spinner("运行基准测试..."):
                results = self.run_benchmark()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CPU计算", f"{results['cpu_score']:.0f} ops/s")
                with col2:
                    st.metric("内存带宽", f"{results['memory_score']:.0f} MB/s")
                with col3:
                    if results['gpu_score'] > 0:
                        st.metric("GPU计算", f"{results['gpu_score']:.0f} ops/s")
                    else:
                        st.metric("GPU", "不可用")
    
    def run_benchmark(self) -> Dict[str, float]:
        """运行基准测试"""
        results = {"cpu_score": 0, "memory_score": 0, "gpu_score": 0}
        
        # CPU基准测试
        start_time = time.time()
        total = sum(i * i for i in range(100000))
        cpu_time = time.time() - start_time
        results["cpu_score"] = 100000 / cpu_time if cpu_time > 0 else 0
        
        # 内存基准测试
        start_time = time.time()
        data = [i for i in range(1000000)]
        memory_time = time.time() - start_time
        results["memory_score"] = len(data) * 4 / (1024 * 1024) / memory_time if memory_time > 0 else 0
        
        # GPU基准测试
        if torch.backends.mps.is_available():
            try:
                start_time = time.time()
                x = torch.randn(1000, 1000, device='mps')
                y = torch.mm(x, x)
                torch.mps.synchronize()
                gpu_time = time.time() - start_time
                results["gpu_score"] = 1000000 / gpu_time if gpu_time > 0 else 0
            except:
                pass
        
        return results

# 全局性能仪表板
performance_dashboard = PerformanceDashboard()
