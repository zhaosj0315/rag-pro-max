import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import hashlib
import re
import fnmatch
from typing import List, Optional, Callable, Dict

# 导入智能优化器
from .crawl_optimizer import CrawlOptimizer
from src.utils.file_system_utils import set_where_from_metadata
from src.utils.html_to_markdown import HtmlToMarkdown

class WebCrawler:
    def __init__(self, output_dir="temp_uploads/web_crawl"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.visited_urls = set()
        self.failed_urls = set()
        self.retry_counts = {}
        
        # 🔥 新增：智能优化器
        self.optimizer = CrawlOptimizer()
        
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

    def _fix_url(self, url):
        """自动修复URL格式，添加协议前缀"""
        if not url:
            return ""
        
        url = url.strip()
        
        # 如果已经有协议，直接返回
        if url.startswith(('http://', 'https://')):
            return url
        
        # 如果是常见域名格式，自动添加https://
        if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
            return f"https://{url}"
        
        return url

    def get_smart_recommendations(self, url: str) -> Dict:
        """🔥 新增：获取智能爬取推荐参数"""
        return self.optimizer.analyze_website(url)

    def crawl_with_smart_params(self, 
                               start_url: str,
                               use_smart_params: bool = True,
                               manual_depth: Optional[int] = None,
                               manual_pages: Optional[int] = None,
                               exclude_patterns: List[str] = None,
                               parser_type: str = "default",
                               status_callback: Optional[Callable] = None) -> List[str]:
        """🔥 新增：使用智能参数推荐的爬取方法"""
        
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
            max_pages = manual_pages or recommendations['recommended_pages']
            
            if status_callback:
                status_callback(f"⚙️ 最终参数: 深度={max_depth}, 页数={max_pages}")
        else:
            # 使用手动参数或默认值
            max_depth = manual_depth or 2
            max_pages = manual_pages or 10
            
            if status_callback:
                status_callback(f"🔧 手动参数: 深度={max_depth}, 页数={max_pages}")
        
        # 调用原有的爬取方法
        return self.crawl_advanced(
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
            exclude_patterns=exclude_patterns,
            parser_type=parser_type,
            status_callback=status_callback
        )

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
            if status_callback and delay > 1.0:
                status_callback(f"⏱️ 延迟 {delay:.1f}s (反爬保护)")
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
            
            if retry_count > 0 and status_callback:
                status_callback(f"🔄 重试第 {retry_count} 次: {url}")
            
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

    def _should_exclude_url(self, url: str, exclude_patterns: List[str]) -> bool:
        """检查URL是否应该被排除"""
        if not exclude_patterns:
            return False
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(url, pattern) or fnmatch.fnmatch(url.lower(), pattern.lower()):
                return True
        return False

    def _extract_links(self, soup, base_url: str, exclude_patterns: List[str] = None, keyword: str = None) -> List[str]:
        """提取页面中的所有链接，并根据关键词进行极其严格的语义筛选"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        # --- v5.5.8 核心锚定逻辑 ---
        core_subject = ""
        if keyword:
            # 找到关键词中最长的一个词（通常是主语，如 Google）
            all_parts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', keyword)
            if all_parts:
                core_subject = max(all_parts, key=len).lower()

        # 预先剔除导航栏、侧边栏、页脚，只在正文区找链接
        search_area = soup.find('div', {'id': 'content'}) or soup.find('main') or soup.find('article') or soup
        
        for link in search_area.find_all('a', href=True):
            href = link.get('href')
            link_text = link.get_text().strip().lower()
            if not href:
                continue
            
            # 构建完整URL
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # --- v5.5.8 语义铁闸：核心主语强制校验 ---
            if core_subject:
                # 检查链接文字或URL路径是否包含【核心主语】
                # 如果搜 Google，链接里必须有 google，只有“如何使用”是不够的
                is_core_match = (core_subject in link_text) or (core_subject in parsed_url.path.lower())
                
                # 屏蔽维基百科系统路径
                is_system = any(p in full_url for p in ['Special:', 'Help:', 'File:', 'Category:', 'Talk:', 'Template:', 'Portal:'])
                
                if is_system or not is_core_match:
                    continue
            # ---------------------------------------

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

    def _save_content(self, url, title, content):
        if not content or len(content.strip()) < 50:  # 内容太少则跳过
            return None
            
        # 生成文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', title)[:50]
        filename = f"{safe_title}_{url_hash}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # 添加元数据头
        file_content = f"**URL:** {url}\n\n# {title}\n\n**Crawl Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n**Content:**\n\n{content}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # 为文件设置 macOS 下载来源元数据
        set_where_from_metadata(filepath, url)
        
        return filepath

    def crawl_advanced(self, 
                      start_url: str, 
                      max_depth: int = 1, 
                      max_pages: int = 10,
                      exclude_patterns: List[str] = None,
                      parser_type: str = "default",
                      status_callback: Optional[Callable] = None) -> List[str]:
        """
        高级递归爬取网页 - 优化种子页逻辑，支持 5+25 指数级分布
        """
        # 🛑 安全熔断：全局最大页面限制
        GLOBAL_MAX_PAGES = 50000
        total_estimated = sum([max_pages ** i for i in range(1, max_depth + 1)])
        if total_estimated > GLOBAL_MAX_PAGES:
            if status_callback:
                status_callback(f"⚠️ 安全熔断：预估页面数 {total_estimated} 超过限制 {GLOBAL_MAX_PAGES}")
            # 简化计算一个合理的 max_pages
            max_pages = min(max_pages, int(GLOBAL_MAX_PAGES ** (1/max_depth)))
        
        # 自动修复URL格式
        start_url = self._fix_url(start_url)
        
        self.visited_urls = set()
        saved_files = []
        total_count = 0
        
        if status_callback:
            status_callback(f"🚀 开始网页抓取 (种子页): {start_url}")

        # --- Step 0: 处理种子页面 (不计入 Level 1 配额) ---
        try:
            response = self._smart_request(start_url, status_callback)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string if soup.title else "No Title"
            content = self._extract_content_by_parser(soup, parser_type)
            
            filepath = self._save_content(start_url, title, content)
            if filepath:
                saved_files.append(filepath)
                total_count += 1
            
            self.visited_urls.add(start_url)
            
            # 提取初始链接作为 Level 1 的起点
            current_level = self._extract_links(soup, start_url, exclude_patterns)
        except Exception as e:
            if status_callback:
                status_callback(f"❌ 种子页抓取失败: {e}")
            return []

        # --- Step 1: 开始层级递归 ---
        for depth in range(1, max_depth + 1):
            if not current_level: break
            
            # 每一层的目标抓取数量 (指数级)
            target_layer_count = max_pages ** depth
            next_level_candidates = []
            layer_processed_count = 0
            
            if status_callback:
                status_callback(f"📂 进入第 {depth} 层抓取 (目标: {target_layer_count} 页)")

            # 过滤掉已访问的链接并限制候选数量，避免无效循环
            current_level = [url for url in current_level if url not in self.visited_urls]
            
            for url in current_level:
                if layer_processed_count >= target_layer_count:
                    break
                
                if url in self.visited_urls: continue
                self.visited_urls.add(url)
                
                try:
                    if status_callback:
                        status_callback(f"🔄 抓取 ({total_count+1}) L{depth}: {url}")
                    
                    response = self._smart_request(url, status_callback)
                    response.encoding = response.apparent_encoding
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    title = soup.title.string if soup.title else "No Title"
                    content = self._extract_content_by_parser(soup, parser_type)
                    
                    filepath = self._save_content(url, title, content)
                    if filepath:
                        saved_files.append(filepath)
                        total_count += 1
                        layer_processed_count += 1
                    
                    # 只有在还没到最后一层时才提取链接
                    if depth < max_depth:
                        links = self._extract_links(soup, url, exclude_patterns)
                        next_level_candidates.extend(links)
                    
                    time.sleep(0.5)
                except: continue
                
            # 准备下一层 (去重)
            current_level = list(set(next_level_candidates))
                
        return saved_files

    def _extract_content_by_parser(self, soup, parser_type: str) -> str:
        """根据解析器类型提取内容 (转换为Markdown)"""
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        target_element = None
        if parser_type == "article":
            content_selectors = ['article', 'main', '.content', '.post-content']
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    target_element = elements[0]
                    break
        
        if target_element: return HtmlToMarkdown.convert(str(target_element))
        if soup.body: return HtmlToMarkdown.convert(str(soup.body))
        return HtmlToMarkdown.convert(str(soup))

    def crawl(self, start_url, max_depth=1, max_pages=10, status_callback=None):
        return self.crawl_advanced(start_url, max_depth, max_pages, status_callback=status_callback)
    
    crawl_recursive = crawl_advanced
    crawl_website = crawl_advanced

    