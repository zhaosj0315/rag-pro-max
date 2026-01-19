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

