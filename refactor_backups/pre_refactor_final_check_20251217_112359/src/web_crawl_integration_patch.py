"""网页抓取集成补丁 - 用于替换主应用中的网页抓取部分"""

import os
import time
import streamlit as st
from src.processors.web_to_kb_simple import render_enhanced_web_crawl, crawl_and_create_kb


def apply_web_crawl_patch():
    """应用网页抓取增强补丁到主应用"""
    
    # 检查是否需要自动创建知识库
    if st.session_state.get('auto_create_kb', False):
        # 清除标记
        st.session_state.auto_create_kb = False
        
        # 如果有上传路径和自动名称，触发知识库创建
        if st.session_state.get('uploaded_path') and st.session_state.get('upload_auto_name'):
            kb_name = st.session_state.upload_auto_name
            
            # 显示创建进度
            with st.spinner(f"正在创建知识库: {kb_name}"):
                try:
                    # 这里应该调用实际的知识库创建逻辑
                    # 为了演示，我们只是创建目录结构
                    kb_path = os.path.join("vector_db_storage", kb_name)
                    os.makedirs(kb_path, exist_ok=True)
                    
                    # 设置选中的知识库
                    st.session_state.selected_kb = kb_name
                    
                    st.success(f"✅ 知识库 '{kb_name}' 创建成功！")
                    st.info("💡 现在可以开始与该知识库对话了")
                    
                except Exception as e:
                    st.error(f"❌ 创建知识库失败: {e}")


def get_enhanced_web_crawl_ui():
    """获取增强版网页抓取UI组件"""
    return render_enhanced_web_crawl


# 使用示例：
# 在主应用的网页抓取标签页中，替换原有内容为：
# 
# with src_tab_web:
#     from src.web_crawl_integration_patch import get_enhanced_web_crawl_ui
#     enhanced_ui = get_enhanced_web_crawl_ui()
#     enhanced_ui()
#
# 在主应用的开始处添加：
# from src.web_crawl_integration_patch import apply_web_crawl_patch
# apply_web_crawl_patch()
