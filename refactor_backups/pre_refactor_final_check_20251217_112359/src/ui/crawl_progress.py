"""
爬虫进度可视化组件
"""

import streamlit as st
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List

class CrawlProgressMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.stats = {
            'total_urls': 0,
            'crawled_urls': 0,
            'failed_urls': 0,
            'duplicate_content': 0,
            'robots_blocked': 0,
            'bytes_downloaded': 0,
            'current_depth': 0,
            'max_depth': 0
        }
        self.timeline = []
        
    def update_stats(self, **kwargs):
        """更新统计信息"""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] = value
        
        # 记录时间线
        self.timeline.append({
            'timestamp': time.time(),
            'crawled': self.stats['crawled_urls'],
            'failed': self.stats['failed_urls']
        })
    
    def render_progress_dashboard(self):
        """渲染进度仪表板"""
        
        # 计算统计数据
        elapsed_time = time.time() - self.start_time
        success_rate = (self.stats['crawled_urls'] / max(self.stats['total_urls'], 1)) * 100
        crawl_speed = self.stats['crawled_urls'] / max(elapsed_time / 60, 0.1)  # 页面/分钟
        
        # 顶部指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "成功爬取", 
                f"{self.stats['crawled_urls']}", 
                f"+{self.stats['crawled_urls'] - self.stats.get('prev_crawled', 0)}"
            )
        
        with col2:
            st.metric(
                "成功率", 
                f"{success_rate:.1f}%",
                f"{success_rate - 90:.1f}%" if success_rate < 90 else "优秀"
            )
        
        with col3:
            st.metric(
                "爬取速度", 
                f"{crawl_speed:.1f} 页/分钟",
                "🚀" if crawl_speed > 10 else "📈"
            )
        
        with col4:
            st.metric(
                "数据量", 
                f"{self.stats['bytes_downloaded'] / 1024 / 1024:.1f} MB",
                f"深度 {self.stats['current_depth']}/{self.stats['max_depth']}"
            )
        
        # 进度条
        if self.stats['total_urls'] > 0:
            progress = self.stats['crawled_urls'] / self.stats['total_urls']
            st.progress(progress)
            st.caption(f"总进度: {self.stats['crawled_urls']}/{self.stats['total_urls']} ({progress*100:.1f}%)")
        
        # 实时图表
        if len(self.timeline) > 1:
            self.render_realtime_chart()
        
        # 详细统计
        self.render_detailed_stats()
    
    def render_realtime_chart(self):
        """渲染实时图表"""
        df = pd.DataFrame(self.timeline)
        df['time_elapsed'] = (df['timestamp'] - self.start_time) / 60  # 转换为分钟
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('爬取进度', '成功/失败趋势'),
            vertical_spacing=0.1
        )
        
        # 爬取进度线
        fig.add_trace(
            go.Scatter(
                x=df['time_elapsed'], 
                y=df['crawled'],
                mode='lines+markers',
                name='成功爬取',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
        
        # 失败趋势
        fig.add_trace(
            go.Scatter(
                x=df['time_elapsed'], 
                y=df['failed'],
                mode='lines+markers',
                name='失败',
                line=dict(color='red', width=2)
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            title_text="实时爬取监控"
        )
        
        fig.update_xaxes(title_text="时间 (分钟)")
        fig.update_yaxes(title_text="页面数量")
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_detailed_stats(self):
        """渲染详细统计"""
        with st.expander("📊 详细统计", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("爬取统计")
                st.write(f"• 总URL数: {self.stats['total_urls']}")
                st.write(f"• 成功爬取: {self.stats['crawled_urls']}")
                st.write(f"• 失败数量: {self.stats['failed_urls']}")
                st.write(f"• 重复内容: {self.stats['duplicate_content']}")
                st.write(f"• robots.txt阻止: {self.stats['robots_blocked']}")
            
            with col2:
                st.subheader("性能指标")
                elapsed = time.time() - self.start_time
                st.write(f"• 运行时间: {elapsed/60:.1f} 分钟")
                st.write(f"• 平均速度: {self.stats['crawled_urls']/(elapsed/60):.1f} 页/分钟")
                st.write(f"• 数据下载: {self.stats['bytes_downloaded']/1024/1024:.2f} MB")
                st.write(f"• 当前深度: {self.stats['current_depth']}/{self.stats['max_depth']}")

class AsyncCrawlUI:
    """异步爬虫UI包装器"""
    
    def __init__(self):
        self.monitor = CrawlProgressMonitor()
        self.status_container = None
        self.progress_container = None
    
    def setup_ui(self):
        """设置UI容器"""
        st.subheader("🚀 异步并发爬虫")
        
        # 配置区域
        col1, col2, col3 = st.columns(3)
        with col1:
            max_concurrent = st.slider("并发数", 5, 50, 15)
        with col2:
            enable_dedup = st.checkbox("内容去重", True)
        with col3:
            check_robots = st.checkbox("robots.txt检查", True)
        
        # 进度显示区域
        self.progress_container = st.container()
        self.status_container = st.empty()
        
        return {
            'max_concurrent': max_concurrent,
            'enable_dedup': enable_dedup,
            'check_robots': check_robots
        }
    
    def update_progress(self, message: str, stats: Dict = None):
        """更新进度显示"""
        self.status_container.info(f"🔄 {message}")
        
        if stats:
            self.monitor.update_stats(**stats)
            
            with self.progress_container:
                self.monitor.render_progress_dashboard()
    
    def show_completion(self, results: Dict):
        """显示完成结果"""
        self.status_container.success(f"✅ 爬取完成！")
        
        # 最终统计
        st.balloons()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总页面", results.get('total_pages', 0))
        with col2:
            st.metric("成功率", f"{results.get('success_rate', 0):.1f}%")
        with col3:
            st.metric("总用时", f"{results.get('total_time', 0):.1f}分钟")

# 使用示例
def demo_progress_monitor():
    """演示进度监控"""
    monitor = CrawlProgressMonitor()
    
    # 模拟爬取过程
    for i in range(10):
        time.sleep(0.5)
        monitor.update_stats(
            total_urls=100,
            crawled_urls=i*10,
            failed_urls=i*2,
            bytes_downloaded=i*1024*1024,
            current_depth=min(i//3 + 1, 5),
            max_depth=5
        )
        monitor.render_progress_dashboard()
        time.sleep(1)

if __name__ == "__main__":
    demo_progress_monitor()
