#!/usr/bin/env python3
"""
RAG Pro Max 优化仪表板
可视化展示优化循环的结果和趋势
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import glob

class OptimizationDashboard:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "optimization_reports"
        
    def load_reports(self) -> list:
        """加载所有优化报告"""
        report_files = glob.glob(str(self.reports_dir / "optimization_report_*.json"))
        reports = []
        
        for file_path in sorted(report_files, reverse=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    report['file_path'] = file_path
                    reports.append(report)
            except Exception as e:
                st.error(f"加载报告失败: {file_path} - {e}")
                
        return reports
    
    def render_dashboard(self):
        """渲染仪表板"""
        st.set_page_config(
            page_title="RAG Pro Max 优化仪表板",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("📊 RAG Pro Max 持续优化仪表板")
        st.markdown("---")
        
        # 加载数据
        reports = self.load_reports()
        
        if not reports:
            st.warning("📭 暂无优化报告数据")
            st.info("运行 `python continuous_optimization_system.py` 生成第一份报告")
            return
        
        # 侧边栏
        self.render_sidebar(reports)
        
        # 主要内容
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_main_metrics(reports)
            self.render_trend_charts(reports)
            
        with col2:
            self.render_latest_report(reports[0])
            self.render_optimization_tasks(reports)
    
    def render_sidebar(self, reports: list):
        """渲染侧边栏"""
        st.sidebar.header("🎛️ 控制面板")
        
        # 报告统计
        st.sidebar.metric("📄 总报告数", len(reports))
        
        if reports:
            latest = reports[0]
            st.sidebar.metric(
                "🕐 最新报告", 
                datetime.fromisoformat(latest['timestamp']).strftime("%m-%d %H:%M")
            )
            
            # 快速操作
            st.sidebar.markdown("### 🚀 快速操作")
            
            if st.sidebar.button("🔄 运行优化循环"):
                self.run_optimization()
            
            if st.sidebar.button("🧹 清理旧报告"):
                self.cleanup_old_reports()
            
            if st.sidebar.button("📊 导出数据"):
                self.export_data(reports)
    
    def render_main_metrics(self, reports: list):
        """渲染主要指标"""
        st.header("📈 核心指标概览")
        
        if not reports:
            return
            
        latest = reports[0]
        metrics = latest.get('metrics', {})
        
        # 创建指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            code_quality = metrics.get('code_quality', {})
            st.metric(
                "📝 代码质量",
                f"{code_quality.get('avg_lines_per_file', 0):.0f}",
                f"行/文件"
            )
        
        with col2:
            performance = metrics.get('performance', {})
            st.metric(
                "⚡ 性能",
                f"{performance.get('cache_size_mb', 0):.0f}MB",
                "缓存大小"
            )
        
        with col3:
            test_coverage = metrics.get('test_coverage', {})
            st.metric(
                "🧪 测试",
                f"{test_coverage.get('test_files', 0)}",
                "测试文件"
            )
        
        with col4:
            issues = latest.get('issues', [])
            st.metric(
                "⚠️ 问题",
                len(issues),
                "待优化项"
            )
    
    def render_trend_charts(self, reports: list):
        """渲染趋势图表"""
        st.header("📊 趋势分析")
        
        if len(reports) < 2:
            st.info("需要至少2份报告才能显示趋势")
            return
        
        # 准备数据
        df_data = []
        for report in reversed(reports[-10:]):  # 最近10份报告
            timestamp = datetime.fromisoformat(report['timestamp'])
            metrics = report.get('metrics', {})
            
            df_data.append({
                'timestamp': timestamp,
                'code_lines': metrics.get('code_quality', {}).get('avg_lines_per_file', 0),
                'cache_size': metrics.get('performance', {}).get('cache_size_mb', 0),
                'issues_count': len(report.get('issues', [])),
                'tasks_completed': report.get('summary', {}).get('tasks_completed', 0)
            })
        
        df = pd.DataFrame(df_data)
        
        # 创建图表
        tab1, tab2, tab3 = st.tabs(["📝 代码质量", "⚡ 性能指标", "🎯 优化效果"])
        
        with tab1:
            fig = px.line(df, x='timestamp', y='code_lines', 
                         title='平均文件行数趋势')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.line(df, x='timestamp', y='cache_size',
                         title='缓存大小趋势 (MB)')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['issues_count'],
                                   mode='lines+markers', name='发现问题'))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['tasks_completed'],
                                   mode='lines+markers', name='完成任务'))
            fig.update_layout(title='优化效果趋势')
            st.plotly_chart(fig, use_container_width=True)
    
    def render_latest_report(self, report: dict):
        """渲染最新报告"""
        st.header("📋 最新报告")
        
        timestamp = datetime.fromisoformat(report['timestamp'])
        st.write(f"**生成时间**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        summary = report.get('summary', {})
        st.write(f"**发现问题**: {summary.get('issues_found', 0)} 个")
        st.write(f"**创建任务**: {summary.get('tasks_created', 0)} 个")
        st.write(f"**完成任务**: {summary.get('tasks_completed', 0)} 个")
        
        # 问题分布
        issues = report.get('issues', [])
        if issues:
            st.subheader("🎯 问题分布")
            categories = {}
            for issue in issues:
                cat = issue.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            fig = px.pie(values=list(categories.values()), 
                        names=list(categories.keys()),
                        title="问题类别分布")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_optimization_tasks(self, reports: list):
        """渲染优化任务"""
        st.header("📝 优化任务")
        
        # 收集所有任务
        all_tasks = []
        for report in reports[:5]:  # 最近5份报告
            tasks = report.get('tasks', [])
            for task in tasks:
                task['report_time'] = report['timestamp']
                all_tasks.append(task)
        
        if not all_tasks:
            st.info("暂无优化任务")
            return
        
        # 任务状态统计
        status_counts = {}
        for task in all_tasks:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ 已完成", status_counts.get('completed', 0))
        with col2:
            st.metric("⏳ 进行中", status_counts.get('in_progress', 0))
        
        # 任务列表
        st.subheader("📋 任务详情")
        for task in all_tasks[:10]:  # 显示最近10个任务
            with st.expander(f"{task.get('category', 'unknown')} - {task.get('description', 'N/A')}"):
                st.write(f"**优先级**: {task.get('priority', 'N/A')}")
                st.write(f"**状态**: {task.get('status', 'N/A')}")
                st.write(f"**创建时间**: {task.get('created_at', 'N/A')}")
                
                action_plan = task.get('action_plan', [])
                if action_plan:
                    st.write("**行动计划**:")
                    for i, action in enumerate(action_plan, 1):
                        st.write(f"{i}. {action}")
    
    def run_optimization(self):
        """运行优化循环"""
        with st.spinner("🔄 正在运行优化循环..."):
            import subprocess
            try:
                result = subprocess.run([
                    "python3", 
                    str(self.project_root / "continuous_optimization_system.py"),
                    str(self.project_root)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    st.success("✅ 优化循环完成！")
                    st.rerun()
                else:
                    st.error(f"❌ 优化循环失败: {result.stderr}")
            except subprocess.TimeoutExpired:
                st.error("⏰ 优化循环超时")
            except Exception as e:
                st.error(f"💥 执行错误: {e}")
    
    def cleanup_old_reports(self):
        """清理旧报告"""
        cutoff_date = datetime.now() - timedelta(days=30)
        cleaned = 0
        
        for report_file in self.reports_dir.glob("optimization_report_*.json"):
            if report_file.stat().st_mtime < cutoff_date.timestamp():
                report_file.unlink()
                cleaned += 1
        
        st.success(f"🧹 已清理 {cleaned} 个旧报告")
    
    def export_data(self, reports: list):
        """导出数据"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'total_reports': len(reports),
            'reports': reports
        }
        
        export_file = self.reports_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        st.success(f"📊 数据已导出到: {export_file}")

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else "/Users/zhaosj/Documents/rag-pro-max"
    
    dashboard = OptimizationDashboard(project_root)
    dashboard.render_dashboard()

if __name__ == "__main__":
    main()
