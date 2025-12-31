#!/usr/bin/env python3
"""
配置文件监控器 - 支持热更新
"""
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigHandler(FileSystemEventHandler):
    def __init__(self, config_file):
        self.config_file = config_file
        
    def on_modified(self, event):
        if event.src_path == str(self.config_file):
            print(f"🔄 配置文件已更新: {self.config_file}")
            # 这里可以添加重新加载配置的逻辑

def watch_config(config_file):
    """监控配置文件变化"""
    event_handler = ConfigHandler(config_file)
    observer = Observer()
    observer.schedule(event_handler, str(config_file.parent), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    config_file = Path("config/app_config.json")
    watch_config(config_file)
