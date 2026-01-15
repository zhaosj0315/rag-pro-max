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

# 🔥 新增：导入智能优化器
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
        
        # 🔥 新增：智能优化器
        self.optimizer = CrawlOptimizer()
        
        # 状态持久化 - 使用唯一文件名避免冲突
        import time
        import os
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
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
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
        """检查robots.txt合规性 - 宽松模式"""
        domain = urlparse(url).netloc
        
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        robots_url = f"https://{domain}/robots.txt"
        
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    # 更宽松的检查 - 只阻止明确的 "Disallow: /"
                    lines = robots_content.lower().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line == 'disallow: /' and 'user-agent: *' in robots_content.lower():
                            self.robots_cache[domain] = False
                            return False
        except:
            pass
        
        # 默认允许访问
        self.robots_cache[domain] = True
        return True
    
    def content_fingerprint(self, text: str) -> str:
        """生成内容指纹用于去重"""
        # 清理文本并生成哈希
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
        async with self.semaphore:  # 限制并发数
            for attempt in range(max_retries):
                try:
                    # 智能延迟
                    if attempt > 0:
                        delay = self.delay_range[1] * (2 ** attempt)
                        await asyncio.sleep(min(delay, 10))
                    else:
                        await asyncio.sleep(
                            __import__('random').uniform(*self.delay_range)
                        )
                    
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            return content
                        elif response.status == 429:  # 限流
                            await asyncio.sleep(5)
                            continue
                        else:
                            break
                            
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.failed_urls.add(url)
                    continue
            
            return None
    
    def extract_links(self, html_content: str, base_url: str, scope_prefix: str = None, max_links: int = 999) -> List[str]:
        """提取链接 - 优化：支持自定义作用域前缀"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
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
                
                # 构建完整URL并去除参数/锚点
                full_url = urljoin(base_url, href).split('#')[0].split('?')[0].rstrip('/')
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
        """智能确定爬取作用域"""
        parsed = urlparse(url)
        path = parsed.path
        
        # 针对阿里云帮助文档的专项优化
        # 格式: /zh/product-name/sub-product/...
        if 'help.aliyun.com' in parsed.netloc:
            parts = path.strip('/').split('/')
            if len(parts) >= 2:
                # 保留前两级或三级作为根 (例如 /zh/analyticdb/analyticdb-for-mysql/)
                # 通常是 /语言/一级产品/二级产品/
                if len(parts) >= 3 and parts[0] in ['zh', 'en']:
                     return '/' + '/'.join(parts[:3]) + '/'
                elif len(parts) >= 2:
                     return '/' + '/'.join(parts[:2]) + '/'
        
        # 默认策略：保留当前目录
        if not path.endswith('/'):
            path = path.rsplit('/', 1)[0] + '/'
        return path
    
    def extract_content(self, html_content: str) -> str:
        """提取页面内容 (使用高保真 HTML2Text 转换)"""
        try:
            # 优先使用带 html2text 后端的转换器
            return HtmlToMarkdown.convert_with_html2text(html_content)
        except Exception as e:
            logger.warning(f"⚠️ 转换失败，降级到标准转换: {e}")
            return HtmlToMarkdown.convert(html_content)
    
    async def crawl_url(self, url: str, status_callback: Optional[Callable] = None, ignore_robots: bool = False) -> Optional[Dict]:
        """爬取单个URL"""
        if status_callback:
            status_callback(f"🔍 正在处理: {url}")
            
        if url in self.visited_urls:
            return None
            
        if url in self.failed_urls:
            return None
        
        # 检查robots.txt（可选）
        if not ignore_robots and not await self.check_robots_txt(url):
            if status_callback:
                status_callback(f"🚫 robots.txt 禁止: {url}")
            return None
        
        html_content = await self.fetch_with_retry(url)
        if not html_content:
            if status_callback:
                status_callback(f"❌ 获取失败: {url}")
            return None
        
        # 提取内容
        content = self.extract_content(html_content)
        
        # 检查内容是否为空或太短
        if len(content.strip()) < 100:
            return None
        
        # 内容去重检查
        if self.is_duplicate_content(content):
            return None
        
        # 提取标题
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            title = title.strip()
        except:
            title = "No Title"
        
        self.visited_urls.add(url)
        
        if status_callback:
            status_callback(f"✅ 已保存: {title} ({len(content)} 字符)")
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'html': html_content,
            'timestamp': time.time()
        }
    
    def get_smart_recommendations(self, url: str) -> Dict:
        """🔥 新增：获取智能爬取推荐参数"""
        return self.optimizer.analyze_website(url)

    async def crawl_with_smart_params(self, 
                                     start_url: str,
                                     use_smart_params: bool = True,
                                     manual_depth: Optional[int] = None,
                                     manual_pages: Optional[int] = None,
                                     output_dir: str = "crawled_data",
                                     status_callback: Optional[Callable] = None) -> List[str]:
        """🔥 新增：使用智能参数推荐的异步爬取方法"""
        
        if use_smart_params:
            # 获取智能推荐
            recommendations = self.get_smart_recommendations(start_url)
            
            if status_callback:
                status_callback("🧠 智能分析网站...")
                status_callback(f"📊 网站类型: {recommendations['site_type']}")
                status_callback(f"📝 描述: {recommendations['description']}")
                status_callback(f"🎯 推荐深度: {recommendations['recommended_depth']}层")
                status_callback(f"📄 推荐页数: {recommendations['recommended_pages']}页/层")
                status_callback(f"📈 预估总页数: {recommendations['estimated_pages']:,}页")
                status_callback(f"🔍 置信度: {recommendations['confidence']:.1%}")
            
            # 使用推荐参数（可被手动参数覆盖）
            max_depth = manual_depth or recommendations['recommended_depth']
            max_pages_per_level = manual_pages or recommendations['recommended_pages']
            
            if status_callback:
                status_callback(f"⚙️ 最终参数: 深度={max_depth}, 页数={max_pages_per_level}")
        else:
            # 使用手动参数或默认值
            max_depth = manual_depth or 3
            max_pages_per_level = manual_pages or 8
            
            if status_callback:
                status_callback(f"🔧 手动参数: 深度={max_depth}, 页数={max_pages_per_level}")
        
        # 调用原有的爬取方法
        return await self.crawl_recursive(
            start_url=start_url,
            max_depth=max_depth,
            max_pages_per_level=max_pages_per_level,
            output_dir=output_dir,
            status_callback=status_callback
        )
    
    async def crawl_recursive(
        self, 
        start_url: str, 
        max_depth: int = 3, 
        max_pages_per_level: int = 8,
        output_dir: str = "crawled_data",
        status_callback: Optional[Callable] = None
    ) -> List[str]:
        """异步递归爬取 - 修复递归逻辑"""
        
        # 加载之前的状态
        await self.load_state()
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 🔥 计算全局作用域
        global_scope = self._determine_scope(start_url)
        
        # [Aliyun Optimization] 专项优化：文档全量模式
        is_doc_mode = False
        crawl_ignore_robots = self.ignore_robots
        if global_scope and len(global_scope) > 1: # 确保不是根目录
            is_doc_mode = True
            max_depth = max(max_depth, 50) # 强制扩展深度至50层
            crawl_ignore_robots = True # 文档模式下强制忽略 robots.txt 以确保全量
            if status_callback:
                status_callback(f"🌐 锁定爬取作用域: {global_scope}")
                status_callback(f"📚 激活文档全量模式: 深度扩展至 {max_depth}，解除单层页数限制，忽略 robots.txt")
        
        current_level = [start_url]
        saved_files = []
        
        if status_callback:
            status_callback(f"🚀 开始异步递归爬取: {start_url}")
            status_callback(f"📊 递归参数: 最大深度={max_depth}, 基础页数={max_pages_per_level}, 并发={self.max_concurrent}")
            for d in range(1, max_depth + 1):
                expected_pages = max_pages_per_level ** d
                status_callback(f"   第{d}层预计: {expected_pages} 页")
        
        for depth in range(1, max_depth + 1):
            if not current_level:
                break
            
            # 🔥 关键修复：每层的页面数量应该是 max_pages_per_level^depth
            # [Aliyun Optimization] 文档模式下解除限制
            if is_doc_mode:
                current_layer_limit = 999999 # 无限宽
            else:
                current_layer_limit = max_pages_per_level ** depth
            
            # 限制当前层处理的URL数量
            current_level = current_level[:current_layer_limit]
            
            if status_callback:
                status_callback(f"📂 第{depth}层: 并发处理 {len(current_level)} 个URL")
            
            # 并发爬取当前层级的所有URL
            tasks = [self.crawl_url(url, status_callback, ignore_robots=crawl_ignore_robots) for url in current_level]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            next_level = []
            level_success = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    if status_callback:
                        status_callback(f"❌ 爬取失败: {current_level[i]} - {result}")
                    continue
                
                if result is None:
                    continue
                
                level_success += 1
                
                # 保存文件
                url = result.get('url', '')
                title = result.get('title', '').strip()
                
                # 方案 A: 优先使用 URL 路径生成文件名
                path = urlparse(url).path
                if path.startswith('/'): path = path[1:]
                url_filename = path.replace('/', '_').strip('_')
                
                if url_filename:
                    url_filename = "".join(c for c in url_filename if c.isalnum() or c in ('-', '_')).strip()
                    filename = f"{url_filename}.md"
                elif title:
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_title = safe_title.replace(' ', '_')[:50]
                    filename = f"{safe_title}.md"
                else:
                    filename = f"page_{int(time.time())}_{len(saved_files)+1}.md"
                
                filepath = output_path / filename
                if filepath.exists():
                    filename = f"{filename[:-3]}_{len(saved_files)+1}.md"
                    filepath = output_path / filename
                
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    await f.write(f"**URL:** {result['url']}\n\n")
                    await f.write(f"# {result['title']}\n\n")
                    await f.write(f"**Timestamp:** {result['timestamp']}\n")
                    await f.write(f"**Content Length:** {len(result['content'])}\n\n")
                    await f.write(f"**Content:**\n\n{result['content']}")
                
                set_where_from_metadata(str(filepath), result['url'])
                saved_files.append(str(filepath))
                
                # 如果还没到最大深度，提取下一级链接
                if depth < max_depth:
                    # [Aliyun Optimization] 解除单页链接提取上限
                    extract_limit = 100000 if is_doc_mode else 999
                    links = self.extract_links(result['html'], result['url'], scope_prefix=global_scope, max_links=extract_limit)
                    next_level.extend(links)
            
            # 去重并准备下一层
            current_level = [u for u in list(set(next_level)) if u not in self.visited_urls]
            
            if status_callback:
                status_callback(f"🎯 第{depth}层完成: 成功 {level_success} 页，新发现 {len(current_level)} 个待爬取链接")
            
            await self.save_state()
            
            if not current_level:
                break
        
        if status_callback:
            status_callback(f"🎉 异步爬取完成！获取 {len(saved_files)} 个页面")
        
        return saved_files

# 使用示例
async def main():
    async with AsyncWebCrawler(max_concurrent=20) as crawler:
        def progress_callback(message):
            logger.info(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        files = await crawler.crawl_recursive(
            start_url="https://docs.python.org/",
            max_depth=3,
            max_pages_per_level=10,
            output_dir="async_crawled_data",
            status_callback=progress_callback
        )
        
        logger.info(f"爬取完成，保存了 {len(files)} 个文件")

if __name__ == "__main__":
    asyncio.run(main())
