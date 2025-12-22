"""
侧边栏配置模块
负责侧边栏的所有配置界面和交互逻辑
"""

import streamlit as st
import time
import psutil
import subprocess
from src.config import ConfigLoader
from src.ui.config_forms import render_basic_config
from src.ui.industry_config_interface import IndustryConfigInterface


class SidebarConfig:
    """侧边栏配置管理器"""
    
    @staticmethod
    def render_sidebar(defaults, perf_monitor):
        """渲染完整的侧边栏"""
        with st.sidebar:
            # 快速开始
            config_values = SidebarConfig._render_quick_start(defaults)
            
            # 高级功能
            advanced_config = SidebarConfig._render_advanced_config()
            
            # 行业网站配置
            SidebarConfig._render_industry_config()
            
            # 性能监控
            perf_monitor.render_panel()
            
            # 系统工具
            SidebarConfig._render_system_tools()
            
            return config_values, advanced_config
    
    @staticmethod
    def _render_industry_config():
        """渲染行业网站配置"""
        st.markdown("---")
        st.markdown("### 🔧 网站配置")
        
        if st.button("🌐 配置行业网站", use_container_width=True):
            st.session_state.show_industry_config = True
        
        # 快速预览
        try:
            interface = IndustryConfigInterface()
            interface.render_quick_config()
        except Exception as e:
            st.caption(f"配置预览加载失败: {str(e)[:50]}...")
    
    @staticmethod
    def _render_quick_start(defaults):
        """渲染快速开始区域"""
        st.markdown("### ⚡ 快速开始")
        
        if st.button("⚡ 一键配置（推荐新手）", type="primary", use_container_width=True, 
                    help="自动配置默认设置，1分钟开始使用"):
            ConfigLoader.quick_setup()
            st.success("✅ 已使用默认配置！\n\n💡 下一步：创建知识库 → 上传文档 → 开始对话")
            time.sleep(2)
            st.rerun()
        
        st.caption("💡 或手动配置（高级用户）")
        st.markdown("---")
        
        # 基础配置
        config_values = render_basic_config(defaults)
        return config_values
    
    @staticmethod
    def _render_advanced_config():
        """渲染高级配置 (优化版)"""
        with st.expander("🔧 高级功能", expanded=False):
            # 使用卡片式布局
            with st.container(border=True):
                st.caption("🎯 检索增强策略")
                
                # 双列布局：Re-ranking 和 BM25
                col1, col2 = st.columns(2)
                
                with col1:
                    enable_rerank = st.checkbox("Re-ranking 重排序", value=False, 
                                              help="使用 Cross-Encoder 模型对检索结果重新排序，提升准确率 10-20%")
                
                with col2:
                    enable_bm25 = st.checkbox("BM25 混合检索", value=False,
                                            help="结合关键词检索和语义检索，提升准确率 5-10%")
                
                # 如果开启 Re-ranking，显示模型选择
                rerank_model = "BAAI/bge-reranker-base"
                if enable_rerank:
                    st.divider()
                    rerank_model = st.selectbox(
                        "Re-ranking 模型", 
                        ["BAAI/bge-reranker-base", "BAAI/bge-reranker-large"],
                        help="选择重排序模型",
                        label_visibility="collapsed"
                    )
                    st.caption(f"当前模型: {rerank_model}")
            
            return {
                'enable_rerank': enable_rerank,
                'rerank_model': rerank_model,
                'enable_bm25': enable_bm25
            }
    
    @staticmethod
    def _render_system_tools():
        """渲染系统工具"""
        with st.expander("🛠️ 系统工具", expanded=False):
            # 系统监控
            auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="monitor_auto_refresh")
            
            monitor_placeholder = st.empty()
            
            # 获取系统信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/System/Volumes/Data')
            
            # GPU 检测
            gpu_active = SidebarConfig._detect_gpu()
            
            # 显示系统信息
            with monitor_placeholder.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💻 CPU", f"{cpu_percent:.1f}%")
                    st.metric("💾 内存", f"{mem.percent:.1f}%")
                with col2:
                    st.metric("💿 磁盘", f"{disk.percent:.1f}%")
                    st.metric("🎮 GPU", "🟢 活跃" if gpu_active else "⚪ 空闲")
            
            # 自动刷新
            if auto_refresh:
                time.sleep(2)
                st.rerun()
            
            # 其他工具
            SidebarConfig._render_other_tools()
    
    @staticmethod
    def _detect_gpu():
        """检测 GPU 状态"""
        try:
            result = subprocess.run(['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                                  capture_output=True, text=True, timeout=1)
            return 'PerformanceStatistics' in result.stdout
        except:
            return False
    
    @staticmethod
    def _render_other_tools():
        """渲染其他工具"""
        st.markdown("**🔧 其他工具**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 清理缓存", use_container_width=True):
                from src.utils.memory import cleanup_memory
                cleanup_memory()
                st.success("✅ 缓存已清理")
        
        with col2:
            if st.button("📊 系统信息", use_container_width=True):
                SidebarConfig._show_system_info()
    
    @staticmethod
    def _show_system_info():
        """显示系统信息"""
        import platform
        import os
        
        info = {
            "系统": platform.system(),
            "版本": platform.release(),
            "架构": platform.machine(),
            "Python": platform.python_version(),
            "CPU 核心": os.cpu_count(),
        }
        
        for key, value in info.items():
            st.caption(f"**{key}**: {value}")
    
    @staticmethod
    def extract_config_values(config_values):
        """提取配置值"""
        return {
            'llm_provider': config_values['llm_provider'],
            'llm_url': config_values['llm_url'],
            'llm_model': config_values['llm_model'],
            'llm_key': config_values['llm_key'],
            'embed_provider': config_values['embed_provider'],
            'embed_model': config_values['embed_model'],
            'embed_url': config_values['embed_url'],
            'embed_key': config_values['embed_key']
        }
