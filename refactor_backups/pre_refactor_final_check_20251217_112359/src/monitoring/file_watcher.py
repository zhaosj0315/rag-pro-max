"""
实时文件监控模块 - v2.1
自动检测文件变化并触发增量更新
"""

import os
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, Set, Dict, Optional
import streamlit as st

class DocumentWatcher(FileSystemEventHandler):
    """文档监控处理器"""
    
    def __init__(self, kb_manager, update_callback: Optional[Callable] = None):
        self.kb_manager = kb_manager
        self.update_callback = update_callback
        self.watched_files: Set[str] = set()
        self.processing_lock = threading.Lock()
        
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        if self._should_process_file(file_path):
            self._trigger_incremental_update(file_path)
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            file_path = event.src_path
            if self._should_process_file(file_path):
                self._trigger_incremental_update(file_path)
    
    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            file_path = event.src_path
            self._remove_from_kb(file_path)
    
    def _should_process_file(self, file_path: str) -> bool:
        """判断是否应该处理该文件"""
        supported_extensions = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.pptx', '.csv', '.html', '.json'}
        return Path(file_path).suffix.lower() in supported_extensions
    
    def _trigger_incremental_update(self, file_path: str):
        """触发增量更新"""
        with self.processing_lock:
            try:
                if hasattr(self.kb_manager, 'incremental_update'):
                    self.kb_manager.incremental_update(file_path)
                    if self.update_callback:
                        self.update_callback(f"已更新: {Path(file_path).name}")
            except Exception as e:
                if self.update_callback:
                    self.update_callback(f"更新失败: {e}")
    
    def _remove_from_kb(self, file_path: str):
        """从知识库中移除文件"""
        with self.processing_lock:
            try:
                if hasattr(self.kb_manager, 'remove_document'):
                    self.kb_manager.remove_document(file_path)
                    if self.update_callback:
                        self.update_callback(f"已移除: {Path(file_path).name}")
            except Exception as e:
                if self.update_callback:
                    self.update_callback(f"移除失败: {e}")

class FileWatcherManager:
    """文件监控管理器"""
    
    def __init__(self):
        self.observer: Optional[Observer] = None
        self.watched_paths: Dict[str, DocumentWatcher] = {}
        self.is_running = False
    
    def start_watching(self, path: str, kb_manager, update_callback: Optional[Callable] = None):
        """开始监控指定路径"""
        if not os.path.exists(path):
            return False
            
        if not self.observer:
            self.observer = Observer()
        
        # 创建监控处理器
        handler = DocumentWatcher(kb_manager, update_callback)
        
        # 添加监控路径
        self.observer.schedule(handler, path, recursive=True)
        self.watched_paths[path] = handler
        
        if not self.is_running:
            self.observer.start()
            self.is_running = True
        
        return True
    
    def stop_watching(self, path: str = None):
        """停止监控"""
        if path and path in self.watched_paths:
            del self.watched_paths[path]
        
        if not path or not self.watched_paths:
            if self.observer and self.is_running:
                self.observer.stop()
                self.observer.join()
                self.is_running = False
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'watched_paths': list(self.watched_paths.keys()),
            'total_watchers': len(self.watched_paths)
        }

# 全局监控管理器
file_watcher_manager = FileWatcherManager()
