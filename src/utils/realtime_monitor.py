#!/usr/bin/env python3
"""
实时监控组件
使用JavaScript实现真正的实时监控，不影响对话页面
"""

import streamlit as st
import json
import time
from datetime import datetime
import psutil
from pathlib import Path

class RealtimeMonitor:
    """实时监控器"""
    
    def __init__(self):
        self.update_interval = 5  # 5秒更新一次
        self.metrics_file = Path("monitoring_data.json")
    
    def render_realtime_monitor(self):
        """渲染实时监控界面 - 使用JavaScript实现倒计时每秒更新"""
        
        st.markdown("### 📊 实时系统监控")
        st.info("💡 此监控使用JavaScript倒计时，不会影响知识库构建和对话功能")
        
        # 使用session state存储监控数据
        current_time = time.time()
        
        if 'monitor_data' not in st.session_state:
            st.session_state.monitor_data = {
                'start_time': current_time,
                'last_update': current_time,
                'refresh_count': 0,
                'history': {
                    'timestamps': [],
                    'cpu_usage': [],
                    'memory_usage': [],
                    'response_time': [],
                    'active_sessions': []
                }
            }
        
        # 计算初始状态
        elapsed = current_time - st.session_state.monitor_data['start_time']
        countdown = max(0, self.update_interval - (elapsed % self.update_interval))
        progress = ((elapsed % self.update_interval) / self.update_interval) * 100
        refresh_count = int(elapsed // self.update_interval)
        
        # 获取系统指标
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 模拟其他指标
        import random
        response_time = round(random.uniform(1.5, 3.5), 2)
        active_sessions = random.randint(1, 8)
        
        # 更新历史数据 (保留最近50个数据点)
        if len(st.session_state.monitor_data['history']['timestamps']) >= 50:
            for key in st.session_state.monitor_data['history']:
                st.session_state.monitor_data['history'][key].pop(0)
        
        st.session_state.monitor_data['history']['timestamps'].append(datetime.now().strftime('%H:%M:%S'))
        st.session_state.monitor_data['history']['cpu_usage'].append(cpu_usage)
        st.session_state.monitor_data['history']['memory_usage'].append(memory_usage)
        st.session_state.monitor_data['history']['response_time'].append(response_time)
        st.session_state.monitor_data['history']['active_sessions'].append(active_sessions)
        
        # 显示倒计时 - 使用JavaScript更新
        st.markdown(f"""
        <div id="countdown-display">
            <h2>⏰ 倒计时: <span id="countdown-value">{int(countdown)}</span> 秒</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示刷新统计
        st.markdown(f"📊 已刷新: **{refresh_count}** 次")
        
        # 显示进度条
        st.progress(progress / 100)
        
        # 添加图表选项
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📈 历史趋势图表")
        with col2:
            show_charts = st.checkbox("显示图表", value=True, help="显示系统指标的历史趋势")
        
        if show_charts and len(st.session_state.monitor_data['history']['timestamps']) > 1:
            # 创建图表
            import pandas as pd
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # 准备数据
            df = pd.DataFrame(st.session_state.monitor_data['history'])
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('CPU使用率 (%)', '内存使用率 (%)', '响应时间 (秒)', '活跃会话数'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # CPU使用率
            fig.add_trace(
                go.Scatter(x=df['timestamps'], y=df['cpu_usage'], 
                          name='CPU', line=dict(color='#1f77b4')),
                row=1, col=1
            )
            
            # 内存使用率
            fig.add_trace(
                go.Scatter(x=df['timestamps'], y=df['memory_usage'], 
                          name='内存', line=dict(color='#ff7f0e')),
                row=1, col=2
            )
            
            # 响应时间
            fig.add_trace(
                go.Scatter(x=df['timestamps'], y=df['response_time'], 
                          name='响应时间', line=dict(color='#2ca02c')),
                row=2, col=1
            )
            
            # 活跃会话
            fig.add_trace(
                go.Scatter(x=df['timestamps'], y=df['active_sessions'], 
                          name='会话数', line=dict(color='#d62728')),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=400,
                showlegend=False,
                title_text=f"系统监控趋势 (最近{len(df)}个数据点)",
                title_x=0.5
            )
            
            # 更新x轴，只显示部分时间标签
            for i in range(1, 3):
                for j in range(1, 3):
                    fig.update_xaxes(
                        tickangle=45,
                        nticks=5,  # 只显示5个时间点
                        row=i, col=j
                    )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示统计摘要
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("平均CPU", f"{df['cpu_usage'].mean():.1f}%", 
                         f"{df['cpu_usage'].iloc[-1] - df['cpu_usage'].mean():.1f}%")
            with col2:
                st.metric("平均内存", f"{df['memory_usage'].mean():.1f}%",
                         f"{df['memory_usage'].iloc[-1] - df['memory_usage'].mean():.1f}%")
            with col3:
                st.metric("平均响应", f"{df['response_time'].mean():.2f}s",
                         f"{df['response_time'].iloc[-1] - df['response_time'].mean():.2f}s")
            with col4:
                st.metric("平均会话", f"{df['active_sessions'].mean():.0f}",
                         f"{df['active_sessions'].iloc[-1] - df['active_sessions'].mean():.0f}")
        
        # 显示其他信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"📊 已刷新: {refresh_count} 次")
        
        with col2:
            st.progress(progress / 100, text=f"进度: {int(progress)}%")
            if st.button("🔄 立即刷新", key="manual_refresh"):
                st.session_state.monitor_data['start_time'] = current_time
                st.success("✅ 手动刷新完成！")
        
        # 显示监控数据
        st.markdown("---")
        self._display_current_metrics_simple()
        
        # 当前时间
        st.write(f"🕐 当前时间: {datetime.now().strftime('%H:%M:%S')}")
        
        # JavaScript倒计时脚本
        st.markdown(f"""
        <script>
        // 倒计时JavaScript实现
        if (!window.countdownInterval) {{
            let startTime = {st.session_state.monitor_data['start_time'] * 1000}; // 转换为毫秒
            let interval = {self.update_interval * 1000}; // 5秒间隔
            
            function updateCountdown() {{
                let now = Date.now();
                let elapsed = now - startTime;
                let cycleTime = elapsed % interval;
                let countdown = Math.max(0, Math.floor((interval - cycleTime) / 1000));
                
                let countdownElement = document.getElementById('countdown-value');
                if (countdownElement) {{
                    countdownElement.textContent = countdown;
                }}
                
                // 如果倒计时到0，重置开始时间
                if (countdown === 0) {{
                    startTime = now;
                }}
            }}
            
            // 每秒更新倒计时
            window.countdownInterval = setInterval(updateCountdown, 1000);
            
            // 立即执行一次
            updateCountdown();
        }}
        </script>
        """, unsafe_allow_html=True)
    
    def _display_current_metrics_simple(self):
        """显示当前监控指标（简化版）"""
        
        # 获取系统指标
        metrics = self._get_system_metrics()
        
        # 系统资源监控
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_percent = metrics['cpu_percent']
            cpu_color = "🔴" if cpu_percent > 80 else "🟡" if cpu_percent > 60 else "🟢"
            st.metric(
                f"{cpu_color} CPU使用率",
                f"{cpu_percent:.1f}%",
                delta=f"{metrics.get('cpu_delta', 0):+.1f}%"
            )
        
        with col2:
            memory_percent = metrics['memory_percent']
            mem_color = "🔴" if memory_percent > 80 else "🟡" if memory_percent > 60 else "🟢"
            st.metric(
                f"{mem_color} 内存使用",
                f"{memory_percent:.1f}%",
                delta=f"{metrics.get('memory_delta', 0):+.1f}%"
            )
        
        with col3:
            response_time = metrics.get('response_time', 1.2)
            resp_color = "🔴" if response_time > 3 else "🟡" if response_time > 2 else "🟢"
            st.metric(
                f"{resp_color} 响应时间",
                f"{response_time:.2f}s",
                delta=f"{metrics.get('response_delta', 0):+.2f}s"
            )
        
        with col4:
            active_sessions = metrics.get('active_sessions', 1)
            st.metric(
                "🔗 活跃会话",
                active_sessions,
                delta=metrics.get('session_delta', 0)
            )
        
        # 应用状态概览
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            kb_count = len(self._get_knowledge_bases())
            st.write(f"📚 知识库: {kb_count} 个")
        
        with col2:
            error_rate = metrics.get('error_rate', 0)
            error_color = "🔴" if error_rate > 5 else "🟡" if error_rate > 1 else "🟢"
            st.write(f"{error_color} 错误率: {error_rate:.1f}%")
        
        with col3:
            last_update = datetime.now().strftime("%H:%M:%S")
            st.write(f"🕐 更新: {last_update}")

    
    def _get_system_metrics(self):
        """获取系统监控指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 获取历史数据用于计算变化量
            if 'monitor_history' not in st.session_state:
                st.session_state.monitor_history = []
            
            # 模拟应用指标（增加变化幅度让效果更明显）
            import random
            base_response = 1.0
            response_time = base_response + random.uniform(0, 2.0)  # 增加变化范围
            active_sessions = random.randint(1, 8)  # 增加变化范围
            total_queries = random.randint(50, 500)  # 增加变化范围
            error_rate = random.uniform(0, 5)  # 增加变化范围
            
            # 计算变化量
            current_metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_usage': disk_usage,
                'response_time': response_time,
                'active_sessions': active_sessions,
                'total_queries': total_queries,
                'error_rate': error_rate,
                'timestamp': time.time()
            }
            
            # 计算与上次的差值
            if st.session_state.monitor_history:
                last_metrics = st.session_state.monitor_history[-1]
                cpu_delta = cpu_percent - last_metrics.get('cpu_percent', cpu_percent)
                memory_delta = memory_percent - last_metrics.get('memory_percent', memory_percent)
                response_delta = response_time - last_metrics.get('response_time', response_time)
                session_delta = active_sessions - last_metrics.get('active_sessions', active_sessions)
            else:
                cpu_delta = 0
                memory_delta = 0
                response_delta = 0
                session_delta = 0
            
            # 添加变化量到结果
            current_metrics.update({
                'cpu_delta': cpu_delta,
                'memory_delta': memory_delta,
                'response_delta': response_delta,
                'session_delta': session_delta,
                'network_ok': True
            })
            
            # 保存历史数据（只保留最近10次）
            st.session_state.monitor_history.append(current_metrics)
            if len(st.session_state.monitor_history) > 10:
                st.session_state.monitor_history.pop(0)
            
            return current_metrics
            
        except Exception as e:
            # 降级处理
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_usage': 0,
                'response_time': 0,
                'active_sessions': 0,
                'total_queries': 0,
                'error_rate': 0,
                'network_ok': False,
                'error': str(e),
                'cpu_delta': 0,
                'memory_delta': 0,
                'response_delta': 0,
                'session_delta': 0
            }
    
    def _get_knowledge_bases(self):
        """获取知识库列表"""
        try:
            kb_dir = Path("vector_db_storage")
            if kb_dir.exists():
                return [d.name for d in kb_dir.iterdir() if d.is_dir()]
            return []
        except:
            return []
    
    def save_metrics_to_file(self):
        """保存监控数据到文件"""
        metrics = self._get_system_metrics()
        
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            st.error(f"保存监控数据失败: {e}")
    
    def render_mini_monitor(self):
        """渲染迷你监控组件（用于侧边栏）"""
        
        metrics = self._get_system_metrics()
        
        # 紧凑显示
        st.markdown("**📊 系统状态**")
        
        # CPU和内存
        cpu_color = "🔴" if metrics['cpu_percent'] > 80 else "🟡" if metrics['cpu_percent'] > 60 else "🟢"
        mem_color = "🔴" if metrics['memory_percent'] > 80 else "🟡" if metrics['memory_percent'] > 60 else "🟢"
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"{cpu_color} CPU: {metrics['cpu_percent']:.0f}%")
        with col2:
            st.write(f"{mem_color} 内存: {metrics['memory_percent']:.0f}%")
        
        # 响应时间
        resp_time = metrics.get('response_time', 1.2)
        resp_color = "🔴" if resp_time > 3 else "🟡" if resp_time > 2 else "🟢"
        st.write(f"{resp_color} 响应: {resp_time:.1f}s")
        
        # 自动刷新提示
        st.caption(f"🔄 自动刷新 ({self.update_interval}s)")
        
        # 自动刷新逻辑
        if 'mini_monitor_last_update' not in st.session_state:
            st.session_state.mini_monitor_last_update = time.time()
        
        current_time = time.time()
        if current_time - st.session_state.mini_monitor_last_update > self.update_interval:
            st.session_state.mini_monitor_last_update = current_time
            st.rerun()

def render_realtime_monitoring():
    """渲染实时监控界面"""
    monitor = RealtimeMonitor()
    monitor.render_realtime_monitor()

def render_mini_monitoring():
    """渲染迷你监控"""
    monitor = RealtimeMonitor()
    monitor.render_mini_monitor()

# 全局实时监控实例
realtime_monitor = RealtimeMonitor()
