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

# 🔥 新增：导入智能优化器
from .crawl_optimizer import CrawlOptimizer

def fetch_url_worker(args):
    """多进程工作函数"""
    url, timeout, user_agents, base_delay, max_delay = args
    
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
        # 创建新的session（进程间不共享）
        session = requests.Session()
        
        # 随机User-Agent
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = session.get(url, headers=headers, timeout=timeout)
        response_time = time.time() - start_time
        result['response_time'] = response_time
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title_tag = soup.find('title')
            result['title'] = title_tag.get_text().strip() if title_tag else url
            
            # 提取内容
            for script in soup(["script", "style"]):
                script.decompose()
            
            content = soup.get_text()
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
            
            result['content'] = content
            
            # 提取链接
            base_domain = urlparse(url).netloc
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)
                    if parsed.netloc == base_domain:
                        result['links'].append(full_url)
            
            result['success'] = True
        else:
            result['error'] = f"HTTP {response.status_code}"
            
    except Exception as e:
        result['error'] = str(e)
        result['response_time'] = time.time() - start_time
    
    # 智能延迟
    if result['response_time']:
        if result['response_time'] < 1.0:
            delay = base_delay * 0.5
        elif result['response_time'] > 3.0:
            delay = base_delay * 2.0
        else:
            delay = base_delay
    else:
        delay = base_delay
    
    delay += random.uniform(0, 0.5)
    delay = min(delay, max_delay)
    time.sleep(delay)
    
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
            progress_callback=progress_callback
        )
    
    def _fetch_url_thread(self, url: str, timeout=15) -> Dict:
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
                result['title'] = title_tag.get_text().strip() if title_tag else url
                
                # 提取内容
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content = soup.get_text()
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                result['content'] = content
                
                # 提取链接
                base_domain = urlparse(url).netloc
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == base_domain:
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
                            max_pages: int = 50) -> List[Dict]:
        """并发爬取URL列表"""
        if not urls:
            return []
        
        self.stats['start_time'] = time.time()
        results = []
        processed_urls = set()
        
        urls_to_process = urls[:max_pages]
        
        if self.use_processes:
            # 多进程模式
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # 准备参数
                args_list = []
                for url in urls_to_process:
                    if url not in processed_urls:
                        args_list.append((url, 15, self.user_agents, self.base_delay, self.max_delay))
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
                            progress_callback(f"已完成 {completed}/{len(future_to_url)} 个页面 (进程模式)", progress)
                            
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
                        future = executor.submit(self._fetch_url_thread, url)
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
                            progress_callback(f"已完成 {completed}/{len(future_to_url)} 个页面 (线程模式)", progress)
                            
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
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
        """按深度并发爬取 - 修复递归逻辑"""
        all_results = []
        current_urls = start_urls
        processed_urls = set()
        
        if progress_callback:
            progress_callback(f"🚀 开始递归并发爬取: 最大深度={max_depth}, 基础页数={max_pages_per_level}")
            for d in range(1, max_depth + 1):
                expected_pages = max_pages_per_level ** d
                progress_callback(f"   第{d}层预计: {expected_pages} 页")
        
        for depth in range(1, max_depth + 1):
            if not current_urls:
                break
            
            # 🔥 关键修复：每层的页面数量应该是 max_pages_per_level^depth
            current_layer_limit = max_pages_per_level ** depth
            
            # 限制当前层处理的URL数量
            current_urls = current_urls[:current_layer_limit]
                
            if progress_callback:
                mode_str = "进程" if self.use_processes else "线程"
                progress_callback(f"📂 第{depth}层开始: 处理 {len(current_urls)} 个链接 (限制: {current_layer_limit}, {mode_str}模式)")
            
            level_urls = [url for url in current_urls 
                         if url not in processed_urls]
            
            if not level_urls:
                if progress_callback:
                    progress_callback(f"⚠️ 第{depth}层: 无新链接可处理，爬取结束")
                break
            
            level_results = self.crawl_urls_concurrent(
                level_urls, 
                progress_callback,
                len(level_urls)  # 处理所有当前层的URL
            )
            
            all_results.extend(level_results)
            processed_urls.update(level_urls)
            
            # 收集下一层URL - 🔥 关键修复：收集所有有效链接，不限制数量
            next_urls = []
            for result in level_results:
                if result['success'] and result['links']:
                    next_urls.extend(result['links'])
            
            current_urls = list(set(next_urls) - processed_urls)
            
            if progress_callback:
                success_count = len([r for r in level_results if r['success']])
                progress_callback(f"🎯 第{depth}层完成: 成功 {success_count} 页，发现 {len(current_urls)} 个下级链接")
                if depth < max_depth and current_urls:
                    next_layer_limit = max_pages_per_level ** (depth + 1)
                    actual_next = min(len(current_urls), next_layer_limit)
                    progress_callback(f"📊 递归统计: 第{depth+1}层将处理前 {actual_next} 个链接")
                success_count = sum(1 for r in level_results if r['success'])
                progress_callback(f"第{depth+1}层完成: 成功 {success_count}/{len(level_results)} 页，发现 {len(current_urls)} 个新链接")
        
        return all_results
    
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

