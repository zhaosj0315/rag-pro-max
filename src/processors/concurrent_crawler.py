from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
并发爬取管理器
支持多进程和多线程混合模式，突破GIL限制
"""

import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, Empty
from typing import List, Dict, Callable, Optional
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
import re

# 🔥 新增：导入智能优化器
from .crawl_optimizer import CrawlOptimizer

def fetch_url_worker(args):
    """多进程工作函数"""
    # 解包参数 (增加了 keyword)
    if len(args) == 6:
        url, timeout, user_agents, base_delay, max_delay, keyword = args
    else:
        url, timeout, user_agents, base_delay, max_delay = args
        keyword = None
    
    # 标记：是否是初始入口 URL (如果是 args 里的第一个 URL 或者深度为 1)
    # 注意：这里的逻辑需要配合 args 传入深度信息，或者简单判断 url 深度
    
    start_time = time.time()
    result = {
        'url': url,
        'success': False,
        'content': None,
        'title': None,
        'links': [],
        'response_time': 0,
        'error': None
    }
    
    try:
        # 创建新的session
        session = requests.Session()
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        response = session.get(url, headers=headers, timeout=timeout)
        response_time = time.time() - start_time
        result['response_time'] = response_time
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else url
            result['title'] = title
            
            # --- v5.5.9 增强逻辑：入口层宽容处理 ---
            # 如果 URL 路径很浅（可能是首页或搜索页），我们允许它作为跳板
            parsed_current = urlparse(url)
            is_entry_point = parsed_current.path == "/" or parsed_current.path == "" or "search" in url.lower() or "Special:" in url
            
            is_relevant = True
            if keyword:
                parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                
                # 标题校验：如果不是入口点，则必须包含核心词
                if core_subject not in title.lower() and not is_entry_point:
                     is_relevant = False
            
            if is_relevant:
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                content = soup.get_text()
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                # 如果标题不相关但作为跳板通过了，我们不保存其内容，仅用于提取链接
                if keyword and core_subject not in title.lower() and is_entry_point:
                    result['content'] = "" 
                else:
                    result['content'] = content
            else:
                result['content'] = "" 
            
            # 提取链接
            base_domain = parsed_current.netloc
            
            # --- v5.6.0 多源适配：针对特定站点的搜索结果页进行定向提取 ---
            extracted_links = []
            
            # 1. 知乎搜索页适配
            if "zhihu.com" in base_domain and "search" in url:
                # 知乎搜索结果通常在 .ContentItem-title a 或类似结构中
                # 同时也尝试通用提取，但优先寻找高价值区域
                for link in soup.select('.ContentItem-title a') + soup.select('.SearchItem-Title a'):
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = urljoin("https://www.zhihu.com", href)
                        extracted_links.append(href)
                        
            # 2. 百度百科搜索页适配
            elif "baike.baidu.com" in base_domain:
                # 百度百科结果通常在 .result-title a
                for link in soup.select('.result-title a') + soup.select('a.result-title'):
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = urljoin("https://baike.baidu.com", href)
                        extracted_links.append(href)
            
            # 3. Bing 搜索页适配
            elif "bing.com" in base_domain:
                # Bing 结果通常在 li.b_algo h2 a
                for link in soup.select('li.b_algo h2 a'):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        extracted_links.append(href)

            # 4. DuckDuckGo (HTML) 适配
            elif "duckduckgo.com" in base_domain:
                # DDG 结果在 .result__a
                for link in soup.select('.result__a'):
                    href = link.get('href')
                    # DDG 有时会用重定向链接，这里简化处理，直接取
                    if href:
                        extracted_links.append(href)

            # 5. 阿里云帮助文档适配 (Aliyun Help)
            elif "help.aliyun.com" in base_domain:
                # A. 增强内容提取：聚焦文档核心区域
                # 阿里云通常使用 .markdown-body 或 .icms-help-docs-content
                main_content = soup.select_one('.markdown-body') or \
                               soup.select_one('.icms-help-docs-content') or \
                               soup.select_one('#main-content') or \
                               soup.select_one('article')
                
                if main_content:
                    # 仅在找到特定内容区域时清理并提取，覆盖默认的全页提取
                    # 1. 移除干扰标签
                    for tag in main_content(["script", "style", "button", "input"]):
                        tag.decompose()
                    
                    # 2. 移除干扰类 (如反馈按钮、复制按钮等)
                    for tag in main_content.select(".feedback-wrapper, .copy-btn, .header-anchor"):
                        tag.decompose()
                    
                    content_text = main_content.get_text()
                    lines = (line.strip() for line in content_text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    result['content'] = ' '.join(chunk for chunk in chunks if chunk)
                
                # B. 关键词增强：从 Meta 标签提取
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                if meta_keywords:
                    keywords_text = meta_keywords.get('content', '')
                    if keywords_text:
                        # 将关键词前置，提高相关性评分
                        result['content'] = f"Keywords: {keywords_text}\n\n{result.get('content', '')}"

                # C. 链接提取优化：优先抓取目录和下一篇
                # 1. 尝试抓取 "下一篇" 链接 (通常在底部)
                next_links = soup.select('a.next-link') or soup.select('.post-navigation a')
                for link in next_links:
                    href = link.get('href')
                    if href:
                         extracted_links.append(urljoin("https://help.aliyun.com", href))
                
                # 2. 尝试抓取左侧目录树 (Sidebar)
                sidebar = soup.select_one('.menu-tree') or soup.select_one('.left-nav') or soup.select_one('div[class*="sidebar"]')
                if sidebar:
                    for link in sidebar.find_all('a', href=True):
                        href = link.get('href')
                        if href:
                             extracted_links.append(urljoin("https://help.aliyun.com", href))

            # 6. 通用提取 (作为保底)
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    extracted_links.append(urljoin(url, href))
            
            # 去重并过滤
            unique_links = list(set(extracted_links))
            
            for full_url in unique_links:
                parsed = urlparse(full_url)
                
                # 允许跨域抓取的情况：从搜索入口跳到了具体内容页 (通常域名会变，或者是同域)
                # 现在的逻辑：如果当前是入口页，我们允许它跳到任何看似相关的同类网站或同域页面
                
                allow_link = False
                if parsed.netloc == base_domain:
                    allow_link = True
                elif "zhihu.com" in parsed.netloc or "baidu.com" in parsed.netloc or "wikipedia.org" in parsed.netloc:
                    allow_link = True
                # 🔥 核心增强：如果来源是通用搜索引擎 (Bing/DDG)，则允许跳转到任何外部域 (除了广告/垃圾站)
                elif "bing.com" in base_domain or "duckduckgo.com" in base_domain:
                    allow_link = True
                
                if allow_link:
                    should_add = True
                    if keyword: 
                        link_text = ""
                        # 尝试找回 link 对应的 text (这里为了性能简化了，直接用 URL 判定为主)
                        # 如果需要更精准，上面提取时应该同时提取 text
                        link_path = parsed.path.lower()
                        parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                        core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                        
                        # 链接过滤
                        # 注意：对于知乎等，链接本身可能不含关键词 (如 /question/123456)，所以必须依赖上面的 select 提取时的精准性
                        # 或者我们放宽一点：如果是从定向选择器里出来的，默认它是相关的？
                        # 目前我们这里只拿到了 URL list，丢失了 text 上下文。
                        # 改进：如果 URL 包含 question/article (知乎) 或 item (百度)，且来源是搜索页，则倾向于保留
                        
                        is_content_url = "/question/" in full_url or "/article/" in full_url or "/item/" in full_url or "/wiki/" in full_url
                        
                        if core_subject not in link_path and not is_content_url:
                             # 既没关键词，又不是典型的内容页路径，大概率是杂音
                             should_add = False
                        
                        if any(x in link_path for x in ['login', 'signup', 'register', 'cart', 'search', 'video']):
                            should_add = False
                            
                    if should_add:
                        result['links'].append(full_url)
            
            result['success'] = True
        else:
            result['error'] = f"HTTP {response.status_code}"
            
    except Exception as e:
        result['error'] = str(e)
        result['response_time'] = time.time() - start_time
    
    # 智能延迟
    time.sleep(random.uniform(0.5, 1.5))
    
    return result

class ConcurrentCrawler:
    """并发爬取管理器 - 支持多进程和多线程"""
    
    def __init__(self, max_workers=None, use_processes=True, base_delay=1.0, max_delay=3.0):
        # 自动检测最佳worker数量
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            if use_processes:
                # 进程模式：使用CPU核心数，但不超过6个（避免过度消耗资源）
                max_workers = min(cpu_count, 6)
            else:
                # 线程模式：可以使用更多线程（I/O密集型）
                max_workers = min(cpu_count * 2, 8)
        
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # 🔥 新增：智能优化器
        self.optimizer = CrawlOptimizer()
        
        # 线程模式才需要session
        if not use_processes:
            self.session = requests.Session()
        
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'response_times': []
        }
        
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
    
    def get_smart_recommendations(self, url: str) -> Dict:
        """🔥 新增：获取智能爬取推荐参数"""
        return self.optimizer.analyze_website(url)

    def crawl_with_smart_params(self, 
                               start_urls: List[str],
                               use_smart_params: bool = True,
                               manual_depth: Optional[int] = None,
                               manual_pages: Optional[int] = None,
                               keyword: str = None,
                               progress_callback: Optional[Callable] = None) -> List[Dict]:
        """🔥 新增：使用智能参数推荐的并发爬取方法"""
        
        if not start_urls:
            return []
        
        # 使用第一个URL进行智能分析
        main_url = start_urls[0]
        
        if use_smart_params:
            # 获取智能推荐
            recommendations = self.get_smart_recommendations(main_url)
            
            if progress_callback:
                progress_callback("🧠 智能分析网站...")
                progress_callback(f"📊 网站类型: {recommendations['site_type']}")
                progress_callback(f"📝 描述: {recommendations['description']}")
                progress_callback(f"🎯 推荐深度: {recommendations['recommended_depth']}层")
                progress_callback(f"📄 推荐页数: {recommendations['recommended_pages']}页/层")
                progress_callback(f"📈 预估总页数: {recommendations['estimated_pages']:,}页")
                progress_callback(f"🔍 置信度: {recommendations['confidence']:.1%}")
            
            # 使用推荐参数（可被手动参数覆盖）
            max_depth = manual_depth or recommendations['recommended_depth']
            max_pages_per_level = manual_pages or recommendations['recommended_pages']
            
            if progress_callback:
                progress_callback(f"⚙️ 最终参数: 深度={max_depth}, 页数={max_pages_per_level}")
        else:
            # 使用手动参数或默认值
            max_depth = manual_depth or 2
            max_pages_per_level = manual_pages or 20
            
            if progress_callback:
                progress_callback(f"🔧 手动参数: 深度={max_depth}, 页数={max_pages_per_level}")
        
        # 调用原有的爬取方法
        return self.crawl_with_depth(
            start_urls=start_urls,
            max_depth=max_depth,
            max_pages_per_level=max_pages_per_level,
            keyword=keyword,
            progress_callback=progress_callback
        )
    
    def _fetch_url_thread(self, url: str, timeout=15, keyword: str = None) -> Dict:
        """线程模式的URL获取"""
        start_time = time.time()
        result = {
            'url': url,
            'success': False,
            'content': None,
            'title': None,
            'links': [],
            'response_time': 0,
            'error': None
        }
        
        try:
            self.stats['total_requests'] += 1
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(url, headers=headers, timeout=timeout)
            response_time = time.time() - start_time
            result['response_time'] = response_time
            self.stats['response_times'].append(response_time)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 提取标题
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else url
                result['title'] = title
                
                # --- 相关性校验 ---
                is_relevant = True
                if keyword:
                    parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                    core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                    if core_subject not in title.lower():
                        if "about" not in url.lower():
                            is_relevant = False
                
                if is_relevant:
                    # 提取内容
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    content = soup.get_text()
                    lines = (line.strip() for line in content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = ' '.join(chunk for chunk in chunks if chunk)
                    result['content'] = content
                else:
                    result['content'] = ""

                # 提取链接
                base_domain = urlparse(url).netloc
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == base_domain:
                            # 关键词过滤
                            should_add = True
                            if keyword:
                                link_text = link.get_text().strip().lower()
                                link_path = parsed.path.lower()
                                parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                                core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                                if core_subject not in link_text and core_subject not in link_path:
                                    should_add = False
                            
                            if should_add:
                                result['links'].append(full_url)
                
                result['success'] = True
                self.stats['successful_requests'] += 1
            else:
                result['error'] = f"HTTP {response.status_code}"
                self.stats['failed_requests'] += 1
                
        except Exception as e:
            result['error'] = str(e)
            result['response_time'] = time.time() - start_time
            self.stats['failed_requests'] += 1
        
        # 智能延迟
        self._smart_delay(result['response_time'])
        return result
    
    def _smart_delay(self, response_time=None):
        """智能延迟策略"""
        if response_time:
            # 根据响应时间调整延迟
            if response_time < 1.0:
                delay = self.base_delay * 0.5  # 快速响应，减少延迟
            elif response_time > 3.0:
                delay = self.base_delay * 2.0  # 慢速响应，增加延迟
            else:
                delay = self.base_delay
        else:
            delay = self.base_delay
            
        # 添加随机性避免被检测
        delay += random.uniform(0, 0.5)
        delay = min(delay, self.max_delay)
        
        time.sleep(delay)
    
    def crawl_urls_concurrent(self, urls: List[str], 
                            progress_callback: Optional[Callable] = None,
                            max_pages: int = 50,
                            keyword: str = None) -> List[Dict]:
        """并发爬取URL列表"""
        if not urls:
            return []
        
        self.stats['start_time'] = time.time()
        results = []
        processed_urls = set()
        
        # 限制爬取数量
        urls_to_process = urls[:max_pages]
        
        if self.use_processes:
            # 多进程模式
            if progress_callback and urls_to_process:
                progress_callback(f"🚀 正在启动批次处理 ({len(urls_to_process)} 个链接)...")

            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # 准备参数
                args_list = []
                for url in urls_to_process:
                    if url not in processed_urls:
                        # 传递 keyword 参数
                        args_list.append((url, 15, self.user_agents, self.base_delay, self.max_delay, keyword))
                        processed_urls.add(url)
                
                # 提交任务
                future_to_url = {executor.submit(fetch_url_worker, args): args[0] for args in args_list}
                
                # 收集结果
                completed = 0
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        
                        # 更新统计（进程模式需要手动更新）
                        if result['success']:
                            self.stats['successful_requests'] += 1
                        else:
                            self.stats['failed_requests'] += 1
                        self.stats['total_requests'] += 1
                        self.stats['response_times'].append(result['response_time'])
                        
                        if progress_callback:
                            progress = completed / len(future_to_url)
                            status_icon = "✅" if (result['success'] and result.get('content')) else "⏳"
                            title_summary = result.get('title', '无标题')[:20]
                            progress_callback(f"{status_icon} [{completed}/{len(future_to_url)}] 正在处理: {title_summary}... ({url})", progress)
                            
                    except Exception as e:
                        error_result = {
                            'url': url,
                            'success': False,
                            'content': None,
                            'title': None,
                            'links': [],
                            'response_time': 0,
                            'error': str(e)
                        }
                        results.append(error_result)
                        completed += 1
                        self.stats['failed_requests'] += 1
                        self.stats['total_requests'] += 1
        else:
            # 多线程模式
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {}
                for url in urls_to_process:
                    if url not in processed_urls:
                        # 传递 keyword (线程模式下 fetch_url_thread 可以访问)
                        # 注意：_fetch_url_thread 需要修改以接受 keyword
                        future = executor.submit(self._fetch_url_thread, url, 15, keyword)
                        future_to_url[future] = url
                        processed_urls.add(url)
                
                completed = 0
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        
                        if progress_callback:
                            progress = completed / len(future_to_url)
                            status_icon = "✅" if (result['success'] and result.get('content')) else "⏳"
                            title_summary = result.get('title', '无标题')[:20]
                            progress_callback(f"{status_icon} [{completed}/{len(future_to_url)}] 正在处理: {title_summary}... ({url})", progress)
                            
                    except Exception as e:
                        error_result = {
                            'url': url,
                            'success': False,
                            'content': None,
                            'title': None,
                            'links': [],
                            'response_time': 0,
                            'error': str(e)
                        }
                        results.append(error_result)
                        completed += 1
        
        return results
    
    def crawl_with_depth(self, start_urls: List[str], 
                        max_depth: int = 2,
                        max_pages_per_level: int = 20,
                        keyword: str = None,
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
        """按深度并发爬取 - 修复递归逻辑"""
        all_results = []
        current_urls = start_urls
        processed_urls = set()
        
        if progress_callback:
            progress_callback(f"🚀 开始递归并发爬取: 最大深度={max_depth}, 基础页数={max_pages_per_level}")
            if keyword:
                progress_callback(f"🎯 关键词锚定: {keyword}")
            for d in range(1, max_depth + 1):
                expected_pages = max_pages_per_level ** d
                progress_callback(f"   第{d}层预计: {expected_pages} 页")
        
        for depth in range(1, max_depth + 1):
            if not current_urls:
                break
            
            # 目标：每层希望能获取到的有效页面数量
            target_success_count = max_pages_per_level ** depth
            
            # 过滤掉已处理的链接
            level_candidates = [url for url in current_urls if url not in processed_urls]
            
            if not level_candidates:
                if progress_callback:
                    progress_callback(f"⚠️ 第{depth}层: 无新链接可处理，爬取结束")
                break
                
            if progress_callback:
                progress_callback(f"📂 第{depth}层开始: 候选链接 {len(level_candidates)} 个, 目标有效抓取 {target_success_count} 个")
            
            level_results = []
            layer_success_count = 0
            
            # 分批处理直到达到目标或耗尽链接
            batch_start = 0
            while layer_success_count < target_success_count and batch_start < len(level_candidates):
                # 计算本批次大小：目标缺口 * 1.5 (作为缓冲) 但不超过 50
                needed = target_success_count - layer_success_count
                batch_size = min(int(needed * 1.5) + 1, 50)
                
                # 确保不越界
                batch_end = min(batch_start + batch_size, len(level_candidates))
                batch_urls = level_candidates[batch_start:batch_end]
                
                if not batch_urls:
                    break
                    
                # 处理批次
                batch_results = self.crawl_urls_concurrent(
                    batch_urls, 
                    progress_callback,
                    len(batch_urls),
                    keyword=keyword
                )
                
                level_results.extend(batch_results)
                processed_urls.update(batch_urls)
                
                # 统计本批次成功数 (必须是 success=True 且有 content)
                batch_success = sum(1 for r in batch_results if r['success'] and r.get('content'))
                layer_success_count += batch_success
                
                batch_start = batch_end
                
                if progress_callback:
                    progress_callback(f"📊 第{depth}层进度: 已获有效 {layer_success_count}/{target_success_count} 页 (已处理 {batch_start}/{len(level_candidates)})")
            
            all_results.extend(level_results)
            
            # 收集下一层URL - 🔥 关键修复：收集所有有效链接，不限制数量
            next_urls = []
            for result in level_results:
                if result['success'] and result['links']:
                    next_urls.extend(result['links'])
            
            # 去重并准备下一层
            current_urls = list(set(next_urls) - processed_urls)
            
            if progress_callback:
                progress_callback(f"🎯 第{depth}层完成: 最终有效 {layer_success_count} 页 (目标 {target_success_count})，发现 {len(current_urls)} 个新链接")
                if depth < max_depth and current_urls:
                    next_target = max_pages_per_level ** (depth + 1)
                    progress_callback(f"📊 递归统计: 第{depth+1}层将尝试获取 {next_target} 个有效页面")
        
        return all_results
    
    # ... get_stats, reset_stats remain same ...
    def get_stats(self) -> Dict:
        """获取爬取统计信息"""
        if self.stats['start_time']:
            elapsed_time = time.time() - self.stats['start_time']
        else:
            elapsed_time = 0
            
        avg_response_time = 0
        if self.stats['response_times']:
            avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
        
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = self.stats['successful_requests'] / self.stats['total_requests']
        
        pages_per_minute = 0
        if elapsed_time > 0:
            pages_per_minute = self.stats['successful_requests'] / (elapsed_time / 60)
        
        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': success_rate,
            'elapsed_time': elapsed_time,
            'avg_response_time': avg_response_time,
            'pages_per_minute': pages_per_minute,
            'max_workers': self.max_workers,
            'mode': 'process' if self.use_processes else 'thread',
            'cpu_count': os.cpu_count()
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'response_times': []
        }

if __name__ == "__main__":
    pass