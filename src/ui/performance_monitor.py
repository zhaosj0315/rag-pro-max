"""
性能监控面板
v1.5.1 新增功能
"""

import streamlit as st
import time
from src.app_logging import LogManager


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = LogManager()
        
    def render_panel(self):
        """渲染性能监控面板"""
        with st.expander("📊 性能监控", expanded=True):
            # 获取性能指标
            metrics = self.logger.get_metrics()
            
            if not metrics:
                st.info("💡 暂无性能数据，开始对话后将显示统计信息")
                return
            
            # 汇总所有操作的指标
            all_times = []
            total_operations = 0
            for op_name, op_metrics in metrics.items():
                if isinstance(op_metrics, dict) and 'count' in op_metrics:
                    total_operations += op_metrics['count']
                    # 重建时间列表
                    avg = op_metrics['avg']
                    count = op_metrics['count']
                    for _ in range(count):
                        all_times.append(avg)
            
            if not all_times:
                st.info("💡 暂无性能数据，开始对话后将显示统计信息")
                return
            
            # 查询性能
            st.markdown("**🔍 查询性能**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_time = sum(all_times) / len(all_times)
                st.metric("平均耗时", f"{avg_time:.2f}s")
            
            with col2:
                min_time = min(all_times)
                st.metric("最快", f"{min_time:.2f}s")
            
            with col3:
                max_time = max(all_times)
                st.metric("最慢", f"{max_time:.2f}s")
            
            # 查询统计
            st.markdown("**📈 查询统计**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("总查询数", total_operations)
            
            with col2:
                total_time = sum(all_times)
                st.metric("总耗时", f"{total_time:.1f}s")
            
            # 最近查询
            if 'last_query_stats' in st.session_state:
                st.markdown("**⏱️ 最近查询**")
                stats = st.session_state.last_query_stats
                
                col1, col2 = st.columns(2)
                with col1:
                    query_time = stats.get('time', 0)
                    st.caption(f"耗时: {query_time:.2f}s")
                
                with col2:
                    doc_count = stats.get('doc_count', 0)
                    st.caption(f"检索文档: {doc_count} 个")
            
            # 操作按钮
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 刷新", use_container_width=True, key="monitor_perf_refresh"):
                    st.rerun()
            
            with col2:
                if st.button("🗑️ 清空", use_container_width=True, key="monitor_perf_clear"):
                    self.logger.metrics.clear()
                    if 'last_query_stats' in st.session_state:
                        del st.session_state.last_query_stats
                    st.success("✅ 已清空")
                    time.sleep(0.5)
                    st.rerun()


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    if 'performance_monitor' not in st.session_state:
        st.session_state.performance_monitor = PerformanceMonitor()
    return st.session_state.performance_monitor
