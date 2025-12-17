"""
响应式布局管理器
"""

import streamlit as st

class ResponsiveLayout:
    def __init__(self):
        self.is_mobile = self.detect_mobile_mode()
    
    def detect_mobile_mode(self):
        """检测是否为移动模式"""
        return st.session_state.get('mobile_mode', False)
    
    def create_responsive_columns(self, desktop_ratios, mobile_ratios=None):
        """创建响应式列布局"""
        if self.is_mobile and mobile_ratios:
            return st.columns(mobile_ratios)
        else:
            return st.columns(desktop_ratios)
    
    def mobile_container(self):
        """移动端容器"""
        if self.is_mobile:
            return st.container()
        else:
            return st.container()
    
    def responsive_sidebar(self):
        """响应式侧边栏"""
        if self.is_mobile:
            # 移动端使用expander代替侧边栏
            return st.expander("📱 菜单", expanded=False)
        else:
            return st.sidebar
    
    def mobile_tabs(self, tab_names):
        """移动端标签页优化"""
        if self.is_mobile:
            # 移动端使用选择框代替标签页
            selected_tab = st.selectbox("选择功能", tab_names)
            return selected_tab, tab_names.index(selected_tab)
        else:
            tabs = st.tabs(tab_names)
            return tabs, None

# 全局响应式布局实例
responsive_layout = ResponsiveLayout()
