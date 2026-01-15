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
        """【重构】饱和式队列爬取模式 - 取代层级递归"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 确定作用域前缀 (复刻原生脚本)
        parsed = urlparse(start_url)
        # 针对阿里云专项提取根路径
        path_parts = parsed.path.strip('/').split('/')
        if 'help.aliyun.com' in parsed.netloc and len(path_parts) >= 3:
            scope_prefix = f"{parsed.scheme}://{parsed.netloc}/{'/'.join(path_parts[:3])}/"
        else:
            # 通用回退
            scope_prefix = start_url.rsplit('/', 1)[0] + '/'

        if status_callback:
            status_callback(f"🌐 激活【饱和抓取】模式 (对齐原生脚本)")
            status_callback(f"📍 作用域: {scope_prefix}")
            status_callback(f"🐢 正在以单线程顺序爬取，请耐心等待...")

        urls_to_visit = {start_url}
        saved_files = []
        
        # 只要队列不空，就一直爬下去 (复刻 while 循环)
        while urls_to_visit and len(saved_files) < 2000:
            current_url = urls_to_visit.pop()
            
            if current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(current_url)
            
            if status_callback:
                status_callback(f"正在处理 ({len(saved_files)+1}): {current_url}")
            
            html = await self.fetch_page(current_url)
            if not html:
                continue
            
            # 提取内容 (使用高保真 HTML2Text，锁定 content-wrapper)
            content = HtmlToMarkdown.convert_with_html2text(html)
            if len(content.strip()) < 100:
                continue
            
            # 保存文件 (复刻命名逻辑)
            filename = self._get_filename_pure(current_url)
            filepath = output_path / filename
            
            # 标题提取
            try:
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.title.string.strip() if soup.title else "No Title"
            except: title = "No Title"
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(f"**URL:** {current_url}\n\n# {title}\n\n{content}")
            
            set_where_from_metadata(str(filepath), current_url)
            saved_files.append(str(filepath))
            
            # 提取新链接并更新队列 (复刻逻辑)
            found_links = self.extract_links_pure(html, current_url, scope_prefix)
            new_links = set(found_links) - self.visited_urls
            urls_to_visit.update(new_links)
            
            # 每 10 个文件显示一次进度
            if len(saved_files) % 10 == 0 and status_callback:
                status_callback(f"✅ 已保存 {len(saved_files)} 个文档，当前队列中还有 {len(urls_to_visit)} 个待爬取链接")

        if status_callback:
            status_callback(f"🎉 爬取完成！共捕获 {len(saved_files)} 个页面")
        
        return saved_files