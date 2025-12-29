"""
角色管理界面
负责 "🎭 角色" 标签页的渲染和交互
"""

import streamlit as st
from src.config.prompt_manager import PromptManager

class RoleManagerUI:
    """角色管理器 UI"""
    
    @staticmethod
    def render():
        """渲染角色管理界面"""
        st.markdown("### 🎭 角色库管理 (Prompt Library)")
        st.caption("在此管理所有可用的 AI 角色提示词。这些角色可以在对话顶栏中快速切换。")
        
        # 加载提示词
        prompts = PromptManager.load_prompts()
        
        # 布局：左侧列表，右侧编辑/预览
        # 或者使用 Tabs 分离 列表/新增
        
        tab_list, tab_add = st.tabs(["📋 角色列表", "➕ 新增角色"])
        
        with tab_list:
            # 使用卡片式布局展示角色
            for p in prompts:
                with st.expander(f"{p['name']}", expanded=False):
                    # 编辑区域
                    new_name = st.text_input("角色名称", p['name'], key=f"edit_name_{p['id']}")
                    new_content = st.text_area("提示词内容", p['content'], height=150, key=f"edit_content_{p['id']}")
                    
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button("💾 保存", key=f"save_role_{p['id']}"):
                            if new_name and new_content:
                                PromptManager.update_prompt(p['id'], new_name, new_content)
                                st.toast(f"✅ 角色 '{new_name}' 已更新")
                                st.rerun()
                            else:
                                st.warning("名称和内容不能为空")
                    
                    with col2:
                        # 保护默认角色
                        if p['id'] not in ['default', 'coder', 'analyst', 'creative', 'academic']:
                            if st.button("🗑️ 删除", key=f"del_role_{p['id']}"):
                                PromptManager.delete_prompt(p['id'])
                                st.toast("✅ 角色已删除")
                                st.rerun()
                        else:
                            st.caption("🔒 内置角色不可删除")

        with tab_add:
            st.markdown("#### 创建新角色")
            with st.container(border=True):
                add_name = st.text_input("角色名称", placeholder="例如: 法律顾问", key="add_role_name")
                add_content = st.text_area("提示词内容", placeholder="你是一个专业的法律顾问，请基于...", height=200, key="add_role_content")
                
                if st.button("➕ 添加到库", type="primary", key="add_role_btn"):
                    if add_name and add_content:
                        PromptManager.add_prompt(add_name, add_content)
                        st.success(f"✅ 角色 '{add_name}' 已创建")
                        st.rerun()
                    else:
                        st.warning("请填写完整的名称和提示词内容")
