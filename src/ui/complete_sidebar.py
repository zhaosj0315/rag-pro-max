"""
完整侧边栏管理模块
负责整个侧边栏的渲染和配置管理
"""

import streamlit as st
import time
import psutil
import subprocess
import os
from src.config import ConfigLoader
from src.ui.config_forms import render_basic_config
from src.kb import KBManager
# from src.ui.performance_dashboard import render_performance_dashboard  # 已删除冗余模块


class CompleteSidebar:
    """完整侧边栏管理器"""
    
    def __init__(self, defaults, output_base):
        self.defaults = defaults
        self.output_base = output_base
        self.kb_manager = KBManager()
        self.kb_manager.base_path = output_base
    
    def render(self):
        """渲染完整侧边栏"""
        with st.sidebar:
            # 快速开始
            self._render_quick_start()
            
            # 基础配置
            config_values = self._render_basic_config()
            
            # 高级功能
            advanced_config = self._render_advanced_config()
            
            # 知识库管理
            kb_config = self._render_kb_management()
            
            # 系统工具
            self._render_system_tools()
            
            return {
                'config': config_values,
                'advanced': advanced_config,
                'kb': kb_config
            }
    
    def _render_quick_start(self):
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
    
    def _render_basic_config(self):
        """渲染基础配置"""
        return render_basic_config(self.defaults)
    
    def _render_advanced_config(self):
        """渲染高级配置"""
        with st.expander("🔧 高级功能", expanded=False):
            # Re-ranking 配置
            enable_rerank = st.checkbox("🎯 启用 Re-ranking 重排序", value=False, 
                                      help="使用 Cross-Encoder 模型对检索结果重新排序，提升准确率 10-20%")
            
            rerank_model = "BAAI/bge-reranker-base"
            if enable_rerank:
                rerank_model = st.selectbox("Re-ranking 模型", 
                                          ["BAAI/bge-reranker-base", "BAAI/bge-reranker-large"],
                                          help="选择重排序模型")
            
            # BM25 混合检索
            enable_bm25 = st.checkbox("🔍 启用 BM25 混合检索", value=False,
                                    help="结合关键词检索和语义检索，提升准确率 5-10%")
            
            # 保存到 session state
            st.session_state.enable_rerank = enable_rerank
            st.session_state.rerank_model = rerank_model
            st.session_state.enable_bm25 = enable_bm25
            
            return {
                'enable_rerank': enable_rerank,
                'rerank_model': rerank_model,
                'enable_bm25': enable_bm25
            }
    
    def _render_kb_management(self):
        """渲染知识库管理"""
        st.markdown("---")
        st.markdown("### 📚 知识库管理")
        
        # 获取现有知识库
        existing_kbs = self._get_existing_kbs()
        
        # 知识库选择
        kb_options = ["创建新知识库"] + [f"📂 {kb}" for kb in existing_kbs]
        current_nav = st.selectbox(
            "选择知识库",
            kb_options,
            key="current_nav",
            help="选择现有知识库或创建新的"
        )
        
        # 知识库操作
        if current_nav != "创建新知识库":
            kb_name = current_nav.replace("📂 ", "")
            
            # 知识库信息
            kb_info = self.kb_manager.get_info(kb_name)
            if kb_info:
                st.caption(f"📄 {kb_info.get('file_count', 0)} 个文件")
                st.caption(f"📅 {kb_info.get('created_at', 'N/A')[:10]}")
            
            # 知识库操作按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 删除", use_container_width=True):
                    if st.session_state.get('confirm_delete'):
                        success, msg = self.kb_manager.delete(kb_name)
                        if success:
                            st.success("✅ 已删除")
                            st.session_state.current_nav = "创建新知识库"
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"删除失败: {msg}")
                    else:
                        st.session_state.confirm_delete = True
                        st.warning("再次点击确认删除")
            
            with col2:
                if st.button("📊 详情", use_container_width=True):
                    st.session_state.show_kb_details = True
        
        else:
            # 创建新知识库
            final_kb_name = st.text_input("知识库名称", placeholder="输入知识库名称...")
            
            # 数据源配置
            st.markdown("**📁 数据源**")
            target_path = st.text_input("文档路径", placeholder="拖拽文件夹或输入路径...")
            
            # 处理模式
            action_mode = st.radio("处理模式", ["NEW", "APPEND"], horizontal=True)
            
            # 创建按钮
            btn_start = st.button("🚀 立即创建", type="primary", use_container_width=True)
            
            return {
                'kb_name': final_kb_name,
                'target_path': target_path,
                'action_mode': action_mode,
                'btn_start': btn_start,
                'current_nav': current_nav
            }
        
        return {'current_nav': current_nav}
    
    def _render_system_tools(self):
        """渲染系统工具"""
        with st.expander("🛠️ 系统工具", expanded=False):
            # 性能监控面板
            if st.button("🚀 性能监控面板"):
                # render_performance_dashboard()  # 已删除冗余模块
                st.info("性能监控功能已迁移到系统监控中")
            
            # 系统监控
            auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="monitor_auto_refresh")
            
            # 获取系统信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/System/Volumes/Data')
            
            # 显示系统信息
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💻 CPU", f"{cpu_percent:.1f}%")
                st.metric("💾 内存", f"{mem.percent:.1f}%")
            with col2:
                st.metric("💿 磁盘", f"{disk.percent:.1f}%")
                gpu_status = self._detect_gpu()
                st.metric("🎮 GPU", "🟢 活跃" if gpu_status else "⚪ 空闲")
            
            # 工具按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 清理缓存", use_container_width=True):
                    from src.utils.memory import cleanup_memory
                    cleanup_memory()
                    st.success("✅ 缓存已清理")
            
            with col2:
                if st.button("📊 系统信息", use_container_width=True):
                    self._show_system_info()
            
            # 自动刷新
            if auto_refresh:
                time.sleep(2)
                st.rerun()
    
    def _get_existing_kbs(self):
        """获取现有知识库列表"""
        try:
            if not os.path.exists(self.output_base):
                os.makedirs(self.output_base)
            return [d for d in os.listdir(self.output_base) 
                    if os.path.isdir(os.path.join(self.output_base, d)) and not d.startswith('.')]
        except:
            return []
    
    def _detect_gpu(self):
        """检测 GPU 状态"""
        try:
            result = subprocess.run(['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                                  capture_output=True, text=True, timeout=1)
            return 'PerformanceStatistics' in result.stdout
        except:
            return False
    
    def _show_system_info(self):
        """显示系统信息"""
        import platform
        
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
