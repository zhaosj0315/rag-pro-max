"""
主页知识库界面 - 极简版
"""

import streamlit as st
import time
from src.ui.kb_management_ui import get_knowledge_base_list, create_knowledge_base

def render_main_kb_interface():
    """渲染极简的主页知识库界面 - 只显示核心功能"""
    
    # 获取知识库列表
    kb_list = get_knowledge_base_list()
    
    if kb_list:
        # 已有知识库 - 显示选择器（包含新建选项）
        st.markdown("#### 📚 选择知识库")
        
        # 获取当前选中的知识库
        current_kb = st.session_state.get('current_kb_id', '')
        
        # 按创建时间倒序排列知识库（最新的在前面）
        kb_names = [kb['name'] for kb in sorted(kb_list, key=lambda x: x.get('created_time', ''), reverse=True)]
        
        # 添加新建选项到列表（放在最后）
        options = [""] + kb_names + ["+ 新建知识库"]
        
        selected_kb = st.selectbox(
            "当前知识库",
            options,
            index=len(options)-1 if not current_kb else (kb_names.index(current_kb) + 1 if current_kb in kb_names else len(options)-1),
            format_func=lambda x: "请选择知识库..." if x == "" else f"📂 {x}" if x != "+ 新建知识库" else "➕ 新建知识库",
            key="main_kb_selector"
        )
        
        # 处理选择
        if selected_kb == "+ 新建知识库":
            # 显示简洁提示，不显示创建表单
            st.info("💡 请使用侧边栏的知识库管理功能创建新知识库")
        elif selected_kb and selected_kb != current_kb and selected_kb != "+ 新建知识库":
            # 自动切换知识库
            st.session_state.current_kb_id = selected_kb
            st.session_state.chat_engine = None
            st.success(f"✅ 已切换到: {selected_kb}")
            st.rerun()
        
        # 显示当前知识库信息
        if selected_kb and selected_kb != "+ 新建知识库":
            kb_info = next((kb for kb in kb_list if kb['name'] == selected_kb), None)
            if kb_info:
                st.caption(f"📄 {kb_info.get('doc_count', 0)}个文档 | 💬 {kb_info.get('chat_count', 0)}次对话")
    
    else:
        # 没有知识库 - 仍然显示下拉框（只有新建选项）
        st.markdown("#### 📚 选择知识库")
        
        options = ["", "+ 新建知识库"]
        
        selected_kb = st.selectbox(
            "当前知识库",
            options,
            index=1,  # 默认选择新建知识库
            format_func=lambda x: "请选择知识库..." if x == "" else "➕ 新建知识库",
            key="main_kb_selector"
        )
        
        # 处理选择
        if selected_kb == "+ 新建知识库":
            # 显示简洁提示，不显示创建表单
            st.info("💡 请使用侧边栏的知识库管理功能创建新知识库")
    
    return st.session_state.get('current_kb_id')

def render_quick_create():
    """快速创建知识库"""
    # 获取自动生成的名称和描述，并清理特殊字符
    raw_auto_name = st.session_state.get('upload_auto_name', '')
    # 清理自动生成的名称
    auto_name = ""
    if raw_auto_name:
        auto_name = raw_auto_name.replace('"', '').replace("'", '').replace('/', '_').replace('\\', '_').strip()
    
    auto_description = generate_auto_description(auto_name)
    
    # 显示智能建议
    if auto_name:
        st.caption(f"💡 建议名称：{auto_name}")
    
    kb_name = st.text_input(
        "知识库名称", 
        value=auto_name if auto_name else "",
        placeholder="例如：我的文档库",
        key="quick_kb_name"
    )
    
    if st.button("🚀 创建知识库", type="primary", key="create_kb_btn"):
        # 如果用户没输入名称，使用自动生成的
        final_kb_name = kb_name.strip() if kb_name.strip() else auto_name
        
        # 再次清理知识库名称，确保安全
        if final_kb_name:
            final_kb_name = final_kb_name.replace('"', '').replace("'", '').replace('/', '_').replace('\\', '_').strip()
            
            success = create_knowledge_base(final_kb_name, "📚 通用文档", auto_description, {
                'chunk_size': 500,
                'chunk_overlap': 50,
                'enable_ocr': False,
                'enable_summary': False
            })
            
            if success:
                st.success(f"✅ 创建成功: {final_kb_name}")
                st.session_state.current_kb_id = final_kb_name
                st.session_state.chat_engine = None
                # 清空自动生成的名称，避免重复使用
                st.session_state.upload_auto_name = ""
                st.rerun()
            else:
                st.error("❌ 创建失败，名称可能重复")
        else:
            st.error("❌ 请输入知识库名称")

def generate_auto_description(kb_name):
    """根据知识库名称自动生成描述"""
    if not kb_name:
        return ""
    
    # 简单的描述生成逻辑
    from datetime import datetime
    
    # 根据名称特征生成描述
    if "新闻" in kb_name or "News" in kb_name:
        return f"包含新闻资讯的知识库，创建于{datetime.now().strftime('%Y年%m月%d日')}"
    elif "技术" in kb_name or "Tech" in kb_name or "代码" in kb_name:
        return f"技术文档和代码相关的知识库，用于技术学习和参考"
    elif "学习" in kb_name or "Study" in kb_name or "课程" in kb_name:
        return f"学习资料和课程内容的知识库，便于知识管理和复习"
    elif "工作" in kb_name or "Work" in kb_name or "项目" in kb_name:
        return f"工作相关文档和项目资料的知识库，提升工作效率"
    else:
        return f"基于'{kb_name}'的文档知识库，创建于{datetime.now().strftime('%Y年%m月%d日')}"
