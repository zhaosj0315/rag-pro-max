from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
异步并发网页爬虫 - 针对文档全量饱和抓取深度优化
完全复刻用户原生成功脚本的逻辑架构
"""

import asyncio
import aiohttp
import aiofiles
import json
import time
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Callable
from pathlib import Path
import os

from src.utils.file_system_utils import set_where_from_metadata
from src.utils.html_to_markdown import HtmlToMarkdown

class AsyncWebCrawler:
    def __init__(self, max_concurrent=1, delay_range=(1.0, 1.5), ignore_robots=True):
        self.max_concurrent = max_concurrent
        self.delay_range = delay_range
        self.ignore_robots = ignore_robots
        self.session = None
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.state_file = os.path.join("temp_uploads", f"crawler_state_{int(time.time())}.json")
        self.semaphore = None
        
    async def __aenter__(self):
        """异步上下文管理器 - 使用与原生脚本完全一致的 Headers"""
        connector = aiohttp.TCPConnector(limit=1, keepalive_timeout=30)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """模仿原生脚本的 fetch 行为"""
        try:
            # 严格延迟
            await asyncio.sleep(__import__('random').uniform(*self.delay_range))
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except:
            pass
        return None

    def extract_links_pure(self, html: str, base_url: str, scope_prefix: str) -> List[str]:
        """【完全复刻原生脚本逻辑】"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # urljoin + 移除锚点和参数
            full_url = urljoin(base_url, href).split('#')[0].split('?')[0]
            # 简单 startswith 判定
            if full_url.startswith(scope_prefix):
                if full_url not in self.visited_urls:
                    links.append(full_url)
        return list(set(links))

    def _get_filename_pure(self, url: str) -> str:
        """【完全复刻原生脚本命名逻辑】"""
        path = urlparse(url).path
        if path.startswith('/'):
            path = path[1:]
        filename = path.replace('/', '_')
        if not filename:
            filename = "index"
        return f"{filename}.md"

    async def crawl_recursive(
        self, start_url: str, max_depth: int = 10, max_pages_per_level: int = 1000,
        output_dir: str = "crawled_data", status_callback: Optional[Callable] = None
    ) -> List[str]:
        """【重构】分层递归爬取模式 - 优化种子页逻辑，支持 5+25 指数分布"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 确定作用域前缀
        parsed = urlparse(start_url)
        if 'help.aliyun.com' in parsed.netloc:
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 3:
                scope_prefix = f"{parsed.scheme}://{parsed.netloc}/{'/'.join(path_parts[:3])}/"
            else:
                scope_prefix = start_url.rsplit('/', 1)[0] + '/'
        else:
            scope_prefix = start_url.rsplit('/', 1)[0] + '/'

        if status_callback:
            status_callback(f"🌐 激活【指数级深度抓取】模式")
            status_callback(f"📍 作用域: {scope_prefix}")
            status_callback(f"🐢 参数设定: 深度={max_depth}, 基础页数={max_pages_per_level}")

        saved_files = []
        total_pages_limit = 50000

        # --- Step 0: 处理种子页 (Level 0) ---
        if status_callback:
            status_callback(f"🚀 处理种子页: {start_url}")
            
        html = await self.fetch_page(start_url)
        if html:
            self.visited_urls.add(start_url)
            content = HtmlToMarkdown.convert_with_html2text(html)
            if len(content.strip()) >= 100:
                filename = self._get_filename_pure(start_url)
                filepath = output_path / filename
                try:
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string.strip() if soup.title else "No Title"
                except: title = "No Title"
                
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    await f.write(f"**URL:** {start_url}\n\n# {title}\n\n{content}")
                set_where_from_metadata(str(filepath), start_url)
                saved_files.append(str(filepath))
            
            # 提取初始链接作为 Level 1 起点
            current_level = set(self.extract_links_pure(html, start_url, scope_prefix))
        else:
            if status_callback: status_callback(f"❌ 种子页获取失败")
            return []

        # --- Step 1: 层级递归 ---
        for depth in range(1, max_depth + 1):
            if not current_level or len(saved_files) >= total_pages_limit:
                break
                
            # 限制本层处理数量 - 指数级
            target_layer_count = max_pages_per_level ** depth
            urls_to_process = list(current_level)[:target_layer_count]
            next_level = set()
            
            if status_callback:
                status_callback(f"📂 第 {depth} 层开始: 目标抓取 {target_layer_count} 页")
            
            for current_url in urls_to_process:
                if current_url in self.visited_urls or len(saved_files) >= total_pages_limit:
                    continue
                    
                self.visited_urls.add(current_url)
                
                if status_callback:
                    status_callback(f"🔄 抓取 (L{depth}, 总:{len(saved_files)+1}): {current_url}")
                
                html = await self.fetch_page(current_url)
                if not html: continue
                
                content = HtmlToMarkdown.convert_with_html2text(html)
                if len(content.strip()) < 100: continue
                
                filename = self._get_filename_pure(current_url)
                filepath = output_path / filename
                
                try:
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string.strip() if soup.title else "No Title"
                except: title = "No Title"
                
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    await f.write(f"**URL:** {current_url}\n\n# {title}\n\n{content}")
                
                set_where_from_metadata(str(filepath), current_url)
                saved_files.append(str(filepath))
                
                if depth < max_depth:
                    found_links = self.extract_links_pure(html, current_url, scope_prefix)
                    next_level.update(set(found_links) - self.visited_urls)
            
            current_level = next_level

        if status_callback:
            status_callback(f"🎉 爬取完成！共捕获 {len(saved_files)} 个页面")
        
        return saved_files

    