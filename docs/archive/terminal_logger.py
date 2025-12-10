"""
终端日志模块 - 彩色输出、详细日志、性能监控
"""
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager

# ANSI 颜色代码
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 亮色
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'

class TerminalLogger:
    def __init__(self, ui_callback=None):
        self.perf_stack = []
        self.metrics = {}
        self.cpu_baseline = None
        self.ui_callback = ui_callback
    
    def set_ui_callback(self, callback):
        """设置UI回调函数"""
        self.ui_callback = callback

    def _log_to_ui(self, level: str, msg: str):
        """同步日志到UI (限流机制，避免前端卡顿)"""
        if self.ui_callback:
            # 关键消息立即发送
            if level in ['error', 'success', 'warning']:
                try:
                    self.ui_callback(level, msg)
                except: pass
                return

            # 普通消息限流 (每0.1秒最多1条)
            import time
            now = time.time()
            if not hasattr(self, '_last_ui_log'):
                self._last_ui_log = 0
            
            if now - self._last_ui_log > 0.1:
                try:
                    self.ui_callback(level, msg)
                    self._last_ui_log = now
                except: pass
    
    def _timestamp(self) -> str:
        """获取时间戳"""
        return datetime.now().strftime("%H:%M:%S")
    
    def _format_msg(self, icon: str, level: str, msg: str, color: str) -> str:
        """格式化消息"""
        ts = self._timestamp()
        return f"{color}{icon} [{ts}] {msg}{Colors.RESET}"
    
    # ==================== 基础日志 ====================
    def info(self, msg: str, ui: bool = True):
        """信息日志"""
        print(self._format_msg("ℹ️", "INFO", msg, Colors.CYAN))
        if ui: self._log_to_ui("info", f"ℹ️ {msg}")
    
    def success(self, msg: str, ui: bool = True):
        """成功日志"""
        print(self._format_msg("✅", "SUCCESS", msg, Colors.GREEN))
        if ui: self._log_to_ui("success", f"✅ {msg}")
    
    def warning(self, msg: str, ui: bool = True):
        """警告日志"""
        print(self._format_msg("⚠️", "WARNING", msg, Colors.YELLOW))
        if ui: self._log_to_ui("warning", f"⚠️ {msg}")
    
    def error(self, msg: str, ui: bool = True):
        """错误日志"""
        print(self._format_msg("❌", "ERROR", msg, Colors.RED))
        if ui: self._log_to_ui("error", f"❌ {msg}")
    
    def debug(self, msg: str, ui: bool = False):
        """调试日志 (默认不显示在UI)"""
        print(self._format_msg("🔍", "DEBUG", msg, Colors.DIM + Colors.WHITE))
        if ui: self._log_to_ui("code", f"🔍 {msg}")
    
    # ==================== 操作日志 ====================
    def start_operation(self, operation: str, details: str = ""):
        """开始操作"""
        msg = f"开始: {operation}"
        if details:
            msg += f" ({details})"
        print(self._format_msg("🚀", "START", msg, Colors.BRIGHT_BLUE))
    
    def processing(self, msg: str):
        """处理中"""
        print(self._format_msg("⏳", "PROCESSING", msg, Colors.BRIGHT_CYAN))
    
    def complete_operation(self, operation: str, details: str = ""):
        """完成操作"""
        msg = f"完成: {operation}"
        if details:
            msg += f" ({details})"
        print(self._format_msg("✨", "COMPLETE", msg, Colors.BRIGHT_GREEN))
    
    # ==================== 数据日志 ====================
    def data_summary(self, title: str, data: Dict[str, Any]):
        """数据摘要"""
        print(self._format_msg("📊", "DATA", f"{title}:", Colors.MAGENTA))
        for key, value in data.items():
            print(f"  {Colors.DIM}├─ {key}: {value}{Colors.RESET}")
    
    def list_items(self, title: str, items: list):
        """列表项"""
        print(self._format_msg("📋", "LIST", f"{title}:", Colors.MAGENTA))
        for i, item in enumerate(items, 1):
            prefix = "└─" if i == len(items) else "├─"
            print(f"  {Colors.DIM}{prefix} {item}{Colors.RESET}")
    
    # ==================== 性能监控 ====================
    @contextmanager
    def timer(self, operation: str, show_result: bool = True):
        """性能计时器上下文管理器"""
        start_time = time.time()
        self.start_operation(operation)
        
        try:
            yield
        except Exception as e:
            elapsed = time.time() - start_time
            self.error(f"{operation} 失败 ({elapsed:.2f}s): {str(e)}")
            raise
        else:
            elapsed = time.time() - start_time
            if show_result:
                self.complete_operation(operation, f"{elapsed:.2f}s")
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed)
    
    def get_metrics(self, operation: str = None) -> Dict[str, Any]:
        """获取性能指标"""
        if operation:
            times = self.metrics.get(operation, [])
            if not times:
                return {}
            return {
                "count": len(times),
                "total": sum(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
            }
        
        result = {}
        for op, times in self.metrics.items():
            if times:
                result[op] = {
                    "count": len(times),
                    "total": sum(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                }
        return result
    
    def show_metrics(self):
        """显示所有性能指标"""
        metrics = self.get_metrics()
        if not metrics:
            self.info("暂无性能数据")
            return
        
        print(self._format_msg("📈", "METRICS", "性能统计:", Colors.BRIGHT_YELLOW))
        for op, data in metrics.items():
            print(f"  {Colors.BOLD}{op}{Colors.RESET}")
            print(f"    {Colors.DIM}├─ 执行次数: {data['count']}{Colors.RESET}")
            print(f"    {Colors.DIM}├─ 总耗时: {data['total']:.2f}s{Colors.RESET}")
            print(f"    {Colors.DIM}├─ 平均: {data['avg']:.2f}s{Colors.RESET}")
            print(f"    {Colors.DIM}├─ 最小: {data['min']:.2f}s{Colors.RESET}")
            print(f"    {Colors.DIM}└─ 最大: {data['max']:.2f}s{Colors.RESET}")
    
    # ==================== 进度显示 ====================
    def progress_bar(self, current: int, total: int, label: str = ""):
        """简单进度条"""
        if total == 0:
            return
        
        percent = current / total
        bar_len = 30
        filled = int(bar_len * percent)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        msg = f"{label} [{bar}] {current}/{total} ({percent*100:.0f}%)"
        sys.stdout.write(f"\r{Colors.CYAN}{msg}{Colors.RESET}")
        sys.stdout.flush()
        
        if current == total:
            print()  # 换行
    
    # ==================== 分隔符 ====================
    def separator(self, title: str = ""):
        """分隔符"""
        if title:
            print(f"{Colors.DIM}{'─' * 20} {title} {'─' * 20}{Colors.RESET}")
        else:
            print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")
    
    # ==================== CPU 多核监控 ====================
    def cpu_multicore_start(self, num_workers: int):
        """记录多核处理开始"""
        try:
            import psutil
            self.cpu_baseline = psutil.cpu_percent(interval=0.1)
            msg = f"🚀 启动多核并行: {num_workers} 个Worker | 当前 CPU: {self.cpu_baseline:.1f}%"
            print(self._format_msg("🔥", "MULTICORE", msg, Colors.BRIGHT_MAGENTA))
        except:
            pass
    
    def cpu_multicore_status(self, processed: int, total: int):
        """显示多核处理状态"""
        try:
            import psutil
            cpu_now = psutil.cpu_percent(interval=0.5)  # 增加到0.5秒获取更准确的数据
            cpu_cores = psutil.cpu_count()
            cores_used = cpu_now / 100 * cpu_cores
            
            msg = f"📊 处理进度: {processed}/{total} | CPU: {cpu_now:.1f}% ({cores_used:.1f}核) | 目标: 90%"
            
            # 根据 CPU 使用率显示不同颜色
            if cpu_now >= 80:
                color = Colors.BRIGHT_GREEN
                icon = "✅"
            elif cpu_now >= 50:
                color = Colors.BRIGHT_YELLOW
                icon = "⚡"
            else:
                color = Colors.YELLOW
                icon = "⚠️"
            
            print(self._format_msg(icon, "CPU", msg, color))
        except:
            pass
    
    def cpu_multicore_end(self, total_docs: int, elapsed: float):
        """记录多核处理结束"""
        try:
            import psutil
            cpu_final = psutil.cpu_percent(interval=0.5)
            cpu_cores = psutil.cpu_count()
            cores_used = cpu_final / 100 * cpu_cores
            throughput = total_docs / elapsed if elapsed > 0 else 0
            
            msg = f"✅ 多核处理完成: {total_docs} 个文档 | 耗时: {elapsed:.1f}s | 吞吐: {throughput:.1f} docs/s"
            print(self._format_msg("🎉", "COMPLETE", msg, Colors.BRIGHT_GREEN))
            
            msg2 = f"📊 最终 CPU: {cpu_final:.1f}% ({cores_used:.1f}核) | 提升: {cpu_final - self.cpu_baseline:.1f}%"
            print(self._format_msg("📈", "STATS", msg2, Colors.BRIGHT_CYAN))
        except:
            pass


# 全局实例
terminal_logger = TerminalLogger()
