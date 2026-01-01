#!/usr/bin/env python3
"""
局部刷新监控仪表板
只刷新监控区域，不影响对话和其他功能
"""

import streamlit as st
import time
import json
from datetime import datetime
import plotly.graph_objects as go
from pathlib import Path

class LocalRefreshMonitor:
    """局部刷新监控器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.metrics_file = self.project_root / "monitoring_alerts" / "realtime_metrics.json"
        
    def render_monitor_dashboard(self):
        """渲染监控仪表板 - 只刷新监控区域"""
        
        # 使用st.empty()容器实现局部刷新
        monitor_container = st.empty()
        
        with monitor_container.container():
            st.markdown("### 📊 实时监控")
            
            # 获取当前指标
            metrics = self._get_current_metrics()
            
            # 使用列布局显示关键指标
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "响应时间", 
                    f"{metrics.get('response_time', 0):.2f}s",
                    delta=f"{metrics.get('response_time_delta', 0):+.2f}s"
                )
            
            with col2:
                st.metric(
                    "查询次数",
                    metrics.get('query_count', 0),
                    delta=metrics.get('query_count_delta', 0)
                )
            
            with col3:
                st.metric(
                    "成功率",
                    f"{metrics.get('success_rate', 0):.1f}%",
                    delta=f"{metrics.get('success_rate_delta', 0):+.1f}%"
                )
            
            with col4:
                st.metric(
                    "活跃知识库",
                    metrics.get('active_kb_count', 0)
                )
            
            # 简单的状态指示器
            status_color = "🟢" if metrics.get('system_status') == 'healthy' else "🟡"
            st.write(f"系统状态: {status_color} {metrics.get('system_status', 'unknown')}")
            
            # 最后更新时间
            st.caption(f"最后更新: {datetime.now().strftime('%H:%M:%S')}")
    
    def _get_current_metrics(self):
        """获取当前监控指标"""
        # 模拟实时数据（实际应用中从日志或数据库获取）
        import random
        
        base_response_time = 1.2
        response_time = base_response_time + random.uniform(-0.3, 0.5)
        
        return {
            "response_time": response_time,
            "response_time_delta": response_time - base_response_time,
            "query_count": random.randint(50, 200),
            "query_count_delta": random.randint(-5, 15),
            "success_rate": random.uniform(85, 99),
            "success_rate_delta": random.uniform(-2, 3),
            "active_kb_count": random.randint(1, 5),
            "system_status": "healthy" if response_time < 3 else "warning"
        }
    
    def render_non_intrusive_monitor(self):
        """渲染非侵入式监控 - 使用session state避免全页面刷新"""
        
        # 检查是否需要更新监控数据
        current_time = time.time()
        last_update = st.session_state.get('monitor_last_update', 0)
        
        # 每30秒更新一次监控数据
        if current_time - last_update > 30:
            st.session_state.monitor_metrics = self._get_current_metrics()
            st.session_state.monitor_last_update = current_time
        
        # 从session state获取数据，避免重复计算
        metrics = st.session_state.get('monitor_metrics', {})
        
        # 使用固定的容器ID，只更新内容
        with st.container():
            st.markdown("### 📊 系统监控")
            
            # 紧凑的监控显示
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"⚡ 响应: {metrics.get('response_time', 0):.2f}s")
                st.write(f"📊 查询: {metrics.get('query_count', 0)} 次")
            
            with col2:
                st.write(f"✅ 成功率: {metrics.get('success_rate', 0):.1f}%")
                status = "🟢 正常" if metrics.get('system_status') == 'healthy' else "🟡 注意"
                st.write(f"🔍 状态: {status}")
    
    def create_monitoring_widget(self):
        """创建监控小部件 - 最小化影响"""
        
        # 使用侧边栏的监控标签页
        if st.session_state.get('show_monitoring_widget', False):
            
            # 获取实时数据但不触发页面刷新
            metrics = self._get_lightweight_metrics()
            
            # 简洁的监控信息
            st.markdown("**📊 实时状态**")
            
            # 使用进度条显示关键指标
            response_time = metrics.get('response_time', 1.0)
            st.progress(min(response_time / 5.0, 1.0), text=f"响应时间: {response_time:.2f}s")
            
            success_rate = metrics.get('success_rate', 95) / 100
            st.progress(success_rate, text=f"成功率: {success_rate*100:.1f}%")
            
            # 状态指示
            if response_time < 2:
                st.success("🟢 系统运行正常")
            elif response_time < 5:
                st.warning("🟡 响应稍慢")
            else:
                st.error("🔴 响应过慢")
    
    def _get_lightweight_metrics(self):
        """获取轻量级指标，避免影响性能"""
        # 从缓存或简单计算获取，不做复杂操作
        return {
            "response_time": st.session_state.get('last_query_time', 1.2),
            "success_rate": 95.0,  # 可以从session state获取
            "system_status": "healthy"
        }

# 全局监控实例
local_monitor = LocalRefreshMonitor("/Users/zhaosj/Documents/rag-pro-max")

def show_local_monitor():
    """显示局部监控 - 不影响其他区域"""
    local_monitor.render_non_intrusive_monitor()

def show_monitor_widget():
    """显示监控小部件"""
    local_monitor.create_monitoring_widget()
