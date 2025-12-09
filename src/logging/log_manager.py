"""统一日志管理器 - 整合文件日志和终端日志"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import contextmanager


class LogManager:
    """统一日志管理器"""
    
    # 日志级别
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    SUCCESS = 'SUCCESS'
    
    def __init__(self, log_dir: str = "app_logs", enable_terminal: bool = True):
        self.log_dir = log_dir
        self.enable_terminal = enable_terminal
        self.timers = {}
        self.perf_stack = []
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        self.log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d')}.jsonl")
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        try:
            import glob
            cutoff = datetime.now() - timedelta(days=days)
            
            for log_file in glob.glob(os.path.join(self.log_dir, 'log_*.jsonl')):
                try:
                    filename = os.path.basename(log_file)
                    date_str = filename.split('_')[1].split('.')[0]
                    log_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    if log_date < cutoff:
                        os.remove(log_file)
                except Exception:
                    continue
        except Exception:
            pass
    
    def log(self, level: str, message: str, stage: str = "", details: Optional[Dict] = None):
        """记录日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "stage": stage,
            "message": message,
            "details": details or {}
        }
        
        # 写入文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception:
            pass
        
        # 终端输出
        if self.enable_terminal:
            self._print_terminal(level, message, stage)
    
    def _print_terminal(self, level: str, message: str, stage: str = ""):
        """终端输出"""
        icons = {
            self.DEBUG: "🔍",
            self.INFO: "ℹ️",
            self.WARNING: "⚠️",
            self.ERROR: "❌",
            self.SUCCESS: "✅"
        }
        icon = icons.get(level, "📝")
        
        if stage:
            print(f"{icon} [{stage}] {message}")
        else:
            print(f"{icon} {message}")
    
    def debug(self, message: str, stage: str = "", details: Optional[Dict] = None):
        """调试日志"""
        self.log(self.DEBUG, message, stage, details)
    
    def info(self, message: str, stage: str = "", details: Optional[Dict] = None):
        """信息日志"""
        self.log(self.INFO, message, stage, details)
    
    def warning(self, message: str, stage: str = "", details: Optional[Dict] = None):
        """警告日志"""
        self.log(self.WARNING, message, stage, details)
    
    def error(self, message: str, stage: str = "", details: Optional[Dict] = None):
        """错误日志"""
        self.log(self.ERROR, message, stage, details)
    
    def success(self, message: str, stage: str = "", details: Optional[Dict] = None):
        """成功日志"""
        self.log(self.SUCCESS, message, stage, details)
    
    def start_timer(self, name: str):
        """开始计时"""
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时"""
        if name in self.timers:
            elapsed = time.time() - self.timers[name]
            del self.timers[name]
            return elapsed
        return 0.0
    
    @contextmanager
    def timer(self, name: str, log_result: bool = True):
        """计时上下文管理器"""
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            if log_result:
                self.info(f"{name} 耗时: {elapsed:.2f}秒")
    
    @contextmanager
    def stage(self, stage_name: str):
        """阶段上下文管理器"""
        self.info(f"开始: {stage_name}", stage=stage_name)
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.success(f"完成: {stage_name} (耗时: {elapsed:.2f}秒)", stage=stage_name)
    
    def get_log_file(self) -> str:
        """获取当前日志文件路径"""
        return self.log_file


# 全局单例
_global_logger: Optional[LogManager] = None


def get_logger() -> LogManager:
    """获取全局日志管理器"""
    global _global_logger
    if _global_logger is None:
        _global_logger = LogManager()
    return _global_logger


def set_logger(logger: LogManager):
    """设置全局日志管理器"""
    global _global_logger
    _global_logger = logger
