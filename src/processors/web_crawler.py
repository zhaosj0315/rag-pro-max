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
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"'
        })

    def _is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    
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
            max_pages: 最大页面数量限制
            exclude_patterns: 排除链接模式列表（支持通配符）
            parser_type: 页面解析器类型 ("default", "article", "documentation")
            status_callback: 状态回调函数 func(msg)
        
        Returns:
            list: 已保存的文件路径列表
        """
        # 自动修复URL格式
        start_url = self._fix_url(start_url)
        
        if not self._is_valid_url(start_url):
            raise ValueError(f"Invalid URL '{start_url}': No scheme supplied. Perhaps you meant https://{start_url.replace('https://', '').replace('http://', '')}?")
        
        self.visited_urls = set()
        # 使用队列存储 (url, depth, parent_url)
        queue = [(start_url, 1, None)]
        saved_files = []
        count = 0
        
        base_domain = urlparse(start_url).netloc
        
        if status_callback:
            status_callback(f"开始爬取: {start_url} (最大深度: {max_depth}, 最大页数: {max_pages})")
        
        while queue and count < max_pages:
            url, depth, parent_url = queue.pop(0)
            
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            try:
                if status_callback:
                    status_callback(f"正在抓取 ({count+1}/{max_pages}) 深度{depth}: {url}")
                
                response = self.session.get(url, timeout=15)
                response.encoding = response.apparent_encoding
                
                if response.status_code != 200:
                    if status_callback:
                        status_callback(f"跳过 {url} (状态码: {response.status_code})")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 根据解析器类型提取内容
                content = self._extract_content_by_parser(soup, parser_type)
                
                title = soup.title.string if soup.title else "No Title"
                title = self._clean_text(title)
                
                # 保存内容
                filepath = self._save_content(url, title, content)
                if filepath:
                    saved_files.append(filepath)
                    count += 1
                    if status_callback:
                        status_callback(f"✅ 已保存: {title} ({len(content)} 字符)")
                
                # 如果还没达到最大深度，提取下一级链接
                if depth < max_depth:
                    links = self._extract_links(soup, url, exclude_patterns)
                    
                    # 限制每页提取的链接数量，避免爆炸式增长
                    max_links_per_page = min(20, max_pages - count)
                    links = links[:max_links_per_page]
                    
                    for link in links:
                        if link not in self.visited_urls and (link, depth + 1, url) not in queue:
                            queue.append((link, depth + 1, url))
                    
                    if status_callback and links:
                        status_callback(f"发现 {len(links)} 个新链接，添加到队列")
                
                time.sleep(0.5)  # 礼貌爬取
                
            except Exception as e:
                if status_callback:
                    status_callback(f"抓取失败 {url}: {e}")
                continue
        
        if status_callback:
            status_callback(f"🎉 爬取完成！共获取 {len(saved_files)} 个页面")
                
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
