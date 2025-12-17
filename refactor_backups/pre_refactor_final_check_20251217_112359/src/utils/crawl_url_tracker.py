#!/usr/bin/env python3
"""
爬虫URL跟踪器
实时显示当前正在爬取的URL
"""

import time
import threading
from typing import Optional, Callable
from datetime import datetime

class CrawlURLTracker:
    """爬虫URL跟踪器"""
    
    def __init__(self):
        self.current_url = None
        self.start_time = None
        self.total_urls = 0
        self.completed_urls = 0
        self.failed_urls = 0
        self.status_callback = None
        self._lock = threading.Lock()
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def start_crawling(self, total_urls: int):
        """开始爬取"""
        with self._lock:
            self.start_time = time.time()
            self.total_urls = total_urls
            self.completed_urls = 0
            self.failed_urls = 0
            self._log(f"🚀 开始爬取 {total_urls} 个URL")
    
    def set_current_url(self, url: str):
        """设置当前正在爬取的URL"""
        with self._lock:
            self.current_url = url
            self._log(f"🔍 正在爬取: {url}")
    
    def url_completed(self, url: str, success: bool = True):
        """URL完成"""
        with self._lock:
            if success:
                self.completed_urls += 1
                self._log(f"✅ 完成: {url}")
            else:
                self.failed_urls += 1
                self._log(f"❌ 失败: {url}")
            
            # 显示进度
            progress = (self.completed_urls + self.failed_urls) / self.total_urls * 100
            elapsed = time.time() - self.start_time if self.start_time else 0
            speed = (self.completed_urls + self.failed_urls) / elapsed if elapsed > 0 else 0
            
            self._log(f"📊 进度: {self.completed_urls + self.failed_urls}/{self.total_urls} ({progress:.1f}%) | 速度: {speed:.1f} URL/秒")
    
    def get_status(self) -> dict:
        """获取当前状态"""
        with self._lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            return {
                'current_url': self.current_url,
                'total_urls': self.total_urls,
                'completed_urls': self.completed_urls,
                'failed_urls': self.failed_urls,
                'elapsed_time': elapsed,
                'speed': (self.completed_urls + self.failed_urls) / elapsed if elapsed > 0 else 0
            }
    
    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self.status_callback:
            self.status_callback(log_message)
        else:
            print(log_message)

# 全局跟踪器实例
url_tracker = CrawlURLTracker()

def track_url(url: str):
    """跟踪URL（装饰器辅助函数）"""
    url_tracker.set_current_url(url)

def url_completed(url: str, success: bool = True):
    """URL完成（辅助函数）"""
    url_tracker.url_completed(url, success)

def start_tracking(total_urls: int):
    """开始跟踪（辅助函数）"""
    url_tracker.start_crawling(total_urls)

def get_tracking_status() -> dict:
    """获取跟踪状态（辅助函数）"""
    return url_tracker.get_status()
