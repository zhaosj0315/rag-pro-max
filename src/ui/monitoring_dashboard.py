"""
智能监控仪表盘组件 (v2.3.0)
提供系统资源、任务队列和后台进程的实时监控
"""

import streamlit as st
import psutil
import time
import os
import threading
from typing import Dict, Any

class MonitoringDashboard:
    """系统监控仪表盘"""
    
    def __init__(self):
        self.last_update = 0
        self.update_interval = 2.0  # 最小更新间隔(秒)
        self.history = {
            'cpu': [],
            'memory': [],
            'timestamps': []
        }
        # 保持最多30个数据点
        self.max_history = 30
        
    def _get_system_stats(self) -> Dict[str, Any]:
        """获取系统资源统计"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # 内存
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used_gb = mem.used / (1024 ** 3)
        mem_total_gb = mem.total / (1024 ** 3)
        
        # 进程信息
        process = psutil.Process(os.getpid())
        app_mem_mb = process.memory_info().rss / (1024 ** 2)
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': mem_percent,  # 修复键名以匹配测试
            'mem_used_gb': mem_used_gb,
            'mem_total_gb': mem_total_gb,
            'app_mem_mb': app_mem_mb,
            'timestamp': time.time()
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """公开接口：获取系统指标 (用于测试和外部调用)"""
        return self._get_system_stats()
        
    def save_metrics(self, metrics: Dict[str, Any]):
        """保存指标到历史记录 (满足测试要求)"""
        timestamp = metrics.get('timestamp', time.time())
        self.history['timestamps'].append(timestamp)
        self.history['cpu'].append(metrics.get('cpu_percent', 0))
        self.history['memory'].append(metrics.get('memory_percent', 0))
        
        # 限制历史长度
        if len(self.history['timestamps']) > self.max_history:
            self.history['timestamps'] = self.history['timestamps'][-self.max_history:]
            self.history['cpu'] = self.history['cpu'][-self.max_history:]
            self.history['memory'] = self.history['memory'][-self.max_history:]
            
    def load_history(self) -> Dict[str, list]:
        """加载历史记录 (满足测试要求)"""
        return self.history
        
    def render_sidebar_widget(self):
        """渲染侧边栏监控小组件"""
        
        # 限制更新频率，避免过度占用 Streamlit 重绘资源
        current_time = time.time()
        
        # 初始化 Session State 数据
        if 'monitor_stats' not in st.session_state:
            st.session_state.monitor_stats = self._get_system_stats()
            
        # 只有在间隔期外才更新数据
        if current_time - self.last_update > self.update_interval:
            metrics = self._get_system_stats()
            st.session_state.monitor_stats = metrics
            self.save_metrics(metrics) # 顺便保存历史
            self.last_update = current_time
            
        stats = st.session_state.monitor_stats
        
        with st.expander("📊 系统监控 (实时)", expanded=False):
            # 1. CPU 仪表
            st.caption("CPU 使用率")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(min(stats['cpu_percent'] / 100, 1.0))
            with col2:
                st.text(f"{stats['cpu_percent']:.1f}%")
                
            # 2. 内存 仪表
            st.caption(f"内存 (应用占用: {stats['app_mem_mb']:.0f} MB)")
            col1, col2 = st.columns([3, 1])
            with col1:
                # 颜色阈值: >85% 红色, >70% 黄色, 其他 绿色
                color = "normal"
                mem_pct = stats.get('memory_percent', stats.get('mem_percent', 0))
                if mem_pct > 85:
                    color = "off" # Streamlit progress 不支持直接改色，这里仅逻辑标记
                st.progress(min(mem_pct / 100, 1.0))
            with col2:
                st.text(f"{mem_pct:.1f}%")
            
            # 3. 线程/任务信息 (占位，需要接入真实队列)
            # st.divider()
            # st.caption("任务队列")
            # active_threads = threading.active_count()
            # st.text(f"活跃线程: {active_threads}")

    def render_full_dashboard(self):
        """渲染完整监控页面（用于独立Tab）"""
        st.subheader("🖥️ 系统资源监控")
        
        stats = self._get_system_stats()
        mem_pct = stats.get('memory_percent', stats.get('mem_percent', 0))
        
        # 顶部指标卡
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("CPU 使用率", f"{stats['cpu_percent']}%")
        with col2:
            st.metric("内存使用率", f"{mem_pct}%", f"{stats['app_mem_mb']:.0f} MB (App)")
        with col3:
            st.metric("系统内存", f"{stats['mem_used_gb']:.1f}/{stats['mem_total_gb']:.1f} GB")
        with col4:
            st.metric("活跃线程", f"{threading.active_count()}")
            
        # 历史趋势图
        if len(self.history['timestamps']) > 0:
            st.subheader("📈 实时趋势")
            chart_data = {
                'CPU': self.history['cpu'],
                'Memory': self.history['memory']
            }
            st.line_chart(chart_data)
        else:
             st.info("⌛ 正在收集历史数据...")
        
        st.info("💡 提示: 高 CPU 使用率通常发生在文件解析或向量化阶段，属于正常现象。")



# 全局单例

monitoring_dashboard = MonitoringDashboard()



# 兼容性接口 (供 v23_integration.py 调用)

def render_monitoring_dashboard():

    """渲染完整监控面板 (v23集成接口)"""

    monitoring_dashboard.render_full_dashboard()



def render_sidebar_widget():

    """渲染侧边栏组件 (v23集成接口)"""

    monitoring_dashboard.render_sidebar_widget()
