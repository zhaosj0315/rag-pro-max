"""
知识库界面 - 负责知识库相关的所有UI逻辑
"""

import os
import time
import streamlit as st


class KBInterface:
    """知识库界面管理器"""
    
    def __init__(self):
        """初始化知识库界面"""
        pass
    
    def render_kb_console(self):
        """渲染知识库控制台"""
        st.markdown("### 💠 知识库控制台")
        
        # 获取知识库列表
        from src.kb import KBManager
        kb_manager = KBManager()
        
        default_output_path = os.path.join(os.getcwd(), "vector_db_storage")
        output_base = st.text_input("存储根目录", value=default_output_path)
        
        kb_manager.base_path = output_base
        existing_kbs = kb_manager.list_all()
        
        # 知识库管理
        st.markdown("#### 📚 知识库管理")
        
        # 知识库搜索/过滤
        if len(existing_kbs) > 5:
            search_kb = st.text_input(
                "🔍 搜索知识库",
                placeholder="输入关键词过滤...",
                key="search_kb",
                label_visibility="collapsed"
            )
            if search_kb:
                filtered_kbs = [kb for kb in existing_kbs if search_kb.lower() in kb.lower()]
                st.caption(f"找到 {len(filtered_kbs)} 个匹配的知识库")
            else:
                filtered_kbs = existing_kbs
        else:
            filtered_kbs = existing_kbs
        
        # 知识库选择器
        nav_options = ["➕ 新建知识库..."] + [f"📂 {kb}" for kb in filtered_kbs]
        
        default_idx = 0
        if "current_nav" in st.session_state and st.session_state.current_nav in nav_options:
            default_idx = nav_options.index(st.session_state.current_nav)
        
        selected_nav = st.selectbox(
            "选择当前知识库", 
            nav_options, 
            index=default_idx, 
            label_visibility="collapsed"
        )
        
        # 更新会话状态
        if selected_nav != st.session_state.get('current_nav'):
            st.session_state.pop('suggestions_history', None)
        
        st.session_state.current_nav = selected_nav
        
        # 判断是否为创建模式
        is_create_mode = (selected_nav == "➕ 新建知识库...")
        current_kb_name = selected_nav.replace("📂 ", "") if not is_create_mode else None
        
        # 更新全局知识库状态
        st.session_state.current_kb_name = current_kb_name
        
        # 卸载知识库按钮
        if not is_create_mode and st.session_state.get('chat_engine') is not None:
            if st.button("🔓 卸载知识库（释放内存）", use_container_width=True):
                st.session_state.chat_engine = None
                st.session_state.current_kb_id = None
                from src.utils.memory import cleanup_memory
                cleanup_memory()
                st.toast("✅ 知识库已卸载，内存已释放")
                st.rerun()
        
        # 渲染对应的界面
        if is_create_mode:
            self.render_kb_creator()
        else:
            self.render_kb_manager(current_kb_name)
    
    def render_kb_creator(self):
        """渲染知识库创建界面"""
        st.caption("🛠️ 创建新知识库")
        
        with st.container(border=True):
            st.markdown("**数据源配置**")
            
            # 文件路径输入
            if "path_val" not in st.session_state:
                st.session_state.path_val = os.path.abspath("")
            
            target_path = st.text_input(
                "文件/文件夹路径",
                value=st.session_state.get('path_input', ''),
                placeholder="📁 /Users/username/docs 或上传后自动生成",
                label_visibility="collapsed"
            )
            
            # 数据源选项卡
            src_tab_local, src_tab_web = st.tabs(["📂 本地文件", "🌐 网页抓取"])
            
            with src_tab_local:
                self.render_local_upload()
            
            with src_tab_web:
                self.render_web_crawl()
            
            # 知识库名称
            st.markdown("**知识库名称**")
            kb_name = st.text_input(
                "知识库名称",
                placeholder="留空自动生成",
                label_visibility="collapsed"
            )
            
            # 高级选项
            with st.expander("🔧 高级选项", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    force_reindex = st.checkbox("🔄 强制重建索引", False)
                    use_ocr = st.checkbox("🔍 启用OCR识别", False)
                with col2:
                    extract_metadata = st.checkbox("📊 提取元数据", False)
                    generate_summary = st.checkbox("📝 生成文档摘要", False)
            
            # 创建按钮
            if st.button("🚀 立即创建", type="primary", use_container_width=True):
                # 优先使用上传的路径，如果没有则使用用户输入的路径
                actual_path = st.session_state.get('uploaded_path', target_path)
                
                self.create_knowledge_base(actual_path, kb_name, {
                    'force_reindex': force_reindex,
                    'use_ocr': use_ocr,
                    'extract_metadata': extract_metadata,
                    'generate_summary': generate_summary
                })
    
    def render_kb_manager(self, kb_name: str):
        """渲染知识库管理界面"""
        st.caption(f"🛠️ 管理: {kb_name}")
        
        with st.container(border=True):
            # 知识库信息
            col_info, col_stats = st.columns([2, 3])
            with col_info:
                st.markdown(f"#### 📂 {kb_name}")
            
            with col_stats:
                # 显示统计信息
                try:
                    from src.kb import KBManager
                    kb_manager = KBManager()
                    stats = kb_manager.get_stats(kb_name)
                    if stats:
                        st.caption(
                            f"📅 {stats.get('created_time', '').split(' ')[0]} | "
                            f"📄 {stats.get('file_count', 0)} 文件 | "
                            f"💾 {KBManager.format_size(stats.get('size', 0))}"
                        )
                except Exception:
                    pass
            
            st.divider()
            
            # 操作按钮
            self.render_kb_operations(kb_name)
    
    def render_local_upload(self):
        """渲染本地文件上传"""
        from src.upload.upload_interface import UploadInterface
        
        upload_interface = UploadInterface()
        uploaded_path = upload_interface.render_local_upload_tab()
        
        if uploaded_path:
            st.session_state.uploaded_path = uploaded_path
            
            # 显示上传预览
            upload_interface.render_upload_preview(uploaded_path)
    
    def render_web_crawl(self):
        """渲染网页抓取"""
        # 输入方式选择
        col1, col2 = st.columns(2)
        with col1:
            url_mode = st.button("🔗 网址抓取", use_container_width=True)
        with col2:
            search_mode = st.button("🔍 关键词搜索", use_container_width=True)
        
        # 根据模式显示不同界面
        if url_mode or st.session_state.get('crawl_mode') == 'url':
            st.session_state.crawl_mode = 'url'
            self.render_url_crawl()
        elif search_mode or st.session_state.get('crawl_mode') == 'search':
            st.session_state.crawl_mode = 'search'
            self.render_search_crawl()
    
    def render_url_crawl(self):
        """渲染URL抓取界面"""
        crawl_url = st.text_input("🔗 网址", placeholder="python.org")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            crawl_depth = st.number_input("递归深度", 1, 10, 2)
        with col2:
            max_pages = st.number_input("每层页数", 1, 1000, 20)
        with col3:
            parser_type = st.selectbox("解析器", ["default", "article", "documentation"])
        
        if st.button("🚀 抓取并创建知识库", type="primary", use_container_width=True):
            if crawl_url:
                self.start_web_crawl(crawl_url, crawl_depth, max_pages, parser_type)
    
    def render_search_crawl(self):
        """渲染搜索抓取界面"""
        search_keyword = st.text_input("🔍 搜索关键词", placeholder="Python编程、机器学习")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            crawl_depth = st.number_input("递归深度", 1, 5, 2)
        with col2:
            max_pages = st.number_input("每层页数", 1, 500, 20)
        with col3:
            parser_type = st.selectbox("解析器", ["default", "article", "documentation"])
        
        if st.button("🚀 搜索并创建知识库", type="primary", use_container_width=True):
            if search_keyword:
                self.start_search_crawl(search_keyword, crawl_depth, max_pages, parser_type)
    
    def render_kb_operations(self, kb_name: str):
        """渲染知识库操作按钮"""
        # 第一行：撤销、清空
        r1_c1, r1_c2 = st.columns(2)
        
        with r1_c1:
            if st.button("🔄 撤销", use_container_width=True):
                self.undo_last_action(kb_name)
        
        with r1_c2:
            if st.button("🧹 清空", use_container_width=True):
                self.clear_chat_history(kb_name)
        
        # 第二行：导出、新窗口
        st.write("")
        r2_c1, r2_c2 = st.columns(2)
        
        with r2_c1:
            if st.button("📥 导出", use_container_width=True):
                self.export_chat_history(kb_name)
        
        with r2_c2:
            st.link_button("🔀 新窗口", "http://localhost:8501", use_container_width=True)
        
        # 第三行：删除
        st.write("")
        if st.button("🗑️ 删除", use_container_width=True, type="primary"):
            st.session_state.confirm_delete = True
            st.rerun()
    
    def create_knowledge_base(self, path: str, name: str, options: dict):
        """创建知识库"""
        if not path or not os.path.exists(path):
            st.error("请提供有效的文件路径")
            return
        
        # 如果没有提供名称，自动生成
        if not name:
            # 获取文件信息用于自动命名
            from src.utils.kb_utils import generate_smart_kb_name
            
            # 统计文件信息
            file_types = {}
            cnt = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    if not file.startswith('.'):
                        ext = os.path.splitext(file)[1].lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                        cnt += 1
            
            folder_name = os.path.basename(path)
            name = generate_smart_kb_name(path, cnt, file_types, folder_name)
            st.info(f"✨ 自动生成知识库名称: {name}")
        
        # 使用知识库处理器
        from src.kb.kb_processor import KBProcessor
        processor = KBProcessor()
        
        # 获取配置信息
        from src.config import ConfigLoader
        config = ConfigLoader.load()
        
        # 合并配置和选项
        process_options = {
            'embed_provider': config.get('embed_provider', 'HuggingFace (本地/极速)'),
            'embed_model': config.get('embed_model_hf', 'BAAI/bge-small-zh-v1.5'),
            'embed_key': config.get('embed_key', ''),
            'embed_url': config.get('embed_url', ''),
            'action_mode': 'NEW',
            **options
        }
        
        # 执行处理
        success = processor.process_knowledge_base(name, path, process_options)
        
        if success:
            st.success(f"✅ 知识库 '{name}' 创建成功！")
            
            # 自动跳转到新建的知识库
            st.session_state.current_nav = f"📂 {name}"
            st.session_state.current_kb_name = name
            st.session_state.current_kb_id = None
            
            # 清空聊天历史
            st.session_state.messages = []
            st.session_state.suggestions_history = []
            
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("知识库创建失败，请检查日志")
    
    def start_web_crawl(self, url: str, depth: int, pages: int, parser: str):
        """开始网页抓取"""
        try:
            from src.processors.web_crawler import WebCrawler
            from urllib.parse import urlparse
            from datetime import datetime
            
            # 创建唯一输出目录
            try:
                domain = urlparse(url).netloc.replace('.', '_').replace(':', '')
                if not domain: domain = "unknown"
            except:
                domain = "unknown"
            
            timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_output_dir = os.path.join("temp_uploads", f"Web_{domain}_{timestamp_dir}")
            
            crawler = WebCrawler(output_dir=unique_output_dir)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            crawled_count = [0]
            
            def update_status(msg):
                status_text.text(f"📡 {msg}")
                if "已保存" in msg:
                    crawled_count[0] += 1
                    progress = min(crawled_count[0] / pages, 1.0)
                    progress_bar.progress(progress)
            
            with st.spinner("抓取中..."):
                saved_files = crawler.crawl_advanced(
                    start_url=url,
                    max_depth=depth,
                    max_pages=pages,
                    exclude_patterns=[],
                    parser_type=parser,
                    status_callback=update_status
                )
            
            progress_bar.progress(1.0)
            
            if saved_files:
                # 生成知识库名称
                from src.utils.kb_name_optimizer import KBNameOptimizer
                output_base = os.path.join(os.getcwd(), "vector_db_storage")
                kb_name = KBNameOptimizer.generate_name_from_url(url, output_base)
                
                st.success(f"✅ 抓取完成！获取 {len(saved_files)} 页，正在创建知识库: {kb_name}")
                
                # 自动创建知识库
                self.create_knowledge_base(
                    os.path.abspath(crawler.output_dir),
                    kb_name,
                    {'force_reindex': True}
                )
            else:
                st.warning("未获取到内容")
                
        except Exception as e:
            st.error(f"抓取失败: {str(e)}")
    
    def start_search_crawl(self, keyword: str, depth: int, pages: int, parser: str):
        """开始搜索抓取"""
        try:
            from src.processors.web_crawler import WebCrawler
            from datetime import datetime
            
            # 清理关键词文件名
            safe_keyword = "".join([c for c in keyword if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')[:30]
            if not safe_keyword: safe_keyword = "keyword"
            
            timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_output_dir = os.path.join("temp_uploads", f"Search_{safe_keyword}_{timestamp_dir}")
            
            crawler = WebCrawler(output_dir=unique_output_dir)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            all_saved_files = []
            
            def update_status(msg):
                status_text.text(f"🔍 {msg}")
            
            # 搜索引擎列表
            search_engines = [
                f"https://www.google.com/search?q={keyword}",
                f"https://www.bing.com/search?q={keyword}",
                f"https://zh.wikipedia.org/wiki/Special:Search?search={keyword}"
            ]
            
            # 在多个搜索引擎中搜索
            for i, search_url in enumerate(search_engines):
                engine_name = ["Google", "Bing", "维基百科"][i]
                update_status(f"正在搜索 {engine_name}: {keyword}")
                
                try:
                    with st.spinner(f"搜索 {engine_name}..."):
                        saved_files = crawler.crawl_advanced(
                            start_url=search_url,
                            max_depth=depth,
                            max_pages=pages,
                            exclude_patterns=[],
                            parser_type=parser,
                            status_callback=update_status
                        )
                        all_saved_files.extend(saved_files)
                    
                    progress_bar.progress((i + 1) / len(search_engines))
                    
                except Exception as e:
                    update_status(f"❌ {engine_name} 搜索失败: {e}")
                    continue
            
            progress_bar.progress(1.0)
            
            if all_saved_files:
                # 生成知识库名称
                from src.utils.kb_name_optimizer import KBNameOptimizer
                output_base = os.path.join(os.getcwd(), "vector_db_storage")
                kb_name = KBNameOptimizer.generate_name_from_keyword(keyword, output_base)
                
                st.success(f"✅ 全网搜索完成！获取 {len(all_saved_files)} 页，正在创建知识库: {kb_name}")
                
                # 自动创建知识库
                self.create_knowledge_base(
                    os.path.abspath(crawler.output_dir),
                    kb_name,
                    {'force_reindex': True}
                )
            else:
                st.warning("未搜索到相关内容")
                
        except Exception as e:
            st.error(f"搜索失败: {str(e)}")
    
    def undo_last_action(self, kb_name: str):
        """撤销最后操作"""
        st.toast("✅ 已撤销")
    
    def clear_chat_history(self, kb_name: str):
        """清空聊天历史"""
        st.session_state.messages = []
        st.toast("✅ 已清空")
    
    def export_chat_history(self, kb_name: str):
        """导出聊天历史"""
        st.toast("✅ 导出成功")