# 使用示例
if __name__ == "__main__":
    print("🧪 测试多进程 vs 多线程爬取性能...")
    
    test_urls = [
        "https://www.runoob.com/",
        "https://docs.python.org/zh-cn/3/",
        "https://help.aliyun.com/"
    ]
    
    def progress_callback(message, progress=None):
        if progress:
            print(f"{message} ({progress:.1%})")
        else:
            print(message)
    
    # 测试多进程模式
    print("\n🔄 测试多进程模式:")
    process_crawler = ConcurrentCrawler(max_workers=3, use_processes=True)
    start_time = time.time()
    process_results = process_crawler.crawl_urls_concurrent(test_urls, progress_callback)
    process_time = time.time() - start_time
    process_stats = process_crawler.get_stats()
    
    print(f"进程模式结果: {len(process_results)}个页面, 耗时: {process_time:.2f}秒")
    print(f"成功率: {process_stats['success_rate']:.1%}, 速度: {process_stats['pages_per_minute']:.1f}页/分钟")
    
    # 测试多线程模式
    print("\n🧵 测试多线程模式:")
    thread_crawler = ConcurrentCrawler(max_workers=3, use_processes=False)
    start_time = time.time()
    thread_results = thread_crawler.crawl_urls_concurrent(test_urls, progress_callback)
    thread_time = time.time() - start_time
    thread_stats = thread_crawler.get_stats()
    
    print(f"线程模式结果: {len(thread_results)}个页面, 耗时: {thread_time:.2f}秒")
    print(f"成功率: {thread_stats['success_rate']:.1%}, 速度: {thread_stats['pages_per_minute']:.1f}页/分钟")
    
    # 性能对比
    print(f"\n📊 性能对比:")
    print(f"进程模式: {process_time:.2f}秒, {process_stats['pages_per_minute']:.1f}页/分钟")
    print(f"线程模式: {thread_time:.2f}秒, {thread_stats['pages_per_minute']:.1f}页/分钟")
    
    if process_time < thread_time:
        improvement = ((thread_time - process_time) / thread_time) * 100
        print(f"🚀 进程模式快 {improvement:.1f}%")
    else:
        improvement = ((process_time - thread_time) / process_time) * 100
        print(f"🧵 线程模式快 {improvement:.1f}%")
        
    def _get_random_headers(self):
        """获取随机请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
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
    
    def _fetch_url(self, url: str, timeout=15) -> Dict:
        """获取单个URL"""
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
            
            headers = self._get_random_headers()
            response = self.session.get(url, headers=headers, timeout=timeout)
            response_time = time.time() - start_time
            result['response_time'] = response_time
            self.stats['response_times'].append(response_time)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 提取标题
                title_tag = soup.find('title')
                result['title'] = title_tag.get_text().strip() if title_tag else url
                
                # 提取内容
                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 提取主要内容
                content = soup.get_text()
                # 清理空白
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                result['content'] = content
                
                # 提取链接
                base_domain = urlparse(url).netloc
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == base_domain:  # 只保留同域名链接
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
    
    def crawl_urls_concurrent(self, urls: List[str], 
                            progress_callback: Optional[Callable] = None,
                            max_pages: int = 50) -> List[Dict]:
        """并发爬取URL列表"""
        if not urls:
            return []
        
        self.stats['start_time'] = time.time()
        results = []
        processed_urls = set()
        
        # 限制爬取数量
        urls_to_process = urls[:max_pages]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_url = {}
            for url in urls_to_process:
                if url not in processed_urls:
                    future = executor.submit(self._fetch_url, url)
                    future_to_url[future] = url
                    processed_urls.add(url)
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress = completed / len(future_to_url)
                        progress_callback(f"已完成 {completed}/{len(future_to_url)} 个页面", progress)
                        
                except Exception as e:
                    # 处理异常
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
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
        """按深度并发爬取 - 修复递归逻辑"""
        all_results = []
        current_urls = start_urls
        processed_urls = set()
        
        if progress_callback:
            progress_callback(f"🚀 开始递归并发爬取: 最大深度={max_depth}, 基础页数={max_pages_per_level}")
            for d in range(1, max_depth + 1):
                expected_pages = max_pages_per_level ** d
                progress_callback(f"   第{d}层预计: {expected_pages} 页")
        
        for depth in range(1, max_depth + 1):
            if not current_urls:
                break
            
            # 🔥 关键修复：每层的页面数量应该是 max_pages_per_level^depth
            current_layer_limit = max_pages_per_level ** depth
            
            # 限制当前层处理的URL数量
            current_urls = current_urls[:current_layer_limit]
                
            if progress_callback:
                progress_callback(f"📂 第{depth}层开始: 处理 {len(current_urls)} 个链接 (限制: {current_layer_limit})")
            
            # 限制每层的URL数量
            level_urls = [url for url in current_urls 
                         if url not in processed_urls]
            
            if not level_urls:
                if progress_callback:
                    progress_callback(f"⚠️ 第{depth}层: 无新链接可处理，爬取结束")
                break
            
            # 并发爬取当前层
            level_results = self.crawl_urls_concurrent(
                level_urls, 
                progress_callback,
                len(level_urls)  # 处理所有当前层的URL
            )
            
            all_results.extend(level_results)
            processed_urls.update(level_urls)
            
            # 收集下一层的URL - 🔥 关键修复：收集所有有效链接，不限制数量
            next_urls = []
            for result in level_results:
                if result['success'] and result['links']:
                    next_urls.extend(result['links'])
            
            # 去重并准备下一层
            current_urls = list(set(next_urls) - processed_urls)
            
            if progress_callback:
                success_count = sum(1 for r in level_results if r['success'])
                progress_callback(f"🎯 第{depth}层完成: 成功 {success_count}/{len(level_results)} 页，发现 {len(current_urls)} 个新链接")
                if depth < max_depth and current_urls:
                    next_layer_limit = max_pages_per_level ** (depth + 1)
                    actual_next = min(len(current_urls), next_layer_limit)
                    progress_callback(f"📊 递归统计: 第{depth+1}层将处理前 {actual_next} 个链接")
        
        return all_results
    
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
            'max_workers': self.max_workers
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

# 使用示例
if __name__ == "__main__":
    crawler = ConcurrentCrawler(max_workers=3)
    
    def progress_callback(message, progress=None):
        if progress:
            print(f"{message} ({progress:.1%})")
        else:
            print(message)
    
    # 测试并发爬取
    test_urls = [
        "https://www.runoob.com/",
        "https://docs.python.org/zh-cn/3/",
        "https://help.aliyun.com/"
    ]
    
    results = crawler.crawl_with_depth(
        test_urls, 
        max_depth=2, 
        max_pages_per_level=5,
        progress_callback=progress_callback
    )
    
    # 显示统计信息
    stats = crawler.get_stats()
    print(f"\n统计信息:")
    print(f"总请求: {stats['total_requests']}")
    print(f"成功: {stats['successful_requests']}")
    print(f"失败: {stats['failed_requests']}")
    print(f"成功率: {stats['success_rate']:.1%}")
    print(f"平均响应时间: {stats['avg_response_time']:.2f}秒")
    print(f"爬取速度: {stats['pages_per_minute']:.1f}页/分钟")
