"""网页抓取到知识库构建的完整流程处理器"""

import os
import json
import requests
from typing import List, Dict, Optional, Callable
from datetime import datetime
from .web_crawler import WebCrawler
from ..kb.kb_manager import KBManager
from ..processors.index_builder import IndexBuilder
import streamlit as st


class WebToKBProcessor:
    """网页抓取到知识库构建的完整流程处理器"""
    
    def __init__(self):
        # self.crawler 将在每次任务执行时独立初始化
        self.kb_manager = KBManager()
        self.index_builder = IndexBuilder()
        
        # 预设知名网站 - 按类别分组
        self.preset_sites = {
            # 百科类网站
            "维基百科": {
                "base_url": "https://zh.wikipedia.org/wiki/",
                "search_url": "https://zh.wikipedia.org/wiki/Special:Search?search={keyword}",
                "description": "中文维基百科 - 全球最大的中文百科全书",
                "category": "百科"
            },
            "百度百科": {
                "base_url": "https://baike.baidu.com/item/",
                "search_url": "https://baike.baidu.com/search?word={keyword}",
                "description": "百度百科 - 中文百科知识平台",
                "category": "百科"
            },
            
            # 医学专业网站
            "丁香园": {
                "base_url": "https://www.dxy.com/",
                "search_url": "https://www.dxy.com/search?q={keyword}",
                "description": "丁香园 - 专业医学知识平台",
                "category": "医学"
            },
            "好大夫在线": {
                "base_url": "https://www.haodf.com/",
                "search_url": "https://www.haodf.com/search?kw={keyword}",
                "description": "好大夫在线 - 医疗健康咨询平台",
                "category": "医学"
            },
            "春雨医生": {
                "base_url": "https://www.chunyuyisheng.com/",
                "search_url": "https://www.chunyuyisheng.com/search?q={keyword}",
                "description": "春雨医生 - 在线医疗健康服务",
                "category": "医学"
            },
            
            # 问答类网站
            "知乎": {
                "base_url": "https://www.zhihu.com/",
                "search_url": "https://www.zhihu.com/search?type=content&q={keyword}",
                "description": "知乎 - 中文问答社区",
                "category": "问答"
            },
            
            # 技术类网站
            "CSDN": {
                "base_url": "https://blog.csdn.net/",
                "search_url": "https://so.csdn.net/so/search?q={keyword}",
                "description": "CSDN - 技术博客平台 ⚠️ 仅适用于技术类搜索",
                "category": "技术"
            },
            "GitHub": {
                "base_url": "https://github.com/",
                "search_url": "https://github.com/search?q={keyword}&type=repositories",
                "description": "GitHub - 代码托管平台 ⚠️ 仅适用于技术类搜索",
                "category": "技术"
            },
            "Stack Overflow": {
                "base_url": "https://stackoverflow.com/",
                "search_url": "https://stackoverflow.com/search?q={keyword}",
                "description": "Stack Overflow - 程序员问答社区 ⚠️ 仅适用于技术类搜索",
                "category": "技术"
            }
        }
    
    def generate_kb_name_from_url(self, url: str, content_preview: str = "") -> str:
        """根据URL和内容预览生成智能知识库名称"""
        from urllib.parse import urlparse
        import re
        
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # 从URL路径提取关键词
        path_parts = [p for p in parsed.path.split('/') if p and len(p) > 2]
        
        # 从内容预览提取关键词
        content_keywords = []
        if content_preview:
            # 简单的关键词提取
            words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content_preview[:500])
            content_keywords = [w for w in words if len(w) >= 2][:5]
        
        # 生成名称策略
        if domain in ['zh.wikipedia.org', 'baike.baidu.com']:
            if path_parts:
                return f"百科_{path_parts[-1][:10]}"
        elif domain in ['zhihu.com']:
            return f"知乎_{path_parts[-1][:10]}" if path_parts else "知乎问答"
        elif domain in ['csdn.net', 'blog.csdn.net']:
            return f"技术_{path_parts[-1][:10]}" if path_parts else "CSDN技术"
        elif domain in ['github.com']:
            if len(path_parts) >= 2:
                return f"项目_{path_parts[1][:10]}"
        elif domain in ['stackoverflow.com']:
            return "编程问答"
        
        # 通用策略
        if content_keywords:
            return f"网页_{content_keywords[0][:8]}"
        elif path_parts:
            return f"网页_{path_parts[-1][:8]}"
        else:
            domain_name = domain.split('.')[0]
            return f"{domain_name}_{datetime.now().strftime('%m%d')}"
    
    def search_preset_sites(self, keyword: str, sites: List[str] = None) -> List[Dict]:
        """在预设网站中搜索关键词，返回搜索结果URL"""
        if sites is None:
            sites = list(self.preset_sites.keys())
        
        results = []
        for site_name in sites:
            if site_name in self.preset_sites:
                site_info = self.preset_sites[site_name]
                search_url = site_info["search_url"].format(keyword=keyword)
                results.append({
                    "site": site_name,
                    "url": search_url,
                    "description": site_info["description"]
                })
        
        return results
    
    def crawl_and_build_kb(self, 
                          url: str = None,
                          keyword: str = None,
                          sites: List[str] = None,
                          max_depth: int = 1,
                          max_pages: int = 10,
                          kb_name: str = None,
                          auto_switch: bool = True,
                          status_callback: Optional[Callable] = None) -> Dict:
        """
        完整的网页抓取到知识库构建流程
        
        Args:
            url: 直接抓取的URL（优先级高）
            keyword: 搜索关键词（当url为空时使用）
            sites: 要搜索的网站列表（当使用keyword时）
            max_depth: 抓取深度
            max_pages: 最大页面数
            kb_name: 指定知识库名称（可选）
            auto_switch: 是否自动切换到新知识库
            status_callback: 状态回调函数
        
        Returns:
            dict: 处理结果
        """
        try:
            # 每次执行使用独立的抓取器和输出目录，防止内容混淆
            timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_output_dir = os.path.join("temp_uploads", f"web_crawl_proc_{timestamp_dir}")
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
                    # 读取第一个文件的内容作为预览
                    content_preview = ""
                    if crawled_files:
                        try:
                            with open(crawled_files[0], 'r', encoding='utf-8') as f:
                                content_preview = f.read()[:1000]
                        except:
                            pass
                    kb_name = self.generate_kb_name_from_url(url, content_preview)
            
            elif keyword:
                # 关键词搜索模式
                if not sites:
                    sites = ["维基百科", "百度百科"]  # 默认搜索网站
                
                if status_callback:
                    status_callback(f"🔍 搜索关键词: {keyword}")
                
                search_results = self.search_preset_sites(keyword, sites)
                
                # 抓取搜索结果
                for result in search_results[:2]:  # 限制搜索结果数量
                    if status_callback:
                        status_callback(f"🌐 抓取 {result['site']}: {result['url']}")
                    
                    try:
                        files = crawler.crawl_advanced(
                            start_url=result['url'],
                            max_depth=2,  # 搜索结果需要抓取2层
                            max_pages=max_pages // len(search_results),
                            status_callback=status_callback
                        )
                        crawled_files.extend(files)
                    except Exception as e:
                        if status_callback:
                            status_callback(f"❌ {result['site']} 抓取失败: {e}")
                        continue
                
                # 生成知识库名称
                if not kb_name:
                    kb_name = f"搜索_{keyword}_{datetime.now().strftime('%m%d')}"
            
            else:
                return {"success": False, "message": "必须提供URL或关键词"}
            
            if not crawled_files:
                return {"success": False, "message": "没有成功抓取到任何内容"}
            
            if status_callback:
                status_callback(f"📚 创建知识库: {kb_name}")
            
            # 创建知识库
            success, message = self.kb_manager.create(kb_name)
            if not success:
                # 如果知识库已存在，生成新名称
                kb_name = f"{kb_name}_{datetime.now().strftime('%H%M')}"
                success, message = self.kb_manager.create(kb_name)
                if not success:
                    return {"success": False, "message": f"创建知识库失败: {message}"}
            
            if status_callback:
                status_callback(f"🔨 构建知识库索引...")
            
            # 构建知识库索引
            try:
                if status_callback:
                    status_callback("🔨 正在构建索引...")
                
                # 获取知识库路径
                kb_info = self.kb_manager.get_info(kb_name)
                if not kb_info:
                    return {"success": False, "message": f"无法获取知识库信息: {kb_name}"}
                
                kb_path = kb_info['path']
                
                # 获取当前嵌入模型
                from llama_index.core import Settings
                
                # 初始化索引构建器
                # 注意：这里重新初始化是为了确保使用正确的参数
                self.index_builder = IndexBuilder(
                    kb_name=kb_name,
                    persist_dir=kb_path,
                    embed_model=Settings.embed_model
                )
                
                # 执行构建
                build_result = self.index_builder.build(
                    source_path=unique_output_dir,
                    action_mode="NEW",
                    status_callback=lambda _, msg, *args: status_callback(f"🔨 {msg}" if isinstance(msg, str) else "处理中...")
                )
                
                if build_result.success:
                    # 如果在Streamlit环境中，自动切换知识库
                    if auto_switch and 'st' in globals():
                        st.session_state.selected_kb = kb_name
                        if status_callback:
                            status_callback(f"✅ 已自动切换到知识库: {kb_name}")
                    
                    return {
                        "success": True,
                        "kb_name": kb_name,
                        "files_count": build_result.file_count,
                        "doc_count": build_result.doc_count,
                        "files": crawled_files,
                        "message": f"✅ 成功创建知识库 '{kb_name}'，包含 {build_result.file_count} 个文件 ({build_result.doc_count} 个片段)"
                    }
                else:
                    return {"success": False, "message": f"索引构建失败: {build_result.error}"}
                
            except Exception as e:
                return {"success": False, "message": f"构建索引失败: {e}"}
                
        except Exception as e:
            return {"success": False, "message": f"处理失败: {e}"}
    
    def get_preset_sites(self) -> Dict:
        """获取预设网站列表"""
        return self.preset_sites
    
    def recommend_sites_for_keyword(self, keyword: str) -> List[str]:
        """根据关键词智能推荐合适的网站"""
        from src.services.configurable_industry_service import get_configurable_industry_service
        
        # 使用新的可配置推荐系统
        service = get_configurable_industry_service()
        return service.recommend_sites_for_keyword(keyword)
    
    def generate_suggestions_for_crawl(self, kb_name: str, crawl_url: str, saved_files: List[str]) -> List[str]:
        """为网页抓取生成推荐问题"""
        from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
        
        # 读取抓取内容作为上下文
        context = ""
        for file_path in saved_files[:3]:  # 只读取前3个文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    context += content[:1000] + "\n"  # 每个文件取前1000字符
            except:
                continue
        
        # 使用统一推荐引擎
        engine = get_unified_suggestion_engine(kb_name)
        return engine.generate_suggestions(
            context=context,
            source_type='web_crawl',
            metadata={'url': crawl_url, 'files': saved_files},
            num_questions=4
        )
    
    def add_preset_site(self, name: str, base_url: str, search_url: str, description: str):
        """添加预设网站"""
        self.preset_sites[name] = {
            "base_url": base_url,
            "search_url": search_url,
            "description": description
        }
