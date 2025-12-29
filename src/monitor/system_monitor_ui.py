"""
系统监控界面 - 负责系统监控相关的UI逻辑
"""

import streamlit as st
import psutil
import time


class SystemMonitorUI:
    """系统监控界面"""
    
    def __init__(self):
        """初始化系统监控界面"""
        pass
    
    def render_monitor_panel(self):
        """渲染监控面板"""
        st.markdown("#### 📊 系统监控")
        
        # 自动刷新选项
        auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="monitor_auto_refresh")
        
        # 监控数据容器
        monitor_placeholder = st.empty()
        
        with monitor_placeholder.container():
            self.render_system_stats()
        
        # 自动刷新逻辑
        if auto_refresh:
            time.sleep(2)
            st.rerun()
    
    def render_system_stats(self):
        """渲染系统统计信息"""
        # CPU 监控
        cpu_percent = psutil.cpu_percent(interval=0.1)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.metric("CPU 使用率", f"{cpu_percent:.1f}%")
        with col2:
            st.caption(f"{psutil.cpu_count()} 核")
        st.progress(cpu_percent / 100)
        
        # GPU 监控 (简化版)
        gpu_active = self.check_gpu_status()
        col1, col2 = st.columns([4, 1])
        with col1:
            st.metric("GPU 状态", "活跃" if gpu_active else "空闲")
        with col2:
            st.caption("32 核")
        st.progress(0.5 if gpu_active else 0.0)
        
        # 内存监控
        mem = psutil.virtual_memory()
        col1, col2 = st.columns([4, 1])
        with col1:
            st.metric("内存使用", f"{mem.percent:.1f}%")
        with col2:
            st.caption(f"{mem.used/1024**3:.1f}GB")
        st.progress(mem.percent / 100)
        
        # 磁盘监控
        try:
            disk = psutil.disk_usage('/System/Volumes/Data')
            col1, col2 = st.columns([4, 1])
            with col1:
                st.metric("磁盘使用", f"{disk.percent:.1f}%")
            with col2:
                st.caption(f"{disk.used/1024**3:.0f}GB")
            st.progress(disk.percent / 100)
        except:
            # 降级到根目录
            disk = psutil.disk_usage('/')
            col1, col2 = st.columns([4, 1])
            with col1:
                st.metric("磁盘使用", f"{disk.percent:.1f}%")
            with col2:
                st.caption(f"{disk.used/1024**3:.0f}GB")
            st.progress(disk.percent / 100)
        
        # 进程信息
        current_proc = psutil.Process()
        proc_mem = current_proc.memory_info().rss / 1024**3
        st.caption(f"🔍 进程: {proc_mem:.1f}GB | {current_proc.num_threads()} 线程")
        st.caption("💡 GPU 详细信息需要: `sudo python3 system_monitor.py`")
    
    def check_gpu_status(self):
        """检查GPU状态"""
        try:
            import subprocess
            result = subprocess.run(
                ['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                capture_output=True, text=True, timeout=1
            )
            return 'PerformanceStatistics' in result.stdout
        except:
            return False
    
    def render_performance_dashboard(self):
        """渲染性能仪表板"""
        try:
            from src.ui.performance_monitor import get_monitor
            perf_monitor = get_monitor()
            perf_monitor.render_panel()
        except ImportError:
            st.info("性能监控模块未找到，显示基础监控")
            self.render_monitor_panel()
    
    def render_v23_monitoring(self):
        """渲染v2.3监控功能"""
        try:
            from src.core.v23_integration import get_v23_integration
            v23 = get_v23_integration()
            v23.render_monitoring_tab()
        except ImportError:
            st.info("v2.3监控模块未找到，显示基础监控")
            self.render_monitor_panel()
    
    def render_resource_usage(self):
        """渲染资源使用情况"""
        st.markdown("##### 📈 资源使用趋势")
        
        # 简单的资源使用历史
        if 'resource_history' not in st.session_state:
            st.session_state.resource_history = {
                'cpu': [],
                'memory': [],
                'timestamps': []
            }
        
        # 获取当前数据
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem_percent = psutil.virtual_memory().percent
        current_time = time.time()
        
        # 更新历史数据 (保留最近20个数据点)
        st.session_state.resource_history['cpu'].append(cpu_percent)
        st.session_state.resource_history['memory'].append(mem_percent)
        st.session_state.resource_history['timestamps'].append(current_time)
        
        # 保持数据长度
        max_points = 20
        for key in st.session_state.resource_history:
            if len(st.session_state.resource_history[key]) > max_points:
                st.session_state.resource_history[key] = st.session_state.resource_history[key][-max_points:]
        
        # 显示趋势图 (简化版)
        if len(st.session_state.resource_history['cpu']) > 1:
            import pandas as pd
            
            df = pd.DataFrame({
                'CPU': st.session_state.resource_history['cpu'],
                'Memory': st.session_state.resource_history['memory']
            })
            
            st.line_chart(df)
        else:
            st.info("收集数据中，请稍等...")
    
    def render_alert_system(self):
        """渲染告警系统"""
        st.markdown("##### 🚨 系统告警")
        
        # 检查告警条件
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem_percent = psutil.virtual_memory().percent
        
        alerts = []
        
        if cpu_percent > 80:
            alerts.append(f"🔥 CPU使用率过高: {cpu_percent:.1f}%")
        
        if mem_percent > 85:
            alerts.append(f"💾 内存使用率过高: {mem_percent:.1f}%")
        
        try:
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                alerts.append(f"💿 磁盘空间不足: {disk.percent:.1f}%")
        except:
            pass
        
        if alerts:
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("✅ 系统运行正常")
    
    def render_process_monitor(self):
        """渲染进程监控"""
        st.markdown("##### 🔍 进程监控")
        
        # 获取当前进程信息
        current_proc = psutil.Process()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("进程ID", current_proc.pid)
        
        with col2:
            mem_mb = current_proc.memory_info().rss / 1024**2
            st.metric("内存使用", f"{mem_mb:.1f}MB")
        
        with col3:
            st.metric("线程数", current_proc.num_threads())
        
        # CPU使用率
        try:
            cpu_percent = current_proc.cpu_percent(interval=0.1)
            st.metric("进程CPU", f"{cpu_percent:.1f}%")
        except:
            st.metric("进程CPU", "N/A")
        
        # 文件描述符
        try:
            num_fds = current_proc.num_fds()
            st.metric("文件描述符", num_fds)
        except:
            st.metric("文件描述符", "N/A")
