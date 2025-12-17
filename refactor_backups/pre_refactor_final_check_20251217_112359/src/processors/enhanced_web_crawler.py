"""
增强版网页爬虫 - 集成异步并发和原有功能
"""

import asyncio
from .async_web_crawler import AsyncWebCrawler
from .web_crawler import WebCrawler
import time
from pathlib import Path

class EnhancedWebCrawler:
    def __init__(self):
        self.sync_crawler = WebCrawler()
        self.async_crawler = None
    
    async def crawl_async(
        self,
        start_url: str,
        max_depth: int = 3,
        max_pages: int = 8,
        parser_type: str = "default",
        exclude_patterns: list = None,
        status_callback=None,
        use_async: bool = True,
        max_concurrent: int = 10,
        ignore_robots: bool = False
    ):
        """异步爬取入口"""
        
        if not use_async:
            # 使用原有同步爬虫
            return self.sync_crawler.crawl_recursive(
                start_url, max_depth, max_pages, parser_type, exclude_patterns, status_callback
            )
        
        # 使用新的异步爬虫
        async with AsyncWebCrawler(max_concurrent=max_concurrent, ignore_robots=ignore_robots) as crawler:
            
            # 创建临时目录
            timestamp = int(time.time())
            temp_dir = f"temp_crawl_{timestamp}"
            
            if status_callback:
                status_callback(f"🚀 启用异步爬虫 (并发:{max_concurrent})")
            
            try:
                files = await crawler.crawl_recursive(
                    start_url=start_url,
                    max_depth=max_depth,
                    max_pages_per_level=max_pages,
                    output_dir=temp_dir,
                    status_callback=status_callback
                )
                
                # 转换为兼容格式 - 移动文件到temp_uploads目录
                import shutil
                import os
                from urllib.parse import urlparse
                from datetime import datetime
                
                # 确保目标目录存在
                os.makedirs("temp_uploads", exist_ok=True)
                
                # 生成最终目录名
                try:
                    domain = urlparse(start_url).netloc.replace('.', '_')
                except:
                    domain = "unknown"
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                final_dir = os.path.join("temp_uploads", f"Web_{domain}_{timestamp}")
                os.makedirs(final_dir, exist_ok=True)
                
                # 移动文件并返回新路径
                moved_files = []
                for file_path in files:
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        new_path = os.path.join(final_dir, filename)
                        shutil.move(file_path, new_path)
                        moved_files.append(new_path)
                
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
                if status_callback:
                    status_callback(f"✅ 异步爬取完成，文件已移动到: {final_dir}")
                
                return moved_files
                
            except Exception as e:
                if status_callback:
                    status_callback(f"❌ 异步爬取失败: {e}")
                    status_callback(f"🔄 回退到同步模式")
                
                # 回退到同步爬虫
                return self.sync_crawler.crawl_recursive(
                    start_url, max_depth, max_pages, parser_type, exclude_patterns, status_callback
                )
    
    def crawl_sync(self, *args, **kwargs):
        """同步爬取入口（兼容性）"""
        return self.sync_crawler.crawl_recursive(*args, **kwargs)

# 工厂函数
def create_crawler(async_mode: bool = True) -> EnhancedWebCrawler:
    """创建爬虫实例"""
    return EnhancedWebCrawler()

# 异步包装器
def run_async_crawl(*args, **kwargs):
    """在同步环境中运行异步爬虫"""
    crawler = EnhancedWebCrawler()
    
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已有事件循环在运行，创建任务
            return asyncio.create_task(crawler.crawl_async(*args, **kwargs))
        else:
            # 运行新的事件循环
            return loop.run_until_complete(crawler.crawl_async(*args, **kwargs))
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(crawler.crawl_async(*args, **kwargs))
