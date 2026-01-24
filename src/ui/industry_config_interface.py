"""
行业网站配置界面
用户可以自定义每个行业的网站列表
"""

import streamlit as st
from src.services.configurable_industry_service import get_configurable_industry_service

class IndustryConfigInterface:
    """行业网站配置界面"""
    
    def __init__(self):
        self.service = get_configurable_industry_service()
    
    def render(self):
        """渲染配置界面"""
        st.title("🔧 行业网站配置")
        
        # 选择配置模式
        mode = st.radio("选择操作", ["管理现有行业", "添加新行业"], horizontal=True)
        
        if mode == "管理现有行业":
            self._render_manage_existing()
        else:
            self._render_add_industry()
    
    def _render_manage_existing(self):
        """管理现有行业"""
        industries = self.service.get_all_industries()
        
        if not industries:
            st.warning("暂无配置的行业，请先添加新行业")
            return
        
        # 选择要管理的行业
        selected_industry = st.selectbox("选择要管理的行业", industries)
        
        if selected_industry:
            st.markdown(f"##### 管理 {selected_industry}")
            
            # 显示当前网站列表
            sites = self.service.get_industry_sites(selected_industry)
            
            st.write("#### 当前网站列表")
            
            # 编辑现有网站
            for i, site in enumerate(sites):
                with st.expander(f"📝 {site['name']}", expanded=False):
                    col1, col2, col3 = st.columns([3, 3, 2])
                    
                    with col1:
                        new_name = st.text_input("网站名称", value=site['name'], key=f"name_{i}")
                    with col2:
                        new_url = st.text_input("网站URL", value=site['url'], key=f"url_{i}")
                    with col3:
                        new_priority = st.number_input("优先级", min_value=1, max_value=100, 
                                                     value=site.get('priority', 10), key=f"priority_{i}")
                    
                    col_update, col_delete = st.columns(2)
                    with col_update:
                        if st.button("更新", key=f"update_{i}"):
                            self.service.update_site(selected_industry, i, new_name, new_url, new_priority)
                            st.success("更新成功！")
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ 删除", key=f"delete_{i}"):
                            self.service.remove_site(selected_industry, i)
                            st.success("删除成功！")
                            st.rerun()
            
            # 添加新网站
            st.write("#### 添加新网站")
            with st.form(f"add_site_{selected_industry}"):
                col1, col2, col3 = st.columns([3, 3, 2])
                
                with col1:
                    new_site_name = st.text_input("网站名称")
                with col2:
                    new_site_url = st.text_input("网站URL")
                with col3:
                    new_site_priority = st.number_input("优先级", min_value=1, max_value=100, value=10)
                
                if st.form_submit_button("➕ 添加网站"):
                    if new_site_name and new_site_url:
                        self.service.add_site(selected_industry, new_site_name, new_site_url, new_site_priority)
                        st.success(f"已添加网站: {new_site_name}")
                        st.rerun()
                    else:
                        st.error("请填写网站名称和URL")
            
            # 删除整个行业
            st.write("#### 危险操作")
            if st.button(f"🗑️ 删除整个行业: {selected_industry}", type="secondary"):
                if st.session_state.get(f"confirm_delete_{selected_industry}"):
                    self.service.remove_industry(selected_industry)
                    st.success(f"已删除行业: {selected_industry}")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{selected_industry}"] = True
                    st.warning("再次点击确认删除")
    
    def _render_add_industry(self):
        """添加新行业"""
        st.markdown("##### ➕ 添加新行业")
        
        with st.form("add_industry"):
            industry_name = st.text_input("行业名称", placeholder="例如: 🎨 设计创意")
            industry_desc = st.text_input("行业描述", placeholder="例如: 平面设计、UI/UX、创意灵感")
            
            # 关键词输入
            keywords_input = st.text_input("关键词", placeholder="用逗号分隔，例如: 设计,UI,创意,平面")
            keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()] if keywords_input else []
            
            if st.form_submit_button("创建行业"):
                if industry_name:
                    self.service.add_industry(industry_name, industry_desc, keywords)
                    st.success(f"已创建行业: {industry_name}")
                    st.rerun()
                else:
                    st.error("请填写行业名称")
    
    def render_quick_config(self):
        """快速配置界面（用于侧边栏）"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 快速配置")
        
        industries = self.service.get_all_industries()
        if industries:
            selected = st.sidebar.selectbox("选择行业", [""] + industries, key="quick_industry")
            if selected:
                sites = self.service.get_industry_sites(selected)
                st.sidebar.write(f"**{selected}** ({len(sites)}个网站)")
                for site in sites[:3]:  # 只显示前3个
                    st.sidebar.write(f"• {site['name']}")
                if len(sites) > 3:
                    st.sidebar.write(f"• ... 还有{len(sites)-3}个")

def render_industry_config_interface():
    """渲染行业配置界面的入口函数"""
    interface = IndustryConfigInterface()
    interface.render()
