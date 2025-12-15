#!/usr/bin/env python3
"""
阿里云文档增强爬虫 - 专门优化
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import hashlib
import re
from typing import List, Set

class EnhancedAliyunCrawler:
    """增强的阿里云文档爬虫"""
    
    def __init__(self, output_dir="temp_aliyun_crawl"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        self.visited_urls: Set[str] = set()
        self.saved_files: List[str] = []
    
    def extract_aliyun_links(self, soup, base_url: str) -> List[str]:
        """专门提取阿里云文档链接"""
        links = set()
        base_domain = urlparse(base_url).netloc
        
        # 阿里云特定的链接选择器
        selectors = [
            'a[href*="/zh/"]',           # 中文文档链接
            'a[href*="/product/"]',      # 产品文档链接
            'a[href*="/help/"]',         # 帮助文档链接
            'a[href*="help.aliyun.com"]', # 帮助中心链接
            '.product-item a',           # 产品项目链接
            '.doc-item a',               # 文档项目链接
            '.category-item a',          # 分类项目链接
            'nav a',                     # 导航链接
            '.menu a',                   # 菜单链接
            '.sidebar a',                # 侧边栏链接
            '.content a',                # 内容区链接
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if not href:
                        continue
                    
                    # 构建完整URL
                    full_url = urljoin(base_url, href)
                    parsed = urlparse(full_url)
                    
                    # 只处理阿里云域名
                    if parsed.netloc not in ['help.aliyun.com', 'www.aliyun.com']:
                        continue
                    
                    # 清理URL
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        # 保留重要参数
                        if any(param in parsed.query for param in ['id', 'product', 'category']):
                            clean_url += f"?{parsed.query}"
                    
                    # 过滤有用的链接
                    if self.is_useful_aliyun_link(clean_url, element):
                        links.add(clean_url)
            except Exception as e:
                continue
        
        # 额外查找：通过JavaScript或数据属性
        try:
            # 查找data-*属性中的链接
            for element in soup.find_all(attrs={'data-url': True}):
                url = element.get('data-url')
                if url and 'help.aliyun.com' in url:
                    links.add(url)
            
            # 查找script标签中的URL
            for script in soup.find_all('script'):
                if script.string:
                    urls = re.findall(r'["\']https://help\.aliyun\.com[^"\']*["\']', script.string)
                    for url in urls:
                        clean_url = url.strip('"\'')
                        if self.is_useful_aliyun_link(clean_url):
                            links.add(clean_url)
        except Exception:
            pass
        
        return list(links)
    
    def is_useful_aliyun_link(self, url: str, element=None) -> bool:
        """判断是否为有用的阿里云链接"""
        url_lower = url.lower()
        
        # 排除无用链接
        exclude_patterns = [
            r'\.(?:jpg|jpeg|png|gif|css|js|ico)$',
            r'/(?:login|logout|register|signin|signup)',
            r'/(?:cart|order|payment|billing)',
            r'#$',
            r'javascript:',
            r'mailto:',
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, url_lower):
                return False
        
        # 优先包含的模式
        include_patterns = [
            r'/zh/',           # 中文文档
            r'/product/',      # 产品文档
            r'/help/',         # 帮助文档
            r'\.html$',        # HTML页面
        ]
        
        # 如果匹配包含模式，直接返回True
        for pattern in include_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # 检查链接文本
        if element:
            text = element.get_text(strip=True)
            if len(text) > 0 and len(text) < 100:  # 合理的链接文本长度
                return True
        
        return False
    
    def crawl_page(self, url: str) -> bool:
        """爬取单个页面"""
        if url in self.visited_urls:
            return False
        
        try:
            print(f"  正在抓取: {url}")
            
            response = self.session.get(url, timeout=15)
            response.encoding = response.apparent_encoding
            
            if response.status_code != 200:
                print(f"    跳过 (状态码: {response.status_code})")
                return False
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = "未知页面"
            if soup.title:
                title = soup.title.get_text(strip=True)
            
            # 提取内容
            content = self.extract_content(soup)
            
            if len(content) < 100:  # 内容太少，可能不是有效页面
                print(f"    跳过 (内容太少: {len(content)} 字符)")
                return False
            
            # 保存文件
            filename = self.save_content(url, title, content)
            if filename:
                self.saved_files.append(filename)
                self.visited_urls.add(url)
                print(f"    ✅ 已保存: {title} ({len(content)} 字符)")
                return True
            
        except Exception as e:
            print(f"    ❌ 抓取失败: {e}")
        
        return False
    
    def extract_content(self, soup) -> str:
        """提取页面主要内容"""
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # 尝试多种内容选择器
        content_selectors = [
            '.main-content',
            '.content',
            '.doc-content',
            '.article-content',
            'main',
            '.container',
            'body'
        ]
        
        content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(separator='\n', strip=True)
                if len(content) > 200:  # 找到足够的内容就停止
                    break
        
        if not content:
            content = soup.get_text(separator='\n', strip=True)
        
        # 清理内容
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def save_content(self, url: str, title: str, content: str) -> str:
        """保存内容到文件"""
        try:
            # 生成文件名
            safe_title = re.sub(r'[^\w\s-]', '', title)[:50]
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{safe_title}_{url_hash}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"标题: {title}\n")
                f.write(f"内容长度: {len(content)} 字符\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)
            
            return filepath
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None
    
    def crawl_aliyun_docs(self, start_url: str, max_pages: int = 100) -> List[str]:
        """爬取阿里云文档"""
        print(f"🚀 开始爬取阿里云文档: {start_url}")
        print(f"📊 目标页面数: {max_pages}")
        
        # 第一层：爬取首页
        if not self.crawl_page(start_url):
            print("❌ 首页爬取失败")
            return []
        
        # 获取首页链接
        try:
            response = self.session.get(start_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            first_level_links = self.extract_aliyun_links(soup, start_url)
            print(f"📂 第1层发现 {len(first_level_links)} 个链接")
        except Exception as e:
            print(f"❌ 获取首页链接失败: {e}")
            return self.saved_files
        
        # 第二层：爬取主要分类页面
        second_level_links = []
        for i, link in enumerate(first_level_links[:20]):  # 限制第一层链接数
            if len(self.saved_files) >= max_pages:
                break
            
            print(f"📄 第1层 ({i+1}/{min(20, len(first_level_links))})")
            if self.crawl_page(link):
                # 获取这个页面的链接
                try:
                    response = self.session.get(link, timeout=15)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_links = self.extract_aliyun_links(soup, link)
                    second_level_links.extend(page_links)
                    print(f"    发现 {len(page_links)} 个子链接")
                except Exception:
                    pass
            
            time.sleep(0.5)  # 礼貌延迟
        
        print(f"📂 第2层发现 {len(second_level_links)} 个链接")
        
        # 第三层：爬取详细文档页面
        unique_links = list(set(second_level_links) - self.visited_urls)
        for i, link in enumerate(unique_links[:max_pages]):
            if len(self.saved_files) >= max_pages:
                break
            
            print(f"📄 第2层 ({i+1}/{min(max_pages, len(unique_links))})")
            self.crawl_page(link)
            time.sleep(0.3)  # 礼貌延迟
        
        print(f"\n🎉 爬取完成！")
        print(f"📊 总计爬取: {len(self.saved_files)} 个页面")
        
        return self.saved_files

def main():
    """主函数"""
    print("=" * 60)
    print("  阿里云文档增强爬虫测试")
    print("=" * 60)
    
    crawler = EnhancedAliyunCrawler()
    
    # 爬取阿里云文档
    saved_files = crawler.crawl_aliyun_docs(
        start_url="https://help.aliyun.com/",
        max_pages=50  # 先测试50页
    )
    
    print(f"\n📊 最终结果:")
    print(f"  成功爬取: {len(saved_files)} 页")
    print(f"  保存目录: {crawler.output_dir}")
    
    if saved_files:
        print(f"\n📄 部分文件列表:")
        for i, file_path in enumerate(saved_files[:10]):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            print(f"  {i+1}. {file_name} ({file_size} bytes)")
        
        if len(saved_files) > 10:
            print(f"  ... 还有 {len(saved_files) - 10} 个文件")

if __name__ == "__main__":
    main()
