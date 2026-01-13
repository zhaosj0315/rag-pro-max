#!/usr/bin/env python3
"""
多标签页侧边栏组件
"""

import streamlit as st
import os
import json
from typing import Dict, Any, Optional

class TabbedSidebar:
    """多标签页侧边栏管理器"""
    
    def __init__(self):
        self.tabs = {
            "home": {"icon": "🏠", "name": "主页", "key": "home"},
            "config": {"icon": "⚙️", "name": "配置", "key": "config"},
            "monitor": {"icon": "📊", "name": "监控", "key": "monitor"},
            "tools": {"icon": "🔧", "name": "工具", "key": "tools"},
            "help": {"icon": "ℹ️", "name": "帮助", "key": "help"}
        }
        
        # 初始化会话状态
        if 'sidebar_tab' not in st.session_state:
            st.session_state.sidebar_tab = 'home'
    
    def render(self) -> str:
        """渲染侧边栏并返回当前选中的标签页"""
        with st.sidebar:
            # 标签页选择器 - 使用radio实现更好的视觉效果
            tab_options = [f"{tab['icon']} {tab['name']}" for tab in self.tabs.values()]
            tab_keys = list(self.tabs.keys())
            
            # 当前选中的索引
            current_index = tab_keys.index(st.session_state.sidebar_tab) if st.session_state.sidebar_tab in tab_keys else 0
            
            selected_index = st.radio(
                "导航",
                range(len(tab_options)),
                format_func=lambda x: tab_options[x],
                index=current_index,
                key="tab_selector",
                label_visibility="collapsed"
            )
            
            selected_tab = tab_keys[selected_index]
            st.session_state.sidebar_tab = selected_tab
            
            st.divider()
            
            # 渲染对应的标签页内容
            if selected_tab == "home":
                self._render_home_tab()
            elif selected_tab == "config":
                self._render_config_tab()
            elif selected_tab == "monitor":
                self._render_monitor_tab()
            elif selected_tab == "tools":
                self._render_tools_tab()
            elif selected_tab == "help":
                self._render_help_tab()
            
            return selected_tab
    
    def _render_home_tab(self):
        """主页标签 - 核心功能"""
        st.markdown("##### 📚 知识库")
        
        # 知识库管理 - 紧凑布局
        col1, col2 = st.columns([4, 1])
        with col1:
            kb_list = self._get_knowledge_bases()
            selected_kb = st.selectbox(
                "选择知识库",
                kb_list,
                key="kb_selector",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("➕", help="新建知识库", key="new_kb"):
                st.session_state.show_new_kb_dialog = True
        
        # 新建知识库对话框
        if st.session_state.get('show_new_kb_dialog', False):
            with st.container():
                st.text_input("知识库名称", key="new_kb_name", placeholder="输入知识库名称")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("创建", key="create_kb"):
                        # 创建知识库逻辑
                        st.success("知识库创建成功！")
                        st.session_state.show_new_kb_dialog = False
                        st.rerun()
                with col2:
                    if st.button("取消", key="cancel_kb"):
                        st.session_state.show_new_kb_dialog = False
                        st.rerun()
        
        # 文档上传 - 折叠式
        with st.expander("📄 文档管理", expanded=False):
            uploaded_file = st.file_uploader(
                "上传文档",
                type=['pdf', 'docx', 'txt', 'md', 'xlsx', 'pptx'],
                key="file_uploader"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.button("📁 批量上传", key="batch_upload")
            with col2:
                st.button("🗑️ 删除文档", key="delete_doc")
        
        # 快速操作
        st.markdown("##### ⚡ 快速操作")
        
        # 2x2 网格布局
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 搜索", key="search_docs", use_container_width=True):
                st.session_state.sidebar_tab = 'tools'
                st.rerun()
            if st.button("📈 统计", key="view_stats", use_container_width=True):
                st.session_state.sidebar_tab = 'monitor'
                st.rerun()
        with col2:
            if st.button("🧹 清理", key="cleanup", use_container_width=True):
                st.info("清理缓存...")
            if st.button("💾 导出", key="export", use_container_width=True):
                st.info("导出数据...")
    
    def _render_config_tab(self):
        """配置标签 - 系统设置"""
        st.markdown("##### 🤖 模型配置")
        
        # LLM 配置
        with st.expander("🧠 大语言模型", expanded=True):
            llm_type = st.selectbox(
                "模型类型",
                ["OpenAI", "Ollama", "其他"],
                key="llm_type"
            )
            
            if llm_type == "OpenAI":
                st.text_input("API Key", type="password", key="openai_key")
                st.text_input("Base URL", value="https://api.openai.com/v1", key="openai_base")
                st.selectbox("模型", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"], key="openai_model")
            elif llm_type == "Ollama":
                st.text_input("服务地址", value="http://localhost:11434", key="ollama_url")
                st.text_input("模型名称", placeholder="gpt-oss:20b", key="ollama_model")
        
        # 嵌入模型配置
        with st.expander("🔤 嵌入模型"):
            embed_type = st.selectbox(
                "嵌入模型",
                ["BAAI/bge-base-zh-v1.5", "OpenAI", "本地模型"],
                key="embed_type"
            )
            
            if embed_type == "OpenAI":
                st.text_input("嵌入模型", value="text-embedding-ada-002", key="embed_model")
        
        # 高级设置
        with st.expander("🔧 高级设置"):
            col1, col2 = st.columns(2)
            with col1:
                st.slider("温度", 0.0, 1.0, 0.7, 0.1, key="temperature")
                st.slider("Top-K", 1, 20, 5, key="top_k")
            with col2:
                st.slider("Top-P", 0.0, 1.0, 0.9, 0.1, key="top_p")
                st.slider("最大长度", 100, 4000, 2000, 100, key="max_length")
        
        # 保存配置
        if st.button("💾 保存配置", key="save_config", use_container_width=True):
            self._save_config()
            st.success("配置已保存！")
    
    def _render_monitor_tab(self):
        """监控标签 - 系统状态"""
        st.markdown("##### 💻 系统状态")
        
        # 实时指标 - 2x2 网格
        col1, col2 = st.columns(2)
        with col1:
            cpu_usage = self._get_cpu_usage()
            st.metric("CPU", f"{cpu_usage}%", f"{'↑' if cpu_usage > 50 else '↓'}{abs(cpu_usage-45)}%")
            
            memory_usage = self._get_memory_usage()
            st.metric("内存", f"{memory_usage:.1f}GB", "↑0.3GB")
        
        with col2:
            gpu_usage = self._get_gpu_usage()
            st.metric("GPU", f"{gpu_usage}%", f"{'↑' if gpu_usage > 70 else '↓'}{abs(gpu_usage-75)}%")
            
            disk_usage = self._get_disk_usage()
            st.metric("磁盘", f"{disk_usage}GB", "↑1GB")
        
        # 自动刷新开关
        auto_refresh = st.checkbox("🔄 自动刷新", key="auto_refresh")
        if auto_refresh:
            st.rerun()
        
        # 性能图表
        with st.expander("📈 性能趋势", expanded=False):
            import pandas as pd
            import numpy as np
            
            # 模拟数据
            chart_data = pd.DataFrame({
                'CPU': np.random.randint(30, 80, 20),
                'GPU': np.random.randint(40, 90, 20),
                'Memory': np.random.randint(20, 60, 20)
            })
            st.line_chart(chart_data)
        
        # 进程信息
        with st.expander("🔍 进程信息"):
            processes = self._get_process_info()
            for proc in processes:
                st.text(f"{proc['name']}: {proc['cpu']}% CPU, {proc['memory']}MB")
    
    def _render_tools_tab(self):
        """工具标签 - 实用工具"""
        st.markdown("##### 🛠️ 系统工具")
        
        # 工具按钮 - 2x3 网格
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 运行测试", key="run_test", use_container_width=True):
                st.info("正在运行系统测试...")
            
            if st.button("🔄 重启服务", key="restart", use_container_width=True):
                st.warning("重启服务中...")
            
            if st.button("📋 查看日志", key="view_logs", use_container_width=True):
                # 使用紧凑日志显示
                from src.utils.compact_log_display import render_compact_log_management
                with st.container():
                    render_compact_log_management()
        
        with col2:
            if st.button("⚡ 一键配置", key="quick_config", use_container_width=True):
                st.success("快速配置完成！")
            
            if st.button("🚨 紧急停止", key="emergency_stop", use_container_width=True):
                st.error("紧急停止所有进程...")
            
            if st.button("📦 导出配置", key="export_config", use_container_width=True):
                st.info("导出配置文件...")
        
        st.markdown("##### 🔧 维护工具")
        
        # 维护工具
        with st.expander("🧹 清理工具"):
            col1, col2 = st.columns(2)
            with col1:
                st.button("清理缓存", key="clear_cache")
                st.button("清理日志", key="clear_logs")
            with col2:
                st.button("清理临时文件", key="clear_temp")
                st.button("重建索引", key="rebuild_index")
        
        # 数据管理
        with st.expander("💾 数据管理"):
            col1, col2 = st.columns(2)
            with col1:
                st.button("备份数据", key="backup_data")
                st.button("导入数据", key="import_data")
            with col2:
                st.button("恢复数据", key="restore_data")
                st.button("同步数据", key="sync_data")
    
    @st.fragment
    def _render_help_tab(self):
        """帮助标签 - 仿阿里云文档中心 (深度层级版)"""
        # --- 样式注入：专业文档中心 ---
        st.markdown("""
        <style>
        /* 导航树样式 */
        .nav-category {
            font-size: 0.9rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }
        
        /* 选中项高亮 */
        div[data-testid="stVerticalBlock"] button[kind="secondary"] {
            border: none !important;
            text-align: left !important;
            padding-left: 1rem !important;
            color: #64748b !important;
        }
        div[data-testid="stVerticalBlock"] button[kind="primary"] {
            border: none !important;
            border-left: 3px solid #3b82f6 !important;
            text-align: left !important;
            padding-left: 0.8rem !important;
            background: #f1f5f9 !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }
        
        /* 文档标题区 */
        .doc-title-box {
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }
        .doc-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e293b;
        }
        .doc-meta {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- 1. 顶部栏 (搜索 + 版本) ---
        col_search, col_ver = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔍", placeholder="搜索文档...", label_visibility="collapsed", key="doc_deep_search")
        with col_ver:
            st.caption("📚 RAG Pro Max Docs")

        st.divider()

        # --- 2. 双栏布局 ---
        nav_col, content_col = st.columns([1.2, 3.8])

        # 定义深度文档树 (仿阿里云结构)
        # 格式: "显示名称": ("文件名.md", "锚点/备注")
        doc_structure = {
            "产品概述": {
                "expanded": True,
                "items": {
                    "产品简介": "README.md",
                    "功能特性": "version.json",  # 特殊处理
                    "技术白皮书": "ARCHITECTURE.md",
                    "动态与公告": "CHANGELOG.md"
                }
            },
            "快速入门": {
                "expanded": True,
                "items": {
                    "部署指南": "DEPLOYMENT.md",
                    "首次运行向导": "FIRST_TIME_GUIDE.md",
                    "免费公网访问": "FREE_PUBLIC_ACCESS.md"
                }
            },
            "操作指南": {
                "expanded": False,
                "items": {
                    "用户手册 (完整版)": "USER_MANUAL.md",
                    "数据安全": "DOCUMENT_PROTECTION_LIST.md",
                    "OCR 识别指南": "IMAGE_OCR_GUIDE.md",
                    "日志与监控": "LOGGING_AND_NOTIFICATION_STANDARD.md"
                }
            },
            "开发参考": {
                "expanded": False,
                "items": {
                    "API 参考": "API_DOCUMENTATION.md",
                    "内部接口定义": "INTERNAL_API.md",
                    "贡献指南": "CONTRIBUTING.md",
                    "测试标准": "TESTING.md"
                }
            },
            "服务支持": {
                "expanded": False,
                "items": {
                    "常见问题 (FAQ)": "FAQ.md",
                    "相关协议": "LICENSE"
                }
            }
        }

        # 初始化 Session State
        if "current_doc_path" not in st.session_state:
            st.session_state.current_doc_path = "README.md"
            st.session_state.current_doc_title = "产品简介"

        # --- 左侧：折叠式导航树 ---
        with nav_col:
            for category, data in doc_structure.items():
                # 使用 expander 模拟一级菜单
                with st.expander(category, expanded=data["expanded"]):
                    for label, file_name in data["items"].items():
                        is_active = (st.session_state.current_doc_path == file_name)
                        
                        # 点击切换文档
                        if st.button(label, key=f"nav_{category}_{label}", use_container_width=True, 
                                   type="primary" if is_active else "secondary"):
                            st.session_state.current_doc_path = file_name
                            st.session_state.current_doc_title = label
                            st.rerun()

        # --- 右侧：文档内容渲染 ---
        with content_col:
            # 搜索模式拦截
            if search_query:
                st.info(f"🔍 搜索结果: '{search_query}'")
                found_count = 0
                for cat, data in doc_structure.items():
                    for label, fname in data["items"].items():
                        if os.path.exists(fname) and fname.endswith(".md"): # 只搜MD
                            with open(fname, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if search_query.lower() in content.lower():
                                found_count += 1
                                with st.expander(f"{label} ({cat})", expanded=True):
                                    idx = content.lower().find(search_query.lower())
                                    snippet = content[max(0, idx-40):min(len(content), idx+150)]
                                    st.markdown(f"...{snippet.replace(search_query, f'**{search_query}**')}...")
                                    if st.button("阅读", key=f"go_{fname}_{found_count}"):
                                        st.session_state.current_doc_path = fname
                                        st.session_state.current_doc_title = label
                                        # 关键修复：清空搜索框以退出搜索模式
                                        st.session_state.doc_deep_search = ""
                                        st.rerun()
                if found_count == 0:
                    st.warning("未找到相关内容")
            
            # 正常阅读模式
            else:
                path = st.session_state.current_doc_path
                title = st.session_state.current_doc_title
                
                # 渲染页头
                update_time = "2026-01-12 20:00:00"
                if os.path.exists(path):
                    mtime = os.path.getmtime(path)
                    import datetime
                    update_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                st.markdown(f"""
                <div class="doc-title-box">
                    <div class="doc-title">{title}</div>
                    <div class="doc-meta">
                        更新时间：{update_time} &nbsp;|&nbsp; 
                        <span style="color:#3b82f6; cursor:pointer;">📥 下载PDF</span> &nbsp;|&nbsp; 
                        <span style="color:#3b82f6; cursor:pointer;">⭐ 收藏</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 渲染内容
                if path == "version.json":
                    # 特殊渲染 JSON 数据为表格
                    try:
                        with open(path, 'r') as f:
                            v_data = json.load(f)
                        st.json(v_data)
                    except: st.error("版本文件读取失败")
                elif os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    with st.container(height=700):
                        st.markdown(content)
                else:
                    st.warning(f"文档 [{path}] 暂未上传或已移动位置。")
                    st.info("💡 提示：您可以联系管理员补充此文档。")
    
    # 辅助方法
    def _get_knowledge_bases(self):
        """获取知识库列表"""
        # 这里应该从实际的知识库管理器获取
        return ["默认知识库", "技术文档", "产品手册", "FAQ库"]
    
    def _get_cpu_usage(self):
        """获取CPU使用率"""
        import psutil
        return psutil.cpu_percent()
    
    def _get_memory_usage(self):
        """获取内存使用量"""
        import psutil
        return psutil.virtual_memory().used / (1024**3)
    
    def _get_gpu_usage(self):
        """获取GPU使用率"""
        # 简化版本，实际应该调用GPU监控
        import random
        return random.randint(60, 90)
    
    def _get_disk_usage(self):
        """获取磁盘使用量"""
        import psutil
        return psutil.disk_usage('/').used / (1024**3)
    
    def _get_process_info(self):
        """获取进程信息"""
        return [
            {"name": "streamlit", "cpu": 15, "memory": 256},
            {"name": "python", "cpu": 8, "memory": 128},
            {"name": "chrome", "cpu": 12, "memory": 512}
        ]
    
    def _save_config(self):
        """保存配置 - 使用统一服务"""
        from src.services.unified_config_service import save_config
        
        config = {
            "llm_type": st.session_state.get("llm_type"),
            "temperature": st.session_state.get("temperature"),
            "top_k": st.session_state.get("top_k"),
            # 添加其他配置项
        }
        
        save_config(config, "ui_config")

# 使用示例
def create_tabbed_sidebar():
    """创建多标签页侧边栏的便捷函数"""
    sidebar = TabbedSidebar()
    return sidebar.render()
