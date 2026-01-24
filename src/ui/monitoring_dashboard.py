import streamlit as st
import psutil
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.app_logging.log_manager import LogManager

logger = LogManager()

def render_monitoring_dashboard():
    """渲染系统监控仪表盘"""
    st.markdown("#### 📊 系统实时性能监控")
    
    # 顶部指标
    col1, col2, col3, col4 = st.columns(4)
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    with col1:
        st.metric("CPU 使用率", f"{cpu_percent}%")
    with col2:
        st.metric("内存 使用率", f"{mem.percent}%")
    with col3:
        st.metric("磁盘 使用率", f"{disk.percent}%")
    with col4:
        # 获取当前进程信息
        process = psutil.Process()
        thread_count = process.num_threads()
        st.metric("系统线程数", thread_count)

    # 资源趋势图
    st.markdown("---")
    st.markdown("##### 📈 资源使用趋势")
    
    # [v6.9.9] 使用列表存储以提高稳定性，规避 pd.concat 类型冲突
    if 'monitor_data_list' not in st.session_state:
        st.session_state.monitor_data_list = []
    
    # 添加新数据点点
    new_entry = {
        'time': datetime.now().strftime("%H:%M:%S"),
        'cpu': float(cpu_percent),
        'memory': float(mem.percent)
    }
    
    st.session_state.monitor_data_list.append(new_entry)
    
    # 仅保留最近 20 个采样点
    if len(st.session_state.monitor_data_list) > 20:
        st.session_state.monitor_data_list = st.session_state.monitor_data_list[-20:]
    
    # 渲染时转换为 DataFrame
    monitor_df = pd.DataFrame(st.session_state.monitor_data_list)
    
    # 绘制折线图
    if not monitor_df.empty:
        fig = px.line(monitor_df, x='time', y=['cpu', 'memory'], 
                     labels={'value': '使用率 (%)', 'time': '时间', 'variable': '指标'},
                     title="CPU vs 内存趋势 (最近20个采样点)")
        st.plotly_chart(fig, use_container_width=True)

    # 进程详细列表
    with st.expander("🔍 进程资源占用详情", expanded=False):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                # [v7.0.0] 健壮性增强：确保数值有效，规避 NoneType 比较错误
                p_cpu = proc.info.get('cpu_percent')
                p_mem = proc.info.get('memory_percent')
                
                # 显式转换为 0.0 如果为 None
                p_cpu = float(p_cpu) if p_cpu is not None else 0.0
                p_mem = float(p_mem) if p_mem is not None else 0.0
                
                # 更新 info 字典以确保 dataframe 渲染正常
                proc.info['cpu_percent'] = p_cpu
                proc.info['memory_percent'] = p_mem

                # 只显示占用较高的进程
                if p_cpu > 1.0 or p_mem > 1.0:
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                pass
        
        if processes:
            df_proc = pd.DataFrame(processes).sort_values(by='cpu_percent', ascending=False)
            st.dataframe(df_proc, use_container_width=True, hide_index=True)
        else:
            st.info("暂无高负载进程数据")
