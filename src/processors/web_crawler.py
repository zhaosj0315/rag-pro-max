import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import hashlib
import re
import fnmatch
from typing import List, Optional, Callable

class WebCrawler:
    def __init__(self, output_dir="temp_uploads/web_crawl"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.visited_urls = set()
        self.failed_urls = set()
        self.retry_counts = {}
        
        # 创建会话，增强反爬处理
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        })
        
        # 设置重试策略
        try:
            from urllib3.util.retry import Retry
            from requests.adapters import HTTPAdapter
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        except ImportError:
            pass  # 如果没有urllib3，使用基本重试
        
        # 反爬处理配置
        self.anti_bot_config = {
            'min_delay': 0.5,      # 最小延迟
            'max_delay': 2.0,      # 最大延迟
            'retry_delay': 5.0,    # 重试延迟
            'max_retries': 3,      # 最大重试次数
            'timeout': 15,         # 请求超时
        }

    def _is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    
    
    def _smart_request(self, url: str, status_callback=None) -> requests.Response:
        """智能请求，处理反爬机制"""
        import random
        
        # 检查是否已经失败过多次
        if url in self.failed_urls:
            raise Exception(f"URL已被标记为失败: {url}")
        
        retry_count = self.retry_counts.get(url, 0)
        if retry_count >= self.anti_bot_config['max_retries']:
            self.failed_urls.add(url)
            raise Exception(f"重试次数超限: {url}")
        
        try:
            # 随机延迟，模拟人类行为
            delay = random.uniform(
                self.anti_bot_config['min_delay'], 
                self.anti_bot_config['max_delay']
            )
            time.sleep(delay)
            
            # 随机化User-Agent
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
            ]
            
            headers = self.session.headers.copy()
            headers['User-Agent'] = random.choice(user_agents)
            
            # 添加Referer（如果有的话）
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            
            response = self.session.get(
                url, 
                headers=headers,
                timeout=self.anti_bot_config['timeout'],
                allow_redirects=True
            )
            
            # 检查响应状态
            if response.status_code == 403:
                raise Exception(f"访问被拒绝 (403): {url}")
            elif response.status_code == 429:
                # 速率限制，增加延迟后重试
                if status_callback:
                    status_callback(f"遇到速率限制，等待 {self.anti_bot_config['retry_delay']} 秒后重试")
                time.sleep(self.anti_bot_config['retry_delay'])
                raise Exception(f"速率限制 (429): {url}")
            elif response.status_code >= 400:
                raise Exception(f"HTTP错误 ({response.status_code}): {url}")
            
            # 重置重试计数
            if url in self.retry_counts:
                del self.retry_counts[url]
            
            return response
            
        except Exception as e:
            # 增加重试计数
            self.retry_counts[url] = retry_count + 1
            
            # 如果是可重试的错误，抛出异常让上层处理
            if "429" in str(e) or "timeout" in str(e).lower():
                if retry_count < self.anti_bot_config['max_retries'] - 1:
                    if status_callback:
                        status_callback(f"请求失败，准备重试 ({retry_count + 1}/{self.anti_bot_config['max_retries']}): {e}")
                    time.sleep(self.anti_bot_config['retry_delay'])
            
            raise e

    def _fix_url(self, url):
        """自动修复URL格式，添加协议前缀"""
        if not url:
            return ""
        
        url = url.strip()
        
        # 如果已经有协议，直接返回
        if url.startswith(('http://', 'https://')):
            return url
        
        # 如果是常见域名格式，自动添加https://
        import re
        if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
            return f"https://{url}"
        
        return url

    def _should_exclude_url(self, url: str, exclude_patterns: List[str]) -> bool:
        """检查URL是否应该被排除"""
        if not exclude_patterns:
            return False
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(url, pattern) or fnmatch.fnmatch(url.lower(), pattern.lower()):
                return True
        return False

    def _extract_links(self, soup, base_url: str, exclude_patterns: List[str] = None) -> List[str]:
        """提取页面中的所有链接"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
            
            # 构建完整URL
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # 判断是否允许外部链接
            is_search_engine = any(se in base_domain for se in [
                'google.com', 'bing.com', 'baidu.com', 'yahoo.com', 
                'duckduckgo.com', 'sogou.com', 'so.com', 'zhihu.com'
            ])
            
            # 如果不是搜索引擎，则只处理同域名链接
            if not is_search_engine and parsed_url.netloc != base_domain:
                continue
            
            # 移除fragment
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            if parsed_url.query:
                clean_url += f"?{parsed_url.query}"
            
            # 检查排除模式
            if self._should_exclude_url(clean_url, exclude_patterns or []):
                continue
            
            # 过滤常见的非内容链接
            skip_patterns = [
                r'\.(?:jpg|jpeg|png|gif|pdf|zip|exe|dmg)$',
                r'#',
                r'javascript:',
                r'mailto:',
                r'/search\?',
                r'/login',
                r'/register',
                r'/logout'
            ]
            
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, clean_url, re.IGNORECASE):
                    should_skip = True
                    break
            
            if not should_skip and clean_url not in links:
                links.append(clean_url)
        
        return links

    def _clean_text(self, text):
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _save_content(self, url, title, content):
        if not content or len(content.strip()) < 50:  # 内容太少则跳过
            return None
            
        # 生成文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', title)[:50]
        filename = f"{safe_title}_{url_hash}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        # 添加元数据头
        file_content = f"URL: {url}\nTitle: {title}\nCrawl Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        return filepath

    def crawl_advanced(self, 
                      start_url: str, 
                      max_depth: int = 1, 
                      max_pages: int = 10,
                      exclude_patterns: List[str] = None,
                      parser_type: str = "default",
                      status_callback: Optional[Callable] = None) -> List[str]:
        """
        高级递归爬取网页
        
        Args:
            start_url: 起始URL
            max_depth: 最大深度 (1-5)
            max_pages: 每层最大页面数量
            exclude_patterns: 排除链接模式列表（支持通配符）
            parser_type: 页面解析器类型 ("default", "article", "documentation")
            status_callback: 状态回调函数 func(msg)
        
        Returns:
            list: 已保存的文件路径列表
        """
        # 🛑 安全熔断：全局最大页面限制
        GLOBAL_MAX_PAGES = 50000
        total_estimated = max_pages ** max_depth
        if total_estimated > GLOBAL_MAX_PAGES:
            if status_callback:
                status_callback(f"⚠️ 安全熔断：预估页面数 {total_estimated} 超过限制 {GLOBAL_MAX_PAGES}")
            max_pages = min(max_pages, int(GLOBAL_MAX_PAGES ** (1/max_depth)))
        
        # 自动修复URL格式
        start_url = self._fix_url(start_url)
        
        if not self._is_valid_url(start_url):
            raise ValueError(f"Invalid URL '{start_url}': No scheme supplied. Perhaps you meant https://{start_url.replace('https://', '').replace('http://', '')}?")
        
        self.visited_urls = set()
        # 按层级组织队列: {depth: [urls]}
        current_level = [start_url]
        saved_files = []
        total_count = 0
        
        base_domain = urlparse(start_url).netloc
        
        if status_callback:
            status_callback(f"开始爬取: {start_url} (最大深度: {max_depth}, 每层最大页数: {max_pages})")
        
        for depth in range(1, max_depth + 1):
            if not current_level:
                break
                
            next_level = []
            level_count = 0
            
            # 限制当前层的页面数
            current_level = current_level[:max_pages]
            
            if status_callback:
                status_callback(f"📂 第{depth}层开始: 准备处理 {len(current_level)} 个链接")
            
            for url in current_level:
                if url in self.visited_urls or level_count >= max_pages:
                    continue
                
                self.visited_urls.add(url)
                
                try:
                    if status_callback:
                        status_callback(f"正在抓取 ({total_count+1}) 第{depth}层 ({level_count+1}/{max_pages}): {url}")
                    
                    # 使用智能请求方法
                    response = self._smart_request(url, status_callback)
                    response.encoding = response.apparent_encoding
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 根据解析器类型提取内容
                    content = self._extract_content_by_parser(soup, parser_type)
                    
                    title = soup.title.string if soup.title else "No Title"
                    title = self._clean_text(title)
                    
                    # 保存内容
                    filepath = self._save_content(url, title, content)
                    if filepath:
                        saved_files.append(filepath)
                        level_count += 1
                        total_count += 1
                        if status_callback:
                            status_callback(f"✅ 已保存: {title} ({len(content)} 字符)")
                    
                    # 如果还没达到最大深度，提取下一级链接
                    if depth < max_depth:
                        links = self._extract_links(soup, url, exclude_patterns)
                        next_level.extend(links)
                        
                        if status_callback and links:
                            status_callback(f"发现 {len(links)} 个新链接，添加到第{depth+1}层队列")
                    
                    time.sleep(0.5)  # 礼貌爬取
                    
                except Exception as e:
                    if status_callback:
                        status_callback(f"抓取失败 {url}: {e}")
                    continue
            
            # 准备下一层
            current_level = list(set(next_level))  # 去重
            
            if status_callback:
                status_callback(f"🎯 第{depth}层完成: 成功抓取 {level_count} 页，发现 {len(current_level)} 个下级链接")
        
        if status_callback:
            status_callback(f"🎉 爬取完成！总共获取 {len(saved_files)} 个页面 (共{max_depth}层)")
                
        return saved_files

    def _extract_content_by_parser(self, soup, parser_type: str) -> str:
        """根据解析器类型提取内容"""
        
        # 移除不需要的标签
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        if parser_type == "article":
            # 文章模式：优先提取article、main、content等标签
            content_selectors = [
                'article', 'main', '[role="main"]', 
                '.content', '.post-content', '.article-content',
                '.entry-content', '.post-body'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    text = elements[0].get_text()
                    clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
                    if len(clean_text) > 100:
                        return clean_text
        
        elif parser_type == "documentation":
            # 文档模式：提取文档特定的内容区域
            doc_selectors = [
                '.documentation', '.docs-content', '.doc-content',
                '.markdown-body', '.rst-content', '.wiki-content',
                '#content', '.main-content'
            ]
            
            for selector in doc_selectors:
                elements = soup.select(selector)
                if elements:
                    text = elements[0].get_text()
                    clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
                    if len(clean_text) > 100:
                        return clean_text
        
        # 默认模式：提取所有文本
        text = soup.get_text()
        clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
        return clean_text

    def crawl(self, start_url, max_depth=1, max_pages=10, status_callback=None):
        """保持向后兼容的简单接口"""
        return self.crawl_advanced(
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
            status_callback=status_callback
        )
