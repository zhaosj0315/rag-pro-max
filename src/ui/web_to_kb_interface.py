"""网页抓取到知识库的UI界面组件"""

import streamlit as st
from typing import Optional
from ..processors.web_to_kb_processor import WebToKBProcessor


class WebToKBInterface:
    """网页抓取到知识库的UI界面"""
    
    def __init__(self):
        self.processor = WebToKBProcessor()
    
    def render(self):
        """渲染完整的网页抓取到知识库界面"""
        st.subheader("🌐 网页抓取 → 知识库")
        st.write("一键从网页内容创建知识库，支持直接URL抓取或关键词搜索")
        
        # 创建两个标签页
        tab1, tab2 = st.tabs(["📝 直接抓取", "🔍 关键词搜索"])
        
        with tab1:
            self._render_direct_crawl()
        
        with tab2:
            self._render_keyword_search()
    
    def _render_direct_crawl(self):
        """渲染直接URL抓取界面"""
        st.write("### 直接网址抓取")
        
        # URL输入
        url = st.text_input(
            "🌐 网页地址",
            placeholder="https://example.com 或 example.com（自动添加https://）",
            help="支持自动修复URL格式，如输入 'baike.baidu.com' 会自动补全为 'https://baike.baidu.com'"
        )
        
        # 抓取参数
        col1, col2 = st.columns(2)
        with col1:
            max_depth = st.selectbox(
                "🔍 抓取深度",
                options=[1, 2, 3, 4, 5],
                index=0,
                help="1=仅当前页面，2=包含链接页面，以此类推"
            )
        
        with col2:
            max_pages = st.selectbox(
                "📄 最大页面数",
                options=[5, 10, 20, 50, 100],
                index=1,
                help="限制抓取的页面总数，避免过度抓取"
            )
        
        # 高级选项
        with st.expander("⚙️ 高级选项"):
            kb_name = st.text_input(
                "📚 知识库名称（可选）",
                placeholder="留空则自动生成智能名称",
                help="如不填写，系统会根据网页内容自动生成合适的名称"
            )
            
            exclude_patterns = st.text_area(
                "🚫 排除链接模式（可选）",
                placeholder="每行一个模式，支持通配符\n例如：*/admin/*\n*/login*",
                help="使用通配符模式排除不需要的链接，如管理页面、登录页面等"
            )
            
            parser_type = st.selectbox(
                "📖 内容解析模式",
                options=["default", "article", "documentation"],
                index=0,
                help="default=通用模式，article=文章模式，documentation=文档模式"
            )
        
        # 开始抓取按钮
        if st.button("🚀 开始抓取并创建知识库", type="primary", disabled=not url):
            self._execute_direct_crawl(url, max_depth, max_pages, kb_name, exclude_patterns, parser_type)
    
    def _render_keyword_search(self):
        """渲染关键词搜索界面"""
        st.write("### 关键词搜索抓取")
        st.info("💡 通过关键词在知名网站搜索相关内容，然后抓取搜索结果页面")
        
        # 关键词输入
        keyword = st.text_input(
            "🔍 搜索关键词",
            placeholder="例如：卵巢癌、Python编程、机器学习",
            help="输入要搜索的关键词，系统会在选定网站中搜索相关内容"
        )
        
        # 智能推荐
        if keyword:
            recommended_sites = self.processor.recommend_sites_for_keyword(keyword)
            st.info(f"💡 根据关键词 '{keyword}' 智能推荐网站: {', '.join(recommended_sites)}")
        else:
            recommended_sites = ["维基百科", "百度百科"]
        
        # 网站选择 - 按类别分组
        preset_sites = self.processor.get_preset_sites()
        st.write("📍 选择搜索网站：")
        
        # 按类别分组
        categories = {}
        for site_name, site_info in preset_sites.items():
            category = site_info.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append((site_name, site_info))
        
        selected_sites = []
        
        # 百科类网站（默认推荐）
        if "百科" in categories:
            st.write("**📚 百科类网站（推荐用于一般搜索）：**")
            cols = st.columns(2)
            for i, (site_name, site_info) in enumerate(categories["百科"]):
                with cols[i % 2]:
                    # 根据智能推荐决定默认选中状态
                    default_checked = site_name in recommended_sites
                    if st.checkbox(site_name, value=default_checked, key=f"site_{site_name}"):
                        selected_sites.append(site_name)
                    st.caption(site_info["description"])
        
        # 医学专业网站
        if "医学" in categories:
            st.write("**🏥 医学专业网站（推荐用于医疗健康搜索）：**")
            st.info("💡 专业医学网站提供权威的医疗健康信息")
            cols = st.columns(3)
            for i, (site_name, site_info) in enumerate(categories["医学"]):
                with cols[i % 3]:
                    default_checked = site_name in recommended_sites
                    if st.checkbox(site_name, value=default_checked, key=f"site_{site_name}"):
                        selected_sites.append(site_name)
                    st.caption(site_info["description"])
        
        # 问答类网站
        if "问答" in categories:
            st.write("**💬 问答类网站：**")
            for site_name, site_info in categories["问答"]:
                default_checked = site_name in recommended_sites
                if st.checkbox(site_name, value=default_checked, key=f"site_{site_name}"):
                    selected_sites.append(site_name)
                st.caption(site_info["description"])
        
        # 技术类网站（特别标注）
        if "技术" in categories:
            st.write("**⚙️ 技术类网站（仅适用于编程/技术相关搜索）：**")
            st.warning("⚠️ 注意：技术类网站仅适用于编程、开发、技术相关的关键词搜索，对于医学、历史、文学等其他领域可能返回不相关结果。")
            cols = st.columns(3)
            for i, (site_name, site_info) in enumerate(categories["技术"]):
                with cols[i % 3]:
                    default_checked = site_name in recommended_sites
                    if st.checkbox(site_name, value=default_checked, key=f"site_{site_name}"):
                        selected_sites.append(site_name)
                    st.caption(site_info["description"])
        
        # 抓取参数
        col1, col2 = st.columns(2)
        with col1:
            max_pages_search = st.selectbox(
                "📄 总页面数限制",
                options=[10, 20, 30, 50],
                index=1,
                help="所有网站抓取的页面总数限制"
            )
        
        with col2:
            kb_name_search = st.text_input(
                "📚 知识库名称（可选）",
                placeholder="留空则自动生成",
                help="如不填写，会生成如'搜索_关键词_日期'的名称"
            )
        
        # 开始搜索按钮
        if st.button("🔍 搜索并创建知识库", type="primary", disabled=not keyword or not selected_sites):
            self._execute_keyword_search(keyword, selected_sites, max_pages_search, kb_name_search)
    
    def _execute_direct_crawl(self, url: str, max_depth: int, max_pages: int, 
                             kb_name: str, exclude_patterns: str, parser_type: str):
        """执行直接URL抓取"""
        # 处理排除模式
        exclude_list = []
        if exclude_patterns:
            exclude_list = [line.strip() for line in exclude_patterns.split('\n') if line.strip()]
        
        # 创建状态显示区域
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        def status_callback(message):
            status_container.info(message)
        
        try:
            # 执行抓取和构建
            result = self.processor.crawl_and_build_kb(
                url=url,
                max_depth=max_depth,
                max_pages=max_pages,
                kb_name=kb_name if kb_name else None,
                status_callback=status_callback
            )
            
            progress_bar.progress(100)
            
            if result["success"]:
                st.success(result["message"])
                
                # 显示详细信息
                with st.expander("📊 抓取详情"):
                    st.write(f"**知识库名称**: {result['kb_name']}")
                    st.write(f"**文件数量**: {result['files_count']}")
                    st.write("**抓取的文件**:")
                    for file_path in result["files"]:
                        st.write(f"- {file_path}")
                
                # 提示用户可以开始使用
                st.info("🎉 知识库创建完成！现在可以在主界面选择该知识库并开始对话。")
                
            else:
                st.error(f"❌ {result['message']}")
                
        except Exception as e:
            st.error(f"❌ 处理过程中出现错误: {e}")
        finally:
            status_container.empty()
            progress_bar.empty()
    
    def _execute_keyword_search(self, keyword: str, selected_sites: list, 
                               max_pages: int, kb_name: str):
        """执行关键词搜索抓取"""
        # 创建状态显示区域
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        def status_callback(message):
            status_container.info(message)
        
        try:
            # 执行搜索和构建
            result = self.processor.crawl_and_build_kb(
                keyword=keyword,
                sites=selected_sites,
                max_pages=max_pages,
                kb_name=kb_name if kb_name else None,
                status_callback=status_callback
            )
            
            progress_bar.progress(100)
            
            if result["success"]:
                st.success(result["message"])
                
                # 显示详细信息
                with st.expander("📊 搜索抓取详情"):
                    st.write(f"**搜索关键词**: {keyword}")
                    st.write(f"**搜索网站**: {', '.join(selected_sites)}")
                    st.write(f"**知识库名称**: {result['kb_name']}")
                    st.write(f"**文件数量**: {result['files_count']}")
                
                # 提示用户可以开始使用
                st.info("🎉 知识库创建完成！现在可以在主界面选择该知识库并开始对话。")
                
            else:
                st.error(f"❌ {result['message']}")
                
        except Exception as e:
            st.error(f"❌ 处理过程中出现错误: {e}")
        finally:
            status_container.empty()
            progress_bar.empty()
    
    def render_quick_access(self):
        """渲染快速访问面板（用于侧边栏）"""
        st.write("### 🌐 快速网页抓取")
        
        # 快速URL输入
        quick_url = st.text_input(
            "网址",
            placeholder="输入网址快速抓取",
            key="quick_url"
        )
        
        if st.button("快速抓取", key="quick_crawl", disabled=not quick_url):
            # 使用默认参数快速抓取
            status_container = st.empty()
            
            def status_callback(message):
                status_container.info(message)
            
            try:
                result = self.processor.crawl_and_build_kb(
                    url=quick_url,
                    max_depth=1,
                    max_pages=5,
                    status_callback=status_callback
                )
                
                if result["success"]:
                    st.success(f"✅ 已创建知识库: {result['kb_name']}")
                else:
                    st.error(f"❌ {result['message']}")
                    
            except Exception as e:
                st.error(f"❌ 错误: {e}")
            finally:
                status_container.empty()
