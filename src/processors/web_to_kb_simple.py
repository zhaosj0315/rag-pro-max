"""简化版网页抓取到知识库构建流程"""

import os
import streamlit as st
from typing import Optional, Callable, List, Dict
from datetime import datetime
from urllib.parse import urlparse
from .web_crawler import WebCrawler


def generate_kb_name_from_web(url: str, files_count: int = 0) -> str:
    """根据URL生成智能知识库名称"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # 特殊网站处理
        if 'wikipedia.org' in domain:
            path_parts = [p for p in parsed.path.split('/') if p and len(p) > 2]
            if path_parts:
                return f"百科_{path_parts[-1][:10]}"
            return "维基百科"
        elif 'baidu.com' in domain:
            return "百度百科"
        elif 'zhihu.com' in domain:
            return "知乎问答"
        elif 'csdn.net' in domain:
            return "CSDN技术"
        elif 'github.com' in domain:
            path_parts = parsed.path.split('/')
            if len(path_parts) >= 3:
                return f"项目_{path_parts[2][:10]}"
            return "GitHub项目"
        elif 'stackoverflow.com' in domain:
            return "编程问答"
        
        # 通用处理
        domain_name = domain.split('.')[0]
        if files_count > 1:
            return f"{domain_name}_{files_count}页"
        else:
            return f"{domain_name}_{datetime.now().strftime('%m%d')}"
            
    except:
        return f"网页_{datetime.now().strftime('%m%d%H%M')}"


def get_preset_search_sites() -> Dict[str, str]:
    """获取预设搜索网站"""
    return {
        "维基百科": "https://zh.wikipedia.org/wiki/Special:Search?search={keyword}",
        "百度百科": "https://baike.baidu.com/search?word={keyword}",
        "知乎": "https://www.zhihu.com/search?type=content&q={keyword}",
        "CSDN": "https://so.csdn.net/so/search?q={keyword}",
        "Stack Overflow": "https://stackoverflow.com/search?q={keyword}",
        "GitHub": "https://github.com/search?q={keyword}&type=repositories"
    }


def crawl_and_create_kb(url: str = None, 
                       keyword: str = None,
                       sites: List[str] = None,
                       max_depth: int = 1,
                       max_pages: int = 10,
                       kb_name: str = None,
                       status_callback: Optional[Callable] = None) -> Dict:
    """
    网页抓取并自动创建知识库
    
    Args:
        url: 直接抓取的URL
        keyword: 搜索关键词（当url为空时使用）
        sites: 要搜索的网站列表
        max_depth: 抓取深度
        max_pages: 最大页面数
        kb_name: 指定知识库名称
        status_callback: 状态回调函数
    
    Returns:
        dict: 处理结果
    """
    try:
        # 使用唯一的时间戳目录，确保每次抓取隔离
        timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_output_dir = os.path.join("temp_uploads", f"web_crawl_{timestamp_dir}")
        
        crawler = WebCrawler(output_dir=unique_output_dir)
        crawled_files = []
        
        if url:
            # 直接抓取URL
            if status_callback:
                status_callback(f"🌐 开始抓取网页: {url}")
            
            crawled_files = crawler.crawl_advanced(
                start_url=url,
                max_depth=max_depth,
                max_pages=max_pages,
                status_callback=status_callback
            )
            
            # 生成知识库名称
            if not kb_name:
                kb_name = generate_kb_name_from_web(url, len(crawled_files))
                
        elif keyword:
            # 关键词搜索模式
            if not sites:
                sites = ["维基百科", "百度百科"]
            
            if status_callback:
                status_callback(f"🔍 搜索关键词: {keyword}")
            
            preset_sites = get_preset_search_sites()
            
            for site_name in sites[:2]:  # 限制搜索网站数量
                if site_name in preset_sites:
                    search_url = preset_sites[site_name].format(keyword=keyword)
                    
                    if status_callback:
                        status_callback(f"🌐 搜索 {site_name}: {search_url}")
                    
                    try:
                        files = crawler.crawl_advanced(
                            start_url=search_url,
                            max_depth=1,
                            max_pages=max_pages // len(sites),
                            status_callback=status_callback
                        )
                        crawled_files.extend(files)
                    except Exception as e:
                        if status_callback:
                            status_callback(f"❌ {site_name} 搜索失败: {e}")
                        continue
            
            # 生成知识库名称
            if not kb_name:
                kb_name = f"搜索_{keyword}_{datetime.now().strftime('%m%d')}"
        
        else:
            return {"success": False, "message": "必须提供URL或关键词"}
        
        if not crawled_files:
            return {"success": False, "message": "没有成功抓取到任何内容"}
        
        # 使用统一的命名逻辑确保唯一性
        from src.utils.kb_name_optimizer import KBNameOptimizer
        from src.core.app_config import output_base
        
        # 确保名称唯一
        kb_name = KBNameOptimizer.generate_unique_name(kb_name, output_base)
        
        if status_callback:
            status_callback(f"📚 创建知识库: {kb_name}")
        
        # 检查知识库是否已存在 (KBNameOptimizer 已经处理了名称冲突，这里只需要构建路径)
        kb_path = os.path.join(output_base, kb_name)
        
        # 创建知识库目录
        os.makedirs(kb_path, exist_ok=True)
        
        if status_callback:
            status_callback(f"✅ 知识库创建完成，准备构建索引...")
        
        # 设置session state，让主应用知道有新的文件需要处理
        st.session_state.uploaded_path = os.path.abspath(crawler.output_dir)
        st.session_state.upload_auto_name = kb_name
        st.session_state.auto_create_kb = True  # 标记自动创建知识库
        st.session_state.selected_kb = kb_name  # 自动选择新知识库
        
        return {
            "success": True,
            "kb_name": kb_name,
            "files_count": len(crawled_files),
            "files": crawled_files,
            "crawler_output_dir": crawler.output_dir,
            "message": f"✅ 网页抓取完成，已准备创建知识库 '{kb_name}'"
        }
        
    except Exception as e:
        return {"success": False, "message": f"处理失败: {e}"}


def render_enhanced_web_crawl():
    """渲染增强版网页抓取界面（替换原有的网页抓取标签页）"""
    
    # 创建子标签页
    web_tab1, web_tab2 = st.tabs(["🔗 直接抓取", "🔍 关键词搜索"])
    
    with web_tab1:
        st.write("**直接网址抓取并创建知识库**")
        
        # URL输入
        crawl_url = st.text_input(
            "🔗 网址", 
            placeholder="例如: python.org 或 https://docs.python.org",
            help="支持自动添加https://前缀"
        )
        
        # 参数设置
        col1, col2, col3 = st.columns(3)
        with col1:
            crawl_depth = st.selectbox("🔍 深度", [1, 2, 3, 4, 5], index=0, help="抓取层级")
        with col2:
            max_pages = st.selectbox("📄 页数", [5, 10, 20, 50], index=1, help="最大页面数")
        with col3:
            kb_name = st.text_input("📚 知识库名", placeholder="留空自动生成", help="可选")
        
        # 高级选项
        with st.expander("⚙️ 高级选项"):
            parser_type = st.selectbox("解析模式", ["default", "article", "documentation"])
            exclude_text = st.text_area("排除链接模式", placeholder="*/admin/*\n*.pdf", height=60)
        
        # 抓取按钮
        if st.button("🚀 抓取并创建知识库", type="primary", disabled=not crawl_url):
            exclude_patterns = [line.strip() for line in exclude_text.split('\n') if line.strip()] if exclude_text else []
            
            status_container = st.empty()
            progress_bar = st.progress(0)
            
            def status_callback(message):
                status_container.info(message)
                if "已保存" in message:
                    progress_bar.progress(min(progress_bar._value + 0.1, 0.9))
            
            try:
                result = crawl_and_create_kb(
                    url=crawl_url,
                    max_depth=crawl_depth,
                    max_pages=max_pages,
                    kb_name=kb_name if kb_name else None,
                    status_callback=status_callback
                )
                
                progress_bar.progress(1.0)
                
                if result["success"]:
                    st.success(result["message"])
                    st.info("🎉 现在可以在左侧选择该知识库并开始对话！")
                    
                    # 显示详情
                    with st.expander("📊 抓取详情"):
                        st.write(f"**知识库名称**: {result['kb_name']}")
                        st.write(f"**抓取页面数**: {result['files_count']}")
                        st.write(f"**文件位置**: {result['crawler_output_dir']}")
                    
                    # 触发重新运行以更新界面
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result["message"])
                    
            except Exception as e:
                st.error(f"❌ 处理失败: {e}")
            finally:
                status_container.empty()
                progress_bar.empty()
    
    with web_tab2:
        st.write("**关键词搜索并创建知识库**")
        
        # 关键词输入
        keyword = st.text_input(
            "🔍 搜索关键词",
            placeholder="例如: 人工智能、Python编程、机器学习",
            help="输入要搜索的关键词"
        )
        
        # 网站选择
        st.write("选择搜索网站:")
        preset_sites = get_preset_search_sites()
        
        selected_sites = []
        cols = st.columns(3)
        for i, site_name in enumerate(preset_sites.keys()):
            with cols[i % 3]:
                default_checked = site_name in ["维基百科", "百度百科"]
                if st.checkbox(site_name, value=default_checked, key=f"search_site_{site_name}"):
                    selected_sites.append(site_name)
        
        # 参数设置
        col1, col2 = st.columns(2)
        with col1:
            search_pages = st.selectbox("总页面数", [10, 20, 30, 50], index=1)
        with col2:
            search_kb_name = st.text_input("知识库名", placeholder="留空自动生成")
        
        # 搜索按钮
        if st.button("🔍 搜索并创建知识库", type="primary", disabled=not keyword or not selected_sites):
            status_container = st.empty()
            progress_bar = st.progress(0)
            
            def status_callback(message):
                status_container.info(message)
                if "搜索" in message or "抓取" in message:
                    progress_bar.progress(min(progress_bar._value + 0.2, 0.9))
            
            try:
                result = crawl_and_create_kb(
                    keyword=keyword,
                    sites=selected_sites,
                    max_pages=search_pages,
                    kb_name=search_kb_name if search_kb_name else None,
                    status_callback=status_callback
                )
                
                progress_bar.progress(1.0)
                
                if result["success"]:
                    st.success(result["message"])
                    st.info("🎉 现在可以在左侧选择该知识库并开始对话！")
                    
                    # 显示详情
                    with st.expander("📊 搜索详情"):
                        st.write(f"**搜索关键词**: {keyword}")
                        st.write(f"**搜索网站**: {', '.join(selected_sites)}")
                        st.write(f"**知识库名称**: {result['kb_name']}")
                        st.write(f"**抓取页面数**: {result['files_count']}")
                    
                    # 触发重新运行以更新界面
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result["message"])
                    
            except Exception as e:
                st.error(f"❌ 处理失败: {e}")
            finally:
                status_container.empty()
                progress_bar.empty()
