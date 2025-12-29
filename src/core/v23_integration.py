"""
v2.3.0 功能集成模块
整合监控面板、智能调度和告警系统
"""

import streamlit as st
from src.ui.monitoring_dashboard import render_monitoring_dashboard
from src.ui.progress_tracker import render_progress_panel, get_progress_tracker
from src.utils.smart_scheduler import get_smart_scheduler
from src.utils.alert_system import get_alert_system
import threading
import time

class V23Integration:
    def __init__(self):
        self.scheduler = get_smart_scheduler()
        self.alert_system = get_alert_system()
        self.progress_tracker = get_progress_tracker()
        self.initialized = False
    
    def initialize(self):
        """初始化v2.3.0功能"""
        if self.initialized:
            return
        
        # 启动告警系统监控
        self.alert_system.start_monitoring()
        
        # 添加告警回调
        self.alert_system.add_callback(self._on_alert_received)
        
        self.initialized = True
    
    def _on_alert_received(self, alert):
        """处理收到的告警"""
        # 可以在这里添加自定义的告警处理逻辑
        pass
    
    def render_v23_sidebar(self):
        """渲染v2.3.0侧边栏功能"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🚀 v2.3.0 智能监控")
        
        # 快速状态显示
        recommendations = self.scheduler.get_recommendations()
        current_load = recommendations['current_load']
        
        # 系统状态指示器
        cpu_color = "🟢" if current_load['cpu_percent'] < 50 else "🟡" if current_load['cpu_percent'] < 80 else "🔴"
        memory_color = "🟢" if current_load['memory_percent'] < 60 else "🟡" if current_load['memory_percent'] < 85 else "🔴"
        
        st.sidebar.metric(
            f"{cpu_color} CPU", 
            f"{current_load['cpu_percent']:.1f}%",
            delta=f"负载: {current_load['cpu_level']}"
        )
        
        st.sidebar.metric(
            f"{memory_color} 内存", 
            f"{current_load['memory_percent']:.1f}%",
            delta=f"负载: {current_load['memory_level']}"
        )
        
        # 智能建议
        if recommendations['recommendations']:
            with st.sidebar.expander("💡 优化建议"):
                for rec in recommendations['recommendations'][:3]:  # 显示前3个建议
                    st.write(f"• {rec}")
        
        # 告警摘要
        alert_summary = self.alert_system.get_alert_summary()
        if alert_summary['total_alerts_24h'] > 0:
            with st.sidebar.expander(f"🚨 告警 ({alert_summary['total_alerts_24h']})"):
                st.write(f"• 严重: {alert_summary['critical_alerts_24h']}")
                st.write(f"• 警告: {alert_summary['warning_alerts_24h']}")
                if alert_summary['most_common_type']:
                    st.write(f"• 主要类型: {alert_summary['most_common_type']}")
    
    def render_monitoring_tab(self):
        """渲染监控标签页"""
        tab1, tab2, tab3 = st.tabs(["📊 系统监控", "📈 进度追踪", "⚙️ 智能调度"])
        
        with tab1:
            render_monitoring_dashboard()
        
        with tab2:
            render_progress_panel()
        
        with tab3:
            self._render_scheduler_panel()
    
    def _render_scheduler_panel(self):
        """渲染调度器面板"""
        st.markdown("#### 🤖 智能资源调度")
        
        # 当前配置
        optimal_config = self.scheduler.get_optimal_workers()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CPU工作线程", optimal_config['cpu_workers'])
        
        with col2:
            st.metric("IO工作线程", optimal_config['io_workers'])
        
        with col3:
            st.metric("负载等级", optimal_config['load_level'].upper())
        
        # 调度原因
        st.info(f"📋 调度原因: {optimal_config['reasoning']}")
        
        # 优化建议
        recommendations = self.scheduler.get_recommendations()
        if recommendations['recommendations']:
            st.markdown("##### 💡 优化建议")
            for i, rec in enumerate(recommendations['recommendations'], 1):
                st.write(f"{i}. {rec}")
        
        # 配置调整
        with st.expander("⚙️ 高级配置"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 阈值设置")
                cpu_low = st.slider("CPU低负载阈值", 10, 50, 
                                   self.scheduler.config['cpu_thresholds']['low'])
                cpu_medium = st.slider("CPU中负载阈值", 40, 80, 
                                      self.scheduler.config['cpu_thresholds']['medium'])
                cpu_high = st.slider("CPU高负载阈值", 70, 95, 
                                    self.scheduler.config['cpu_thresholds']['high'])
            
            with col2:
                st.markdown("##### 学习设置")
                adaptive_enabled = st.checkbox("启用自适应调整", 
                                             self.scheduler.config['adaptive_enabled'])
                learning_enabled = st.checkbox("启用学习功能", 
                                             self.scheduler.config['learning_enabled'])
            
            if st.button("💾 保存配置"):
                self.scheduler.config['cpu_thresholds'] = {
                    'low': cpu_low, 'medium': cpu_medium, 'high': cpu_high
                }
                self.scheduler.config['adaptive_enabled'] = adaptive_enabled
                self.scheduler.config['learning_enabled'] = learning_enabled
                self.scheduler.save_config()
                st.success("配置已保存！")
                st.rerun()
    
    def get_optimal_processing_config(self, task_type: str = 'general') -> dict:
        """获取最优处理配置"""
        return self.scheduler.get_optimal_workers(task_type)
    
    def create_processing_task(self, name: str, total_items: int, description: str = "") -> str:
        """创建处理任务"""
        return self.progress_tracker.create_task(name, total_items, description)
    
    def update_task_progress(self, task_id: str, completed: int, current_item: str = ""):
        """更新任务进度"""
        self.progress_tracker.update_progress(task_id, completed, current_item)
    
    def complete_task(self, task_id: str, success: bool = True, message: str = ""):
        """完成任务"""
        self.progress_tracker.complete_task(task_id, success, message)
    
    def record_task_performance(self, task_id: str, duration: float, success: bool, cpu_usage: float = None):
        """记录任务性能"""
        self.scheduler.record_performance(task_id, duration, success, cpu_usage)
    
    def cleanup(self):
        """清理资源"""
        if self.initialized:
            self.alert_system.stop_monitoring()
            self.initialized = False

# 全局v2.3.0集成实例
_v23_integration = None

def get_v23_integration() -> V23Integration:
    """获取v2.3.0集成实例"""
    global _v23_integration
    if _v23_integration is None:
        _v23_integration = V23Integration()
        _v23_integration.initialize()
    return _v23_integration
