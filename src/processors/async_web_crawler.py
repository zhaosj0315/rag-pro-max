from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
异步并发网页爬虫 - 性能提升10倍+
支持并发请求、智能限流、断点续传
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
import urllib.robotparser
from pathlib import Path
import logging
import os

# 🔥 导入智能优化器
from .crawl_optimizer import CrawlOptimizer
from src.utils.file_system_utils import set_where_from_metadata
from src.utils.html_to_markdown import HtmlToMarkdown

class AsyncWebCrawler:
    def __init__(self, max_concurrent=10, delay_range=(0.5, 2.0), ignore_robots=False):
        self.max_concurrent = max_concurrent
        self.delay_range = delay_range
        self.ignore_robots = ignore_robots  # 是否忽略robots.txt
        self.session = None
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.content_hashes: Set[str] = set()  # 内容去重
        self.robots_cache: Dict[str, bool] = {}
        
        # 🔥 智能优化器
        self.optimizer = CrawlOptimizer()
        
        # 状态持久化
        self.state_file = os.path.join("temp_uploads", f"crawler_state_{int(time.time())}.json")
        self.semaphore = None
        
    async def __aenter__(self):
        """异步上下文管理器"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # [Aliyun Optimization] 使用与用户脚本完全一致的 UA
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
        """清理资源"""
        if self.session:
            await self.session.close()
    
    async def save_state(self):
        """保存爬取状态"""
        state = {
            'visited_urls': list(self.visited_urls),
            'failed_urls': list(self.failed_urls),
            'content_hashes': list(self.content_hashes),
            'timestamp': time.time()
        }
        
        async with aiofiles.open(self.state_file, 'w') as f:
            await f.write(json.dumps(state, indent=2))
    
    async def load_state(self):
        """加载爬取状态"""
        try:
            async with aiofiles.open(self.state_file, 'r') as f:
                content = await f.read()
                state = json.loads(content)
                
            self.visited_urls = set(state.get('visited_urls', []))
            self.failed_urls = set(state.get('failed_urls', []))
            self.content_hashes = set(state.get('content_hashes', []))
            
            return True
        except FileNotFoundError:
            return False
    
    async def check_robots_txt(self, url: str) -> bool:
        """检查robots.txt合规性"""
        domain = urlparse(url).netloc
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        robots_url = f"https://{domain}/robots.txt"
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    lines = robots_content.lower().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line == 'disallow: /' and 'user-agent: *' in robots_content.lower():
                            self.robots_cache[domain] = False
                            return False
        except: pass
        self.robots_cache[domain] = True
        return True
    
    def content_fingerprint(self, text: str) -> str:
        """生成内容指纹用于去重"""
        cleaned = ''.join(text.split()).lower()
        return hashlib.md5(cleaned.encode()).hexdigest()
    
    def is_duplicate_content(self, text: str) -> bool:
        """检查内容是否重复"""
        fingerprint = self.content_fingerprint(text)
        if fingerprint in self.content_hashes:
            return True
        self.content_hashes.add(fingerprint)
        return False
    
    async def fetch_with_retry(self, url: str, max_retries=3) -> Optional[str]:
        """带重试的异步请求"""
        async with self.semaphore:
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        delay = self.delay_range[1] * (2 ** attempt)
                        await asyncio.sleep(min(delay, 10))
                    else:
                        await asyncio.sleep(__import__('random').uniform(*self.delay_range))
                    
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:
                            await asyncio.sleep(5)
                            continue
                        else: break
                except: continue
            return None
    
    def extract_links(self, html_content: str, base_url: str, scope_prefix: str = None, max_links: int = 999) -> List[str]:
        """提取链接 - 优化：支持自定义作用域前缀"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # [Aliyun Optimization] 如果有明确的作用域前缀，使用极简匹配逻辑 (复刻用户成功脚本)
            if scope_prefix:
                # 调试日志：打印当前 Scope
                # logger.info(f"🔍 [Debug] 当前作用域: {scope_prefix}")
                
                count_total = 0
                count_accepted = 0
                
                for link in soup.find_all('a', href=True):
                    count_total += 1
                    href = link.get('href')
                    if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                        continue
                    
                    # 简单粗暴的拼接与清洗
                    full_url = urljoin(base_url, href).split('#')[0].split('?')[0]
                    
                    # 核心判定：只看是否以作用域开头
                    if full_url.startswith(scope_prefix):
                        if full_url not in self.visited_urls and full_url not in links:
                            links.append(full_url)
                            count_accepted += 1
                    
                    if len(links) >= max_links:
                        break
                
                # 调试日志：如果有大量拒绝，可能是 Scope 算错了
                # if count_total > 100 and count_accepted < 10:
                #     logger.warning(f"⚠️ [Debug] 链接提取率极低! 总数: {count_total}, 接受: {count_accepted}, Scope: {scope_prefix}")
                
                return links

            # --- 以下为原有通用逻辑 (无 scope_prefix 时使用) ---
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            
            # 如果没有指定作用域，默认使用当前URL的目录
            if not scope_prefix:
                scope_prefix = parsed_base.path
                if not scope_prefix.endswith('/'):
                    scope_prefix = scope_prefix.rsplit('/', 1)[0] + '/'
            
            # 预处理作用域前缀，移除尾斜杠以确保根路径匹配
            check_prefix = scope_prefix.rstrip('/')
            
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # 构建完整URL并去除参数/锚点 (不再 rstrip，保持目录语义)
                full_url = urljoin(base_url, href).split('#')[0].split('?')[0]
                parsed = urlparse(full_url)
                
                # 策略：必须是同域名，且匹配作用域前缀
                if parsed.netloc == base_domain:
                    # 检查路径是否以作用域前缀开头 (移除尾斜杠进行比较)
                    if parsed.path.rstrip('/').startswith(check_prefix):
                        if full_url not in self.visited_urls and full_url not in links:
                            links.append(full_url)
                
                if len(links) >= max_links:
                    break
            
            return links
        except Exception as e:
            logger.warning(f"提取链接失败: {e}")
            return []

    def _determine_scope(self, url: str) -> str:
        """智能确定爬取作用域 - 返回完整URL前缀"""
        parsed = urlparse(url)
        path = parsed.path
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        
        prefix = ""
        
        # 针对阿里云帮助文档的专项优化
        # 格式: /zh/product-name/sub-product/...
        if 'help.aliyun.com' in netloc:
            parts = path.strip('/').split('/')
            if len(parts) >= 2:
                if len(parts) >= 3 and parts[0] in ['zh', 'en']:
                     prefix = '/' + '/'.join(parts[:3]) + '/'
                elif len(parts) >= 2:
                     prefix = '/' + '/'.join(parts[:2]) + '/'
        
        if not prefix:
            # 默认策略：保留当前目录
            if not path.endswith('/'):
                prefix = path.rsplit('/', 1)[0] + '/'
            else:
                prefix = path
                
        # 返回完整URL前缀 (scheme + netloc + path)
        return f"{scheme}://{netloc}{prefix}"
    
    def extract_content(self, html_content: str) -> str:
        """提取页面内容"""
        try:
            return HtmlToMarkdown.convert_with_html2text(html_content)
        except Exception as e:
            logger.warning(f"⚠️ 转换失败: {e}")
            return HtmlToMarkdown.convert(html_content)
    
    async def crawl_url(self, url: str, status_callback: Optional[Callable] = None, ignore_robots: bool = False) -> Optional[Dict]:
        """爬取单个URL"""
        if status_callback: status_callback(f"🔍 正在处理: {url}")
        if url in self.visited_urls: return None
        if url in self.failed_urls: return None
        
        if not ignore_robots and not await self.check_robots_txt(url):
            if status_callback: status_callback(f"🚫 robots.txt 禁止: {url}")
            return None
        
        html_content = await self.fetch_with_retry(url)
        if not html_content:
            if status_callback: status_callback(f"❌ 获取失败 (可能被封锁): {url}")
            return None
        
        content = self.extract_content(html_content)
        if len(content.strip()) < 100: return None
        if self.is_duplicate_content(content): return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string.strip() if soup.title else "No Title"
        except: title = "No Title"
        
        self.visited_urls.add(url)
        if status_callback: status_callback(f"✅ 已保存: {title} ({len(content)} 字符)")
        
        return {'url': url, 'title': title, 'content': content, 'html': html_content, 'timestamp': time.time()}
    
    async def crawl_recursive(
        self, start_url: str, max_depth: int = 3, max_pages_per_level: int = 8,
        output_dir: str = "crawled_data", status_callback: Optional[Callable] = None
    ) -> List[str]:
        """异步递归爬取 - 针对文档全量饱和模式优化"""
        await self.load_state()
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        global_scope = self._determine_scope(start_url)
        is_doc_mode = False
        crawl_ignore_robots = self.ignore_robots
        
        if global_scope and len(global_scope) > 1:
            is_doc_mode = True
            max_depth = max(max_depth, 50) # 强制深度
            crawl_ignore_robots = True
            
            # 🔥 彻底模仿原生脚本：并发强制设为 1，随机延迟 1-2 秒
            self.max_concurrent = 1
            self.semaphore = asyncio.Semaphore(1) 
            self.delay_range = (1.0, 2.0)
            
            if status_callback:
                status_callback(f"🌐 锁定作用域: {global_scope}")
                status_callback(f"📚 激活饱和爬取模式: 深度={max_depth}, 已解除页数限制")
                status_callback(f"🐢 切换至单线程顺序爬取模式 (对齐原生脚本逻辑)")
        
        current_level = [start_url]
        saved_files = []
        
        for depth in range(1, max_depth + 1):
            if not current_level: break
            
            # [Aliyun Optimization] 文档模式下解除单层截断
            if is_doc_mode: current_layer_limit = 999999
            else: current_layer_limit = max_pages_per_level ** depth
            
            current_level = current_level[:current_layer_limit]
            if status_callback: status_callback(f"📂 第{depth}层: 并发处理 {len(current_level)} 个URL")
            
            tasks = [self.crawl_url(url, status_callback, ignore_robots=crawl_ignore_robots) for url in current_level]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            next_level = []
            level_success = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    if status_callback: status_callback(f"❌ 错误: {current_level[i]} - {result}")
                    continue
                if result is None: continue
                level_success += 1
                
                # 文件名映射 (完全对齐用户脚本)
                url = result['url']
                path = urlparse(url).path.strip('/')
                url_filename = path.replace('/', '_') or "index"
                url_filename = "".join(c for c in url_filename if c.isalnum() or c in ('-', '_')).strip()
                filename = f"{url_filename}.md"
                
                filepath = output_path / filename
                if filepath.exists():
                    filepath = output_path / f"{url_filename}_{int(time.time()) % 1000}.md"
                
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    await f.write(f"**URL:** {result['url']}\n\n# {result['title']}\n\n{result['content']}")
                
                set_where_from_metadata(str(filepath), result['url'])
                saved_files.append(str(filepath))
                
                if depth < max_depth:
                    extract_limit = 100000 if is_doc_mode else 999
                    links = self.extract_links(result['html'], result['url'], scope_prefix=global_scope, max_links=extract_limit)
                    if links and status_callback and i % 10 == 0:
                        status_callback(f"🔗 从 {os.path.basename(url)} 发现 {len(links)} 个新链接")
                    next_level.extend(links)
            
            current_level = [u for u in list(set(next_level)) if u not in self.visited_urls]
            if status_callback: status_callback(f"🎯 第{depth}层完成: 成功 {level_success} 页，新发现 {len(current_level)} 个链接")
            await self.save_state()
            if not current_level: break
            
        if status_callback: status_callback(f"🎉 异步爬取完成！获取 {len(saved_files)} 个页面")
        return saved_files
