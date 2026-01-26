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

def extract_real_url(url: str) -> str:
    """[v9.5.32] 从搜索引擎跳转链接中提取真实目标 URL"""
    from urllib.parse import urlparse, parse_qs, unquote
    try:
        parsed = urlparse(url)
        # 1. DuckDuckGo: uddg=...
        if "duckduckgo.com" in parsed.netloc:
            qs = parse_qs(parsed.query)
            if 'uddg' in qs: return unquote(qs['uddg'][0])
        # 2. Bing: u=... (Base64 or URL)
        elif "bing.com" in parsed.netloc:
            qs = parse_qs(parsed.query)
            if 'u' in qs:
                u_val = qs['u'][0]
                if u_val.startswith('a1'): # Bing 特有的 base64 包装
                    import base64
                    try: 
                        # 尝试解码 Bing 的 a1 包装
                        decoded = base64.b64decode(u_val[2:] + "==").decode('utf-8', errors='ignore')
                        if decoded.startswith('http'): return decoded
                    except: pass
                return unquote(u_val)
        # 3. Google: url=...
        elif "google." in parsed.netloc:
            qs = parse_qs(parsed.query)
            if 'url' in qs: return unquote(qs['url'][0])
    except: pass
    return url

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
    
    # [v9.5.32] 预处理：如果是跳转链接，先解壳
    real_url = extract_real_url(url)
    result['url'] = real_url
    
    try:
        # 创建新的session
        session = requests.Session()
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        response = session.get(real_url, headers=headers, timeout=timeout)
        response_time = time.time() - start_time
        result['response_time'] = response_time
        
        # [v9.5.31] 核心修复：使用跳转后的最终 URL 进行判定
        final_url = response.url
        parsed_current = urlparse(final_url)
        base_domain = parsed_current.netloc.lower()
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else final_url
            result['title'] = title
            
            # 只有当最终 URL 仍然是搜索引擎时，才判定为入口页
            is_entry_point = (
                "search" in final_url.lower() or 
                "bing.com" in base_domain or
                "duckduckgo.com" in base_domain or
                "google." in base_domain
            )
            
            is_relevant = True
            if keyword:
                # [v9.5.32] 增强型相关性：支持中英双语匹配
                parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                
                # 如果搜索的是中文字符，自动添加对应的英文通用词（启发式）
                english_terms = []
                if re.search(r'[\u4e00-\u9fff]', keyword):
                    if "数据分析" in keyword: english_terms = ["data analy", "analytics"]
                    elif "架构" in keyword: english_terms = ["architecture"]
                
                if not is_entry_point:
                    content_snippet = str(response.content).lower()
                    # 只要满足：中文关键词命中 OR 英文对应词命中，即视为相关
                    found_match = (core_subject in title.lower() or core_subject in content_snippet)
                    if not found_match and english_terms:
                        found_match = any(et in title.lower() or et in content_snippet for et in english_terms)
                    
                    if not found_match:
                         is_relevant = False
            
            if is_relevant:
                # [v9.5.29] 清洗降级：仅删除绝对干扰项
                for script in soup(["script", "style"]):
                    script.decompose()
                content = soup.get_text()
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                # 入口页（搜索结果页）本身不作为文档保存
                if is_entry_point:
                    result['content'] = "" 
                else:
                    result['content'] = content
            else:
                result['content'] = "" 
            
            # 提取链接
            extracted_links = []
            
            # [v9.5.27] 增强型搜索结果提取 (优先尝试高准确率选择器)
            # 1. Bing 搜索结果
            bing_links = soup.select('li.b_algo h2 a') or soup.select('a[href*="/ck/a"]')
            if bing_links:
                for link in bing_links:
                    href = link.get('href')
                    if href: extracted_links.append(urljoin(url, href))
                        
            # 2. DuckDuckGo (HTML) 结果
            ddg_links = soup.select('.result__a') or soup.select('a[href*="/l/?uddg="]')
            if ddg_links:
                for link in ddg_links:
                    href = link.get('href')
                    if href: extracted_links.append(urljoin(url, href))
            
            # 3. 百度/知乎/通用搜索引擎
            general_search_links = soup.select('.result-title a') + soup.select('.ContentItem-title a')
            for link in general_search_links:
                href = link.get('href')
                if href: extracted_links.append(urljoin(url, href))

            # 4. 通用保底提取 (所有 a 标签)
            for link in soup.find_all('a', href=True):
                extracted_links.append(urljoin(url, href := link.get('href')))
            
            # [v9.5.35] 暴力保底提取：针对 WAF 混淆，使用正则直接从 HTML 文本中捞取 http 链接
            if is_entry_point and not extracted_links:
                import re
                found_http = re.findall(r'https?://[^\s"\'<>)]+', str(response.content))
                for raw_url in found_http:
                    extracted_links.append(raw_url)

            unique_links = list(set(extracted_links))
            
            # --- 核心过滤算法 [v9.5.30 重构] ---
            for full_url in unique_links:
                parsed = urlparse(full_url)
                if not parsed.netloc: continue
                
                allow_link = False
                is_redirect = False
                
                # A. 检查是否为已知的搜索引擎跳转模式
                redirect_patterns = ["bing.com/ck/a", "duckduckgo.com/l/", "google.com/url"]
                if any(p in full_url.lower() for p in redirect_patterns):
                    allow_link = True
                    is_redirect = True
                
                # B. 核心策略：如果是搜索页，放行所有第三方域名
                if is_entry_point:
                    if parsed.netloc.lower() != base_domain:
                        # 排除搜索引擎自身的其它服务
                        if not any(x in full_url.lower() for x in ['microsoft.com', 'google.com', 'apple.com', 'bing.com/images', 'duckduckgo.com/about']):
                            allow_link = True
                else:
                    # 正常文档页，允许同域名下钻或已知白名单
                    if parsed.netloc.lower() == base_domain:
                        allow_link = True
                    elif any(x in parsed.netloc.lower() for x in ['zhihu.com', 'baidu.com', 'wikipedia.org', 'github.com']):
                        allow_link = True
                
                if allow_link:
                    should_add = True
                    # 关键词相关性校验 (探测出的种子链接免检)
                    if keyword and not is_entry_point and not is_redirect: 
                        link_path = parsed.path.lower()
                        parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                        core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                        
                        is_content_url = any(x in full_url for x in ["/question/", "/article/", "/item/", "/wiki/", "/p/"])
                        if core_subject not in link_path and not is_content_url:
                             should_add = False
                        
                        if any(x in link_path for x in ['login', 'signup', 'register', 'cart', 'search']):
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
        
        # [v9.5.33] 增加更现代化的 UA 池，规避 WAF
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
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
        
        # [v9.5.32] 预处理：如果是跳转链接，先解壳
        real_url = extract_real_url(url)
        result['url'] = real_url

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
            
            response = self.session.get(real_url, headers=headers, timeout=timeout)
            response_time = time.time() - start_time
            result['response_time'] = response_time
            self.stats['response_times'].append(response_time)
            
            # [v9.5.31] 核心修复：使用最终 URL 判定
            final_url = response.url
            parsed_current = urlparse(final_url)
            base_domain = parsed_current.netloc.lower()

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else final_url
                result['title'] = title
                
                is_entry_point = (
                    "search" in final_url.lower() or 
                    "bing.com" in base_domain or
                    "duckduckgo.com" in base_domain or
                    "google." in base_domain
                )
                
                is_relevant = True
                if keyword:
                    # [v9.5.32] 增强型相关性：支持中英双语匹配
                    parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
                    core_subject = max(parts, key=len).lower() if parts else keyword.lower()
                    
                    english_terms = []
                    if re.search(r'[\u4e00-\u9fff]', keyword):
                        if "数据分析" in keyword: english_terms = ["data analy", "analytics"]
                        elif "架构" in keyword: english_terms = ["architecture"]
                    
                    if not is_entry_point:
                        content_snippet = str(response.content).lower()
                        found_match = (core_subject in title.lower() or core_subject in content_snippet)
                        if not found_match and english_terms:
                            found_match = any(et in title.lower() or et in content_snippet for et in english_terms)
                        
                        if not found_match:
                             is_relevant = False
                
                if is_relevant:
                    # [v9.5.29] 清洗降级
                    for script in soup(["script", "style"]):
                        script.decompose()
                    content = soup.get_text()
                    lines = (line.strip() for line in content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = ' '.join(chunk for chunk in chunks if chunk)
                    
                    result['content'] = "" if is_entry_point else content
                else:
                    result['content'] = ""

                # 提取链接 [v9.5.30]
                extracted_links = []
                # 优先尝试高准确率搜索选择器
                bing_links = soup.select('li.b_algo h2 a') or soup.select('a[href*="/ck/a"]')
                if bing_links:
                    for link in bing_links:
                        href = link.get('href')
                        if href: extracted_links.append(urljoin(url, href))
                            
                ddg_links = soup.select('.result__a') or soup.select('a[href*="/l/?uddg="]')
                if ddg_links:
                    for link in ddg_links:
                        href = link.get('href')
                        if href: extracted_links.append(urljoin(url, href))

                # 通用保底提取
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        extracted_links.append(urljoin(url, href))
                
                # [v9.5.35] 暴力保底提取：针对 WAF 混淆，使用正则直接从 HTML 文本中捞取 http 链接
                if is_entry_point and not extracted_links:
                    import re
                    # 匹配 http(s):// 开头的，且非搜索引擎域名的链接
                    found_http = re.findall(r'https?://[^\s"\'<>)]+', str(response.content))
                    for raw_url in found_http:
                        extracted_links.append(raw_url)
                
                unique_links = list(set(extracted_links))
                
                for full_url in unique_links:
                    parsed = urlparse(full_url)
                    if not parsed.netloc: continue
                    
                    allow_link = False
                    is_redirect = False
                    
                    redirect_patterns = ["bing.com/ck/a", "duckduckgo.com/l/", "google.com/url"]
                    if any(p in full_url.lower() for p in redirect_patterns):
                        allow_link = True
                        is_redirect = True
                    
                    if is_entry_point:
                        if parsed.netloc.lower() != base_domain:
                            if not any(x in full_url.lower() for x in ['microsoft.com', 'google.com', 'apple.com', 'bing.com/images', 'duckduckgo.com/about']):
                                allow_link = True
                    else:
                        if parsed.netloc.lower() == base_domain:
                            allow_link = True
                        elif any(x in parsed.netloc.lower() for x in ['zhihu.com', 'baidu.com', 'wikipedia.org', 'github.com']):
                            allow_link = True
                    
                    if allow_link:
                        should_add = True
                        if keyword and not is_entry_point and not is_redirect:
                            link_text = link.get_text().strip().lower()
                            link_path = parsed.path.lower()
                            
                            is_content_url = any(x in full_url for x in ["/question/", "/article/", "/item/", "/wiki/", "/p/"])
                            if core_subject not in link_text and core_subject not in link_path and not is_content_url:
                                should_add = False
                                    
                            if any(x in link_path for x in ['login', 'signup', 'register', 'cart', 'search']):
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

        # [v9.5.34] 逻辑革命：探测层强制【单线程/同步】以规避 WAF 拦截
        current_urls = []
        
        if keyword and start_urls:
            if progress_callback: progress_callback(f"🔍 [L0] 正在从搜索引擎探测初始链接 (安全模式)...")
            
            # [v9.5.34] 核心修改：不再使用多进程，改用内部线程方法逐个请求
            # 这样可以维持一致的 Session 环境，且不会因瞬间并发被封
            seed_results = []
            for s_url in start_urls:
                res = self._fetch_url_thread(s_url, 15, keyword)
                seed_results.append(res)
            
            processed_urls.update(start_urls)
            
            initial_links = []
            for r in seed_results:
                if r['success'] and r['links']:
                    initial_links.extend(r['links'])
            
            # 去重且清理链接
            current_urls = []
            for link in set(initial_links):
                if link not in processed_urls:
                    current_urls.append(link)
            
            if progress_callback: 
                progress_callback(f"✅ [L0] 探测完成，发现 {len(current_urls)} 个潜在文档链接")
                if current_urls:
                    for i, link in enumerate(current_urls[:3]):
                        progress_callback(f"   📍 目标样例 {i+1}: {link[:80]}...")
            
        elif len(start_urls) == 1 and not keyword:
            # 传统的单种子 URL 模式 (也将种子视为 L0)
            if progress_callback: progress_callback(f"🌱 [L0] 处理种子页面: {start_urls[0]}")
            seed_results = self.crawl_urls_concurrent(start_urls, progress_callback, 1, keyword)
            all_results.extend(seed_results) # 传统的爬虫通常保留种子页
            processed_urls.update(start_urls)
            
            next_urls = []
            for r in seed_results:
                if r['success'] and r['links']:
                    next_urls.extend(r['links'])
            current_urls = list(set(next_urls) - processed_urls)
        else:
            # 基础列表模式
            current_urls = start_urls

        # 正式深度循环 (Level 1 到 Level N)
        for depth in range(1, max_depth + 1):
            if not current_urls:
                break
                
            # 指数级配额: n^depth (即 5, 25, 125...)
            target_success_count = max_pages_per_level ** depth
            level_candidates = [url for url in current_urls if url not in processed_urls]
            
            if not level_candidates:
                if progress_callback: progress_callback(f"⚠️ 第{depth}层: 无新链接可处理")
                break
                
            if progress_callback:
                progress_callback(f"📂 第{depth}层开始: 候选 {len(level_candidates)} 个, 目标抓取 {target_success_count} 页")
            
            level_results = []
            layer_success_count = 0
            batch_start = 0
            
            # 分批处理直到达到本层配额
            while layer_success_count < target_success_count and batch_start < len(level_candidates):
                needed = target_success_count - layer_success_count
                batch_size = min(int(needed * 1.2) + 1, 50)
                batch_end = min(batch_start + batch_size, len(level_candidates))
                batch_urls = level_candidates[batch_start:batch_end]
                
                if not batch_urls: break
                
                # 执行并发抓取
                batch_results = self.crawl_urls_concurrent(batch_urls, progress_callback, len(batch_urls), keyword=keyword)
                
                # 过滤掉内容质量太差或失败的结果
                valid_batch_results = [r for r in batch_results if r['success'] and r.get('content') and len(r['content']) > 100]
                
                level_results.extend(valid_batch_results)
                processed_urls.update(batch_urls)
                layer_success_count += len(valid_batch_results)
                batch_start = batch_end
            
            all_results.extend(level_results)
            
            # 提取下一层候选链接
            if depth < max_depth:
                next_layer_urls = []
                for result in level_results:
                    if result['links']:
                        next_layer_urls.extend(result['links'])
                current_urls = list(set(next_layer_urls) - processed_urls)
            
            if progress_callback:
                progress_callback(f"🎯 第{depth}层完成: 最终捕获 {layer_success_count} 份有效文档")
                
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
