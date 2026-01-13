"""统一日志管理器 - 整合文件日志和终端日志"""

import os
import json
import time
import getpass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


# 全局单例
_global_logger_instance = None


class LogManager:
    """统一日志管理器 - 替代 terminal_logger"""
    
    # 日志级别
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    SUCCESS = 'SUCCESS'
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        global _global_logger_instance
        if _global_logger_instance is None:
            _global_logger_instance = super().__new__(cls)
        return _global_logger_instance
    
    def __init__(self, log_dir: str = "app_logs", enable_terminal: bool = True):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.enable_terminal = enable_terminal # 极其重要：先锚定终端标志
        
        # [Diagnostic] 记录终端日志状态到文件
        self.log(self.DEBUG, f"LogManager initialized: enable_terminal={self.enable_terminal}, user={getpass.getuser()}", stage="Internal")
        
        # [v5.5.4] 权限自愈补丁：探测目录是否可写
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            # 测试写入权限
            test_file = os.path.join(log_dir, ".write_test")
            with open(test_file, 'w') as f: f.write("test")
            os.remove(test_file)
            self.log_dir = log_dir
        except Exception:
            # 降级到用户主目录
            fallback_dir = os.path.expanduser("~/.rag_pro_max/app_logs")
            try:
                os.makedirs(fallback_dir, exist_ok=True)
                self.log_dir = fallback_dir
                if self.enable_terminal:
                    print(f"⚠️ [WARNING] 默认日志目录 {log_dir} 无写入权限，已降级至 {fallback_dir}")
            except:
                # 最后的最后：使用临时目录
                import tempfile
                self.log_dir = tempfile.gettempdir()
                if self.enable_terminal:
                    print(f"⚠️ [CRITICAL] 权限彻底锁定，日志降级至临时目录: {self.log_dir}")

        # 使用当前用户名防止多用户冲突
        current_user = getpass.getuser()
        self.log_file = os.path.join(self.log_dir, f"log_{datetime.now().strftime('%Y%m%d')}_{current_user}.jsonl")
        
        # 再次确认文件写入权限，如果当前文件被root占用了，尝试重命名
        try:
            # 显式尝试以追加模式打开或创建
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'a', encoding='utf-8') as f: pass
            
            # [核心修复] 强制设置文件权限为 666
            try:
                os.chmod(self.log_file, 0o666)
                # 如果是 root 运行，尝试把组改回普通用户的组（通常是 staff）
                if current_user == 'root':
                    import pwd
                    # 尝试寻找标准用户的 gid
                    try:
                        std_user = pwd.getpwnam('zhaosj')
                        os.chown(self.log_file, -1, std_user.pw_gid)
                    except: pass
            except: pass 
        except PermissionError:
             if self.enable_terminal:
                print(f"⚠️ [LogManager] {self.log_file} 权限被锁定，已自动切换到专属日志文件")
             # 如果文件被占用了，加个时间戳后缀
             self.log_file = os.path.join(self.log_dir, f"log_{datetime.now().strftime('%Y%m%d')}_{current_user}_{int(time.time())}.jsonl")
             # 对新文件也尝试设置权限
             try:
                 with open(self.log_file, 'a') as f: pass
                 os.chmod(self.log_file, 0o666)
             except: pass
        
        # Initialize metrics and tracking
        self.metrics: Dict[str, List[float]] = {}
        self.timers: Dict[str, float] = {}
        self._recent_logs: List[str] = []
        self._max_recent: int = 100
        
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        try:
            import glob
            cutoff = datetime.now() - timedelta(days=days)
            
            for log_file in glob.glob(os.path.join(self.log_dir, 'log_*.jsonl')):
                try:
                    filename = os.path.basename(log_file)
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        date_str = parts[1]
                        # 简单的日期校验
                        if len(date_str) == 8 and date_str.isdigit():
                            log_date = datetime.strptime(date_str, '%Y%m%d')
                            
                            if log_date < cutoff:
                                os.remove(log_file)
                except Exception:
                    continue
        except Exception:
            pass
    
    def _is_duplicate(self, message: str, stage: str) -> bool:
        """检查是否为重复日志"""
        log_key = f"{stage}:{message}"
        
        if log_key in self._recent_logs:
            return True
            
        # 添加到最近日志列表
        self._recent_logs.append(log_key)
        if len(self._recent_logs) > self._max_recent:
            self._recent_logs.pop(0)
            
        return False
    
    def log(self, level: str, message: str, stage: str = "", details: Optional[Dict] = None):
        """记录日志"""
        # 检查重复日志（模型加载等重复信息）
        if stage in ["模型加载", "GPU状态"] and self._is_duplicate(message, stage):
            return
            
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
            self._print_terminal(level, message, stage, details)
    
    def _print_terminal(self, level: str, message: str, stage: str = "", details: Optional[Dict] = None):
        """终端输出"""
        import sys
        icons = {
            self.DEBUG: "🔍",
            self.INFO: "ℹ️",
            self.WARNING: "⚠️",
            self.ERROR: "❌",
            self.SUCCESS: "✅"
        }
        icon = icons.get(level, "📝")
        ts = datetime.now().strftime("%H:%M:%S")
        
        # 增强显示：如果有模型信息，追加到消息中
        if details and 'model' in details:
            message += f" (Model: {details['model']})"
        
        # 增加角色显示
        if details and 'role' in details:
            message += f" [角色: {details['role']}]"
        
        if stage:
            output = f"{icon} [{ts}] [{stage}] {message}\n"
        else:
            output = f"{icon} [{ts}] {message}\n"
            
        sys.stdout.write(output)
        sys.stdout.flush()
    
    # ==================== 基础日志方法 ====================
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
    
    # ==================== 操作日志 ====================
    def start_operation(self, operation: str, details: str = ""):
        """开始操作"""
        import sys
        msg = f"开始: {operation}"
        if details:
            msg += f" - {details}"
        if self.enable_terminal:
            sys.stdout.write(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            sys.stdout.flush()
        self.log(self.INFO, msg)
    
    def processing(self, message: str):
        """处理中"""
        import sys
        if self.enable_terminal:
            sys.stdout.write(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            sys.stdout.flush()
        self.log(self.INFO, message)
    
    def complete_operation(self, operation: str, details: str = ""):
        """完成操作"""
        import sys
        msg = f"完成: {operation}"
        if details:
            msg += f" - {details}"
        if self.enable_terminal:
            sys.stdout.write(f"✨ [{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            sys.stdout.flush()
        self.log(self.SUCCESS, msg)
    
    # ==================== 数据日志 ====================
    def data_summary(self, title: str, data: Dict[str, Any]):
        """数据摘要"""
        import sys
        if self.enable_terminal:
            sys.stdout.write(f"📊 [{datetime.now().strftime('%H:%M:%S')}] {title}:\n")
            for key, value in data.items():
                sys.stdout.write(f"  ├─ {key}: {value}\n")
            sys.stdout.flush()
        self.log(self.INFO, f"{title}: {data}")
    
    def list_items(self, title: str, items: List[str]):
        """列表项"""
        import sys
        if self.enable_terminal:
            sys.stdout.write(f"📋 [{datetime.now().strftime('%H:%M:%S')}] {title}:\n")
            for item in items:
                sys.stdout.write(f"  • {item}\n")
            sys.stdout.flush()
        self.log(self.INFO, f"{title}: {items}")
    
    # ==================== 分隔符 ====================
    def separator(self, title: str = ""):
        """分隔符"""
        import sys
        if self.enable_terminal:
            if title:
                sys.stdout.write(f"\n{'='*60}\n")
                sys.stdout.write(f"  {title}\n")
                sys.stdout.write(f"{'='*60}\n")
            else:
                sys.stdout.write(f"{'='*60}\n")
            sys.stdout.flush()
    
    # ==================== 性能监控 ====================
    def start_timer(self, name: str):
        """开始计时"""
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时"""
        if name in self.timers:
            elapsed = time.time() - self.timers[name]
            del self.timers[name]
            
            # 记录性能指标
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(elapsed)
            
            return elapsed
        return 0.0
    
    @contextmanager
    def timer(self, operation: str, show_result: bool = True):
        """计时上下文管理器"""
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            if show_result and self.enable_terminal:
                print(f"⏱️  [{datetime.now().strftime('%H:%M:%S')}] {operation} 耗时: {elapsed:.2f}秒")
            
            # 记录性能指标
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed)
    
    @contextmanager
    def stage(self, stage_name: str):
        """阶段上下文管理器"""
        self.start_operation(stage_name)
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.complete_operation(stage_name, f"耗时: {elapsed:.2f}秒")
    
    def get_metrics(self, operation: str = None) -> Dict[str, Any]:
        """获取性能指标"""
        if operation:
            if operation in self.metrics:
                times = self.metrics[operation]
                return {
                    "count": len(times),
                    "total": sum(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
            return {}
        
        # 返回所有指标
        result = {}
        for op, times in self.metrics.items():
            result[op] = {
                "count": len(times),
                "total": sum(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times)
            }
        return result
    
    def show_metrics(self):
        """显示所有性能指标"""
        import sys
        metrics = self.get_metrics()
        if not metrics:
            self.info("暂无性能指标")
            return
        
        self.separator("性能指标")
        if self.enable_terminal:
            for operation, stats in metrics.items():
                sys.stdout.write(f"  {operation}:\n")
                sys.stdout.write(f"    次数: {stats['count']}\n")
                sys.stdout.write(f"    总计: {stats['total']:.2f}秒\n")
                sys.stdout.write(f"    平均: {stats['avg']:.2f}秒\n")
                sys.stdout.write(f"    最小: {stats['min']:.2f}秒\n")
                sys.stdout.write(f"    最大: {stats['max']:.2f}秒\n")
            sys.stdout.flush()
    
    # ==================== 进度显示 ====================
    def progress_bar(self, current: int, total: int, label: str = ""):
        """简单进度条"""
        if total == 0:
            return
        
        percent = int((current / total) * 100)
        bar_length = 40
        filled = int((current / total) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        if self.enable_terminal:
            print(f"\r{label} [{bar}] {percent}% ({current}/{total})", end='', flush=True)
            if current == total:
                print()  # 完成后换行
    
    # ==================== 多核处理监控 ====================
    def cpu_multicore_start(self, num_workers: int):
        """记录多核处理开始"""
        self.info(f"🔥 启动多核处理: {num_workers} 个工作进程")
    
    def cpu_multicore_status(self, processed: int, total: int):
        """显示多核处理状态"""
        self.progress_bar(processed, total, "多核处理进度")
    
    def cpu_multicore_end(self, total_docs: int, elapsed: float):
        """记录多核处理结束"""
        speed = total_docs / elapsed if elapsed > 0 else 0
        self.success(f"多核处理完成: {total_docs} 个文档, 耗时 {elapsed:.2f}秒, 速度 {speed:.1f} docs/s")
    
    # ==================== 工具方法 ====================
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
