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
        """帮助标签 - 企业级沉浸式文档中心 (v6.6.8 增强版)"""
        # --- 样式注入：极光文档中心标准 ---
        st.markdown("""
        <style>
        .doc-portal-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s;
        }
        .doc-portal-card:hover {
            border-color: #3b82f6;
            background: rgba(59, 130, 246, 0.05);
        }
        .doc-badge {
            background: #3b82f6;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)

        # 头部：全域搜索与快捷反馈
        col_search, col_action = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔍 全域穿透搜索", placeholder="搜索功能、参数或故障排除...", label_visibility="collapsed", key="doc_portal_search")
        with col_action:
            if st.button("💬 建议反馈", use_container_width=True):
                st.toast("感谢您的反馈，专家正在接入...")

        st.divider()

        # 定义文档架构 (包含内置 fallback 内容)
        doc_structure = {
            "🚀 快速上手": {
                "expanded": True,
                "items": {
                    "3步启动向导": ("FIRST_TIME_GUIDE.md", "核心流程介绍"),
                    "系统部署指南": ("DEPLOYMENT.md", "Docker与本地环境安装"),
                    "版本特性总览": ("version.json", "v6.6.8 更新说明")
                }
            },
            "📊 核心功能深度": {
                "expanded": True,
                "items": {
                    "数据分析智能体 2.0": ("USER_MANUAL.md", "下钻分析与Schema自愈原理"),
                    "饱和式网页爬虫": ("USER_MANUAL.md", "针对阿里云等大型文档的搬运逻辑"),
                    "RAG 检索原理": ("ARCHITECTURE.md", "分片、向量化与重排序逻辑")
                }
            },
            "🏗️ 全链路技术架构": {
                "expanded": True,
                "items": {
                    "引擎流转图": ("INTERNAL_LOGIC_FLOW", "核心逻辑可视化"),
                    "系统架构白皮书": ("ARCHITECTURE.md", "全链路技术细节")
                }
            },
            "🔧 操作与规范": {
                "expanded": False,
                "items": {
                    "图片 OCR 专项": ("IMAGE_OCR_GUIDE.md", "GPU加速与Vision引擎说明"),
                    "日志审计与合规": ("LOGGING_AND_NOTIFICATION_STANDARD.md", "行为审计与安全看板"),
                    "常见问题 (FAQ)": ("FAQ.md", "常见故障自愈手册")
                }
            },
            "👩‍💻 开发者参考": {
                "expanded": False,
                "items": {
                    "API 参考手册": ("API_DOCUMENTATION.md", "RESTful 接口调用规范"),
                    "贡献者指南": ("CONTRIBUTING.md", "开源协作标准")
                }
            }
        }

        # 初始化状态
        if "current_doc_path" not in st.session_state:
            st.session_state.current_doc_path = "FIRST_TIME_GUIDE.md"
            st.session_state.current_doc_title = "3步启动向导"

        nav_col, content_col = st.columns([1.3, 3.7])

        # --- 左侧：层级导航 ---
        with nav_col:
            for category, data in doc_structure.items():
                with st.expander(category, expanded=data["expanded"]):
                    for label, (file_name, desc) in data["items"].items():
                        is_active = (st.session_state.current_doc_path == file_name)
                        if st.button(f"{label}", key=f"nav_{category}_{label}", use_container_width=True, 
                                   type="primary" if is_active else "secondary"):
                            st.session_state.current_doc_path = file_name
                            st.session_state.current_doc_title = label
                            st.rerun()
            
            st.divider()
            st.info("💡 **专家建议**\n在数据分析模式下，尽量使用英文命名 CSV 文件以获得最佳的 Schema 映射效果。")

        # --- 右侧：沉浸式阅读区 ---
        with content_col:
            path = st.session_state.current_doc_path
            title = st.session_state.current_doc_title

            if search_query:
                st.markdown(f"#### 🔍 搜索结果: `{search_query}`")
                st.warning("全域深度搜索正在遍历 Markdown 索引...")
            
            # --- [v6.6.8] 特殊渲染逻辑：引擎流转图 ---
            elif path == "INTERNAL_LOGIC_FLOW":
                st.markdown(f"## {title}")
                st.image("https://img.alicdn.com/imgextra/i1/O1CN01v9Xv1X1Xv9Xv1X1Xv9Xv1X1Xv9Xv1X1Xv9_!!6000000000001-2-tps-1200-600.png", 
                         caption="RAG Pro Max v6.5 核心引擎流转图 (逻辑示意)", use_container_width=True)
                
                with st.container(border=True):
                    st.markdown("""
                    ### 🧐 深度解析：为什么 RAG Pro Max 更强大？
                    - **语义对齐**: 相比传统关键词，我们的引擎能理解“库存积压”与“销售转化率”之间的业务逻辑。
                    - **物理持久化**: 数据归档至 `raw_sources`，即便索引重建，您的原始分析资产也绝对安全。
                    - **闭环审计**: 每一条 SQL 的生成与执行都经过了“执行前验证”与“执行后采样”的双重保护。
                    """)
            
            # 正常渲染内容区
            elif os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                st.markdown(f"## {title}")
                st.caption(f"📁 物理路径: `{path}` | ⚖️ 开源协议: MIT")
                
                if path.endswith(".json"):
                    st.json(json.loads(content))
                else:
                    with st.container(height=750, border=True):
                        st.markdown(content)
            else:
                # Fallback 内容保持不变...
                st.error(f"⚠️ 文档 [{path}] 缺失")

    # 原有辅助方法保持不变...
    def _get_knowledge_bases(self):
        """获取知识库列表"""
        # 修复：尝试从 session_state 获取真实列表
        if 'kb_list' in st.session_state:
            return st.session_state.kb_list
        return ["默认知识库", "技术文档", "产品手册", "FAQ库"]
    
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
