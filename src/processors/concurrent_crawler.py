from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
并发爬取管理器
支持多进程和多线程混合模式，突破GIL限制
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
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
            parsed_current = urlparse(url)
            is_entry_point = parsed_current.path == "/" or parsed_current.path == "" or "search" in url.lower() or "Special:" in url
            
            is_relevant = True
            if keyword:
                parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                
                # 标题校验
                if core_subject not in title.lower() and not is_entry_point:
                     is_relevant = False
            
            if is_relevant:
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                content = soup.get_text()
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                if keyword and core_subject not in title.lower() and is_entry_point:
                    result['content'] = "" 
                else:
                    result['content'] = content
            else:
                result['content'] = "" 
            
            # 提取链接
            base_domain = parsed_current.netloc
            extracted_links = []
            
            # 1. 知乎搜索页适配
            if "zhihu.com" in base_domain and "search" in url:
                for link in soup.select('.ContentItem-title a') + soup.select('.SearchItem-Title a'):
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = urljoin("https://www.zhihu.com", href)
                        extracted_links.append(href)
                        
            # 2. 百度百科搜索页适配
            elif "baike.baidu.com" in base_domain:
                for link in soup.select('.result-title a') + soup.select('a.result-title'):
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = urljoin("https://baike.baidu.com", href)
                        extracted_links.append(href)
            
            # 3. Bing 搜索页适配
            elif "bing.com" in base_domain:
                for link in soup.select('li.b_algo h2 a'):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        extracted_links.append(href)

            # 4. DuckDuckGo (HTML) 适配
            elif "duckduckgo.com" in base_domain:
                for link in soup.select('.result__a'):
                    href = link.get('href')
                    if href:
                        extracted_links.append(href)

            # 5. 阿里云帮助文档适配
            elif "help.aliyun.com" in base_domain:
                main_content = soup.select_one('.markdown-body') or \
                               soup.select_one('.icms-help-docs-content') or \
                               soup.select_one('#main-content') or \
                               soup.select_one('article')
                
                if main_content:
                    for tag in main_content(["script", "style", "button", "input"]):
                        tag.decompose()
                    for tag in main_content.select(".feedback-wrapper, .copy-btn, .header-anchor"):
                        tag.decompose()
                    
                    content_text = main_content.get_text()
                    lines = (line.strip() for line in content_text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    result['content'] = ' '.join(chunk for chunk in chunks if chunk)
                
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                if meta_keywords:
                    keywords_text = meta_keywords.get('content', '')
                    if keywords_text:
                        result['content'] = f"Keywords: {keywords_text}\n\n{result.get('content', '')}"

                next_links = soup.select('a.next-link') or soup.select('.post-navigation a')
                for link in next_links:
                    href = link.get('href')
                    if href:
                         extracted_links.append(urljoin("https://help.aliyun.com", href))
                
                sidebar = soup.select_one('.menu-tree') or soup.select_one('.left-nav') or soup.select_one('div[class*="sidebar"]')
                if sidebar:
                    for link in sidebar.find_all('a', href=True):
                        href = link.get('href')
                        if href:
                             extracted_links.append(urljoin("https://help.aliyun.com", href))

            # 6. 通用提取
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    extracted_links.append(urljoin(url, href))
            
            unique_links = list(set(extracted_links))
            
            for full_url in unique_links:
                parsed = urlparse(full_url)
                
                allow_link = False
                if parsed.netloc == base_domain:
                    allow_link = True
                elif "zhihu.com" in parsed.netloc or "baidu.com" in parsed.netloc or "wikipedia.org" in parsed.netloc:
                    allow_link = True
                elif "bing.com" in base_domain or "duckduckgo.com" in base_domain:
                    allow_link = True
                
                if allow_link:
                    should_add = True
                    if keyword: 
                        link_path = parsed.path.lower()
                        parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                        core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                        
                        is_content_url = "/question/" in full_url or "/article/" in full_url or "/item/" in full_url or "/wiki/" in full_url
                        
                        if core_subject not in link_path and not is_content_url:
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
    
    time.sleep(random.uniform(0.5, 1.5))
    return result

class ConcurrentCrawler:
    """并发爬取管理器 - 支持多进程和多线程"""
    
    def __init__(self, max_workers=None, use_processes=True, base_delay=1.0, max_delay=3.0):
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            if use_processes:
                max_workers = min(cpu_count, 6)
            else:
                max_workers = min(cpu_count * 2, 8)
        
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.optimizer = CrawlOptimizer()
        
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
        return self.optimizer.analyze_website(url)

    def crawl_with_smart_params(self, 
                               start_urls: List[str],
                               use_smart_params: bool = True,
                               manual_depth: Optional[int] = None,
                               manual_pages: Optional[int] = None,
                               keyword: str = None,
                               progress_callback: Optional[Callable] = None) -> List[Dict]:
        if not start_urls:
            return []
        
        main_url = start_urls[0]
        if use_smart_params:
            recommendations = self.get_smart_recommendations(main_url)
            if progress_callback:
                progress_callback("🧠 智能分析网站...")
                progress_callback(f"📊 网站类型: {recommendations['site_type']}")
                progress_callback(f"📝 描述: {recommendations['description']}")
                progress_callback(f"🎯 推荐深度: {recommendations['recommended_depth']}层")
                progress_callback(f"📄 推荐页数: {recommendations['recommended_pages']}页/层")
                progress_callback(f"📈 预估总页数: {recommendations['estimated_pages']:,}页")
                progress_callback(f"🔍 置信度: {recommendations['confidence']:.1%}")
            
            max_depth = manual_depth or recommendations['recommended_depth']
            max_pages_per_level = manual_pages or recommendations['recommended_pages']
            
            if progress_callback:
                progress_callback(f"⚙️ 最终参数: 深度={max_depth}, 页数={max_pages_per_level}")
        else:
            max_depth = manual_depth or 2
            max_pages_per_level = manual_pages or 20
            
            if progress_callback:
                progress_callback(f"🔧 手动参数: 深度={max_depth}, 页数={max_pages_per_level}")
        
        return self.crawl_with_depth(
            start_urls=start_urls,
            max_depth=max_depth,
            max_pages_per_level=max_pages_per_level,
            keyword=keyword,
            progress_callback=progress_callback
        )
    
    def _fetch_url_thread(self, url: str, timeout=15, keyword: str = None) -> Dict:
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
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else url
                result['title'] = title
                
                is_relevant = True
                if keyword:
                    parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                    core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                    if core_subject not in title.lower():
                        if "about" not in url.lower():
                            is_relevant = False
                
                if is_relevant:
                    for script in soup(["script", "style"]):
                        script.decompose()
                    content = soup.get_text()
                    lines = (line.strip() for line in content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = ' '.join(chunk for chunk in chunks if chunk)
                    result['content'] = content
                else:
                    result['content'] = ""

                base_domain = urlparse(url).netloc
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == base_domain:
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
        
        self._smart_delay(result['response_time'])
        return result
    
    def _smart_delay(self, response_time=None):
        if response_time:
            if response_time < 1.0:
                delay = self.base_delay * 0.5
            elif response_time > 3.0:
                delay = self.base_delay * 2.0
            else:
                delay = self.base_delay
        else:
            delay = self.base_delay
        delay += random.uniform(0, 0.5)
        delay = min(delay, self.max_delay)
        time.sleep(delay)
    
    def crawl_urls_concurrent(self, urls: List[str], 
                            progress_callback: Optional[Callable] = None,
                            max_pages: int = 50,
                            keyword: str = None) -> List[Dict]:
        if not urls:
            return []
        self.stats['start_time'] = time.time()
        results = []
        processed_urls = set()
        urls_to_process = urls[:max_pages]
        
        if self.use_processes:
            if progress_callback and urls_to_process:
                progress_callback(f"🚀 正在启动批次处理 ({len(urls_to_process)} 个链接)...")
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                args_list = []
                for url in urls_to_process:
                    if url not in processed_urls:
                        args_list.append((url, 15, self.user_agents, self.base_delay, self.max_delay, keyword))
                        processed_urls.add(url)
                future_to_url = {executor.submit(fetch_url_worker, args): args[0] for args in args_list}
                completed = 0
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
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
                        error_result = {'url': url, 'success': False, 'content': None, 'title': None, 'links': [], 'response_time': 0, 'error': str(e)}
                        results.append(error_result)
                        completed += 1
                        self.stats['failed_requests'] += 1
                        self.stats['total_requests'] += 1
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {}
                for url in urls_to_process:
                    if url not in processed_urls:
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
                        error_result = {'url': url, 'success': False, 'content': None, 'title': None, 'links': [], 'response_time': 0, 'error': str(e)}
                        results.append(error_result)
                        completed += 1
        return results
    
    def crawl_with_depth(self, start_urls: List[str], 
                        max_depth: int = 2,
                        max_pages_per_level: int = 20,
                        keyword: str = None,
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
        """按深度并发爬取 - 优化种子逻辑"""
        all_results = []
        processed_urls = set()
        if progress_callback:
            progress_callback(f"🚀 开始递归并发爬取: 最大深度={max_depth}, 基础页数={max_pages_per_level}")
            if keyword:
                progress_callback(f"🎯 关键词锚定: {keyword}")

        if len(start_urls) == 1 and not keyword:
            if progress_callback: progress_callback(f"🌱 处理种子页面: {start_urls[0]}")
            seed_results = self.crawl_urls_concurrent(start_urls, progress_callback, 1, keyword)
            all_results.extend(seed_results)
            processed_urls.update(start_urls)
            next_urls = []
            for r in seed_results:
                if r['success'] and r['links']:
                    next_urls.extend(r['links'])
            current_urls = list(set(next_urls) - processed_urls)
        else:
            current_urls = start_urls

        for depth in range(1, max_depth + 1):
            if not current_urls:
                break
            target_success_count = max_pages_per_level ** depth
            level_candidates = [url for url in current_urls if url not in processed_urls]
            if not level_candidates:
                if progress_callback: progress_callback(f"⚠️ 第{depth}层: 无新链接可处理")
                break
            if progress_callback:
                progress_callback(f"📂 第{depth}层开始: 候选 {len(level_candidates)} 个, 目标有效抓取 {target_success_count} 个")
            level_results = []
            layer_success_count = 0
            batch_start = 0
            while layer_success_count < target_success_count and batch_start < len(level_candidates):
                needed = target_success_count - layer_success_count
                batch_size = min(int(needed * 1.5) + 1, 50)
                batch_end = min(batch_start + batch_size, len(level_candidates))
                batch_urls = level_candidates[batch_start:batch_end]
                if not batch_urls: break
                batch_results = self.crawl_urls_concurrent(batch_urls, progress_callback, len(batch_urls), keyword=keyword)
                level_results.extend(batch_results)
                processed_urls.update(batch_urls)
                batch_success = sum(1 for r in batch_results if r['success'] and r.get('content'))
                layer_success_count += batch_success
                batch_start = batch_end
            all_results.extend(level_results)
            next_layer_urls = []
            for result in level_results:
                if result['success'] and result['links']:
                    next_layer_urls.extend(result['links'])
            current_urls = list(set(next_layer_urls) - processed_urls)
            if progress_callback:
                progress_callback(f"🎯 第{depth}层完成: 最终有效 {layer_success_count} 页")
        return all_results
    
    def get_stats(self) -> Dict:
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
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'response_times': []
        }

if __name__ == "__main__":
    pass
