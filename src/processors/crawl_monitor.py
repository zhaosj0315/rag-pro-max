"""
实时爬取监控系统 - v2.4.1
提供实时爬取进度、统计和控制功能
"""

import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class CrawlStats:
    """爬取统计数据"""
    start_time: datetime = field(default_factory=datetime.now)
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    current_depth: int = 1
    max_depth: int = 2
    discovered_links: int = 0
    processing_speed: float = 0.0  # 页面/分钟
    estimated_completion: Optional[datetime] = None
    current_url: str = ""
    status: str = "准备中"  # 准备中, 爬取中, 暂停, 完成, 错误
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_pages == 0:
            return 0.0
        return (self.successful_pages / self.total_pages) * 100
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def pages_per_minute(self) -> float:
        """每分钟页面数"""
        elapsed_minutes = self.elapsed_time / 60
        if elapsed_minutes == 0:
            return 0.0
        return self.successful_pages / elapsed_minutes

class CrawlMonitor:
    """爬取监控器"""
    
    def __init__(self):
        self.stats = CrawlStats()
        self.is_paused = False
        self.should_stop = False
        self.callbacks: List[Callable] = []
        self.lock = threading.Lock()
        self.depth_stats: Dict[int, Dict] = {}
        
    def start_crawl(self, max_depth: int, estimated_pages: int):
        """开始爬取"""
        with self.lock:
            self.stats = CrawlStats(max_depth=max_depth)
            self.stats.status = "爬取中"
            self.is_paused = False
            self.should_stop = False
            self.depth_stats = {}
        self._notify_callbacks()
    
    def update_progress(self, 
                       current_url: str,
                       depth: int,
                       page_count: int,
                       success: bool,
                       discovered_links: int = 0):
        """更新进度"""
        with self.lock:
            self.stats.current_url = current_url
            self.stats.current_depth = depth
            self.stats.total_pages = page_count
            
            if success:
                self.stats.successful_pages += 1
            else:
                self.stats.failed_pages += 1
            
            if discovered_links > 0:
                self.stats.discovered_links += discovered_links
            
            # 更新深度统计
            if depth not in self.depth_stats:
                self.depth_stats[depth] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "links_found": 0
                }
            
            depth_stat = self.depth_stats[depth]
            depth_stat["total"] += 1
            if success:
                depth_stat["successful"] += 1
            else:
                depth_stat["failed"] += 1
            depth_stat["links_found"] += discovered_links
            
            # 计算处理速度
            self.stats.processing_speed = self.stats.pages_per_minute
            
        self._notify_callbacks()
    
    def pause_crawl(self):
        """暂停爬取"""
        with self.lock:
            self.is_paused = True
            self.stats.status = "暂停"
        self._notify_callbacks()
    
    def resume_crawl(self):
        """恢复爬取"""
        with self.lock:
            self.is_paused = False
            self.stats.status = "爬取中"
        self._notify_callbacks()
    
    def stop_crawl(self, reason: str = "用户停止"):
        """停止爬取"""
        with self.lock:
            self.should_stop = True
            self.stats.status = f"已停止: {reason}"
        self._notify_callbacks()
    
    def complete_crawl(self):
        """完成爬取"""
        with self.lock:
            self.stats.status = "完成"
        self._notify_callbacks()
    
    def add_callback(self, callback: Callable):
        """添加状态变化回调"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self):
        """通知所有回调"""
        for callback in self.callbacks:
            try:
                callback(self.get_status())
            except Exception:
                pass  # 忽略回调错误
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        with self.lock:
            return {
                "stats": {
                    "total_pages": self.stats.total_pages,
                    "successful_pages": self.stats.successful_pages,
                    "failed_pages": self.stats.failed_pages,
                    "success_rate": self.stats.success_rate,
                    "current_depth": self.stats.current_depth,
                    "max_depth": self.stats.max_depth,
                    "discovered_links": self.stats.discovered_links,
                    "processing_speed": self.stats.processing_speed,
                    "elapsed_time": self.stats.elapsed_time,
                    "current_url": self.stats.current_url,
                    "status": self.stats.status
                },
                "depth_stats": self.depth_stats.copy(),
                "controls": {
                    "is_paused": self.is_paused,
                    "should_stop": self.should_stop
                }
            }
    
    def generate_progress_text(self) -> str:
        """生成进度文本"""
        status = self.get_status()
        stats = status["stats"]
        
        progress_text = f"""
🚀 **爬取进度**

📊 **总体统计**:
- 已处理: {stats['successful_pages']}/{stats['total_pages']} 页
- 成功率: {stats['success_rate']:.1f}%
- 当前深度: {stats['current_depth']}/{stats['max_depth']}
- 发现链接: {stats['discovered_links']} 个

⚡ **性能指标**:
- 处理速度: {stats['processing_speed']:.1f} 页/分钟
- 已用时间: {stats['elapsed_time']:.1f} 秒
- 状态: {stats['status']}

🌐 **当前处理**: {stats['current_url'][:50]}...
        """
        
        return progress_text.strip()

# 使用示例
if __name__ == "__main__":
    monitor = CrawlMonitor()
    
    # 添加状态回调
    def on_status_change(status):
        print(f"状态更新: {status['stats']['status']}")
    
    monitor.add_callback(on_status_change)
    
    # 模拟爬取过程
    monitor.start_crawl(max_depth=2, estimated_pages=100)
    
    for i in range(10):
        monitor.update_progress(
            current_url=f"https://example.com/page{i}",
            depth=1,
            page_count=i+1,
            success=True,
            discovered_links=5
        )
        time.sleep(0.1)
    
    print(monitor.generate_progress_text())
