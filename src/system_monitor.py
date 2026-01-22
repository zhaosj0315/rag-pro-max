#!/usr/bin/env python3
"""
RAG Pro Max 系统监控大屏 (System Monitor Dashboard)
------------------------------------------------
基于 Rich 库构建的终端监控仪表盘，专为 RAG 应用优化。
提供 CPU/GPU/内存/磁盘/网络/电池 以及 关键进程(Streamlit/Ollama等) 的实时监控。

Usage:
    python3 src/system_monitor.py
    sudo python3 src/system_monitor.py (推荐，以获取完整 GPU 功耗数据)
"""

import os
import sys
import time
import psutil
import subprocess
import threading
from datetime import datetime, timedelta
from collections import deque

# 自动处理路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 尝试导入 Rich，如果不存在则提示安装
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.columns import Columns
    from rich.text import Text
    from rich.align import Align
    from rich import box
except ImportError:
    print("❌ 错误: 缺少 'rich' 库。请运行: pip install rich")
    sys.exit(1)

from src.app_logging.log_manager import LogManager

# 初始化日志 (仅用于后台记录，不干扰前台显示)
logger = LogManager(enable_terminal=False)

class SystemMonitor:
    def __init__(self, history_len=60):
        self.console = Console()
        self.history_len = history_len
        self.net_io_counters = psutil.net_io_counters()
        self.disk_io_counters = psutil.disk_io_counters()
        self.last_time = time.time()
        
        # 历史数据 (可用于绘制迷你图，暂留接口)
        self.cpu_history = deque(maxlen=history_len)
        self.mem_history = deque(maxlen=history_len)
        
        # RAG 相关进程关键词
        self.rag_keywords = ['streamlit', 'ollama', 'chroma', 'python', 'node']
        self.rag_exact_names = ['ollama_llama_server']

    def get_gpu_info(self):
        """获取 Apple Silicon GPU 信息 (需要 sudo)"""
        try:
            # 使用 -n 1 只采样一次，降低延迟
            result = subprocess.run(
                ['sudo', 'powermetrics', '--samplers', 'gpu_power', '-i', '100', '-n', '1'],
                capture_output=True, text=True, timeout=1
            )
            
            if result.returncode != 0:
                return {'usage': 0.0, 'freq': 'N/A', 'power': 'N/A', 'auth': False}
            
            lines = result.stdout.split('\n')
            usage = 0.0
            freq = '0 MHz'
            power = '0 mW'
            
            for line in lines:
                if 'GPU HW active residency:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        try:
                            usage = float(parts[1].strip().split('%')[0].strip())
                        except:
                            pass
                elif 'GPU HW active frequency:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        freq = parts[1].strip()
                elif 'GPU Power:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        power = parts[1].strip()
                            
            return {'usage': usage, 'freq': freq, 'power': power, 'auth': True}
        except Exception:
            return {'usage': 0.0, 'freq': 'N/A', 'power': 'N/A', 'auth': False}

    def get_rag_processes(self):
        """获取 RAG 相关进程"""
        rag_procs = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'status']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        continue
                        
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    is_related = False
                    # 检查精确匹配
                    if name in self.rag_exact_names:
                        is_related = True
                    # 检查关键词匹配 (cmdline 更准确)
                    elif any(k in cmdline for k in self.rag_keywords):
                        # 过滤掉 system_monitor 自身
                        if 'system_monitor.py' in cmdline:
                            continue
                        # Streamlit 特别检查
                        if 'streamlit' in cmdline and 'apppro.py' in cmdline:
                            name = "Streamlit (Main)"
                            is_related = True
                        elif 'ollama' in name or 'ollama' in cmdline:
                            name = "Ollama Service"
                            is_related = True
                        elif 'python' in name and ('rag' in cmdline or 'src' in cmdline):
                            name = "RAG Worker"
                            is_related = True
                            
                    if is_related:
                        rag_procs.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
            
        # 按 CPU 使用率排序
        return sorted(rag_procs, key=lambda p: p.info['cpu_percent'], reverse=True)

    def get_metrics(self):
        """收集所有监控指标"""
        now = time.time()
        delta = now - self.last_time
        self.last_time = now
        
        # CPU
        cpu_pct = psutil.cpu_percent(interval=None)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        load_avg = psutil.getloadavg() # (1, 5, 15 min)
        
        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk
        try:
            disk = psutil.disk_usage('/System/Volumes/Data')
        except:
            disk = psutil.disk_usage('/')
            
        # Network Speed
        net = psutil.net_io_counters()
        up_speed = (net.bytes_sent - self.net_io_counters.bytes_sent) / delta
        down_speed = (net.bytes_recv - self.net_io_counters.bytes_recv) / delta
        self.net_io_counters = net
        
        # Disk IO Speed
        disk_io = psutil.disk_io_counters()
        read_speed = (disk_io.read_bytes - self.disk_io_counters.read_bytes) / delta
        write_speed = (disk_io.write_bytes - self.disk_io_counters.write_bytes) / delta
        self.disk_io_counters = disk_io
        
        # GPU
        gpu = self.get_gpu_info()
        
        return {
            "cpu": {"total": cpu_pct, "cores": cpu_per_core, "load": load_avg},
            "mem": {"percent": mem.percent, "used": mem.used, "total": mem.total},
            "swap": {"percent": swap.percent, "used": swap.used, "total": swap.total},
            "disk": {"percent": disk.percent, "used": disk.used, "total": disk.total},
            "net": {"up": up_speed, "down": down_speed},
            "io": {"read": read_speed, "write": write_speed},
            "gpu": gpu
        }

    def format_bytes(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _generate_cpu_table(self, metrics):
        """生成 CPU/GPU 详情表"""
        table = Table(box=box.SIMPLE, show_header=False, expand=True)
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Bar", ratio=2)
        
        # CPU Total
        cpu_color = "green" if metrics['cpu']['total'] < 60 else "yellow" if metrics['cpu']['total'] < 85 else "red"
        table.add_row(
            "💻 CPU 总计", 
            f"{metrics['cpu']['total']:.1f}%", 
            Text("█" * int(metrics['cpu']['total'] / 5), style=cpu_color)
        )
        
        # Load Avg
        table.add_row(
            "⚖️  平均负载", 
            f"{metrics['cpu']['load'][0]:.2f} / {metrics['cpu']['load'][1]:.2f} / {metrics['cpu']['load'][2]:.2f}", 
            ""
        )
        
        # GPU
        gpu = metrics['gpu']
        if gpu['auth']:
            gpu_color = "magenta"
            table.add_row(
                "🎮 GPU 使用", 
                f"{gpu['usage']:.1f}%", 
                Text("█" * int(gpu['usage'] / 5), style=gpu_color)
            )
            table.add_row("⚡ GPU 功耗", f"{gpu['power']}", "")
        else:
            table.add_row("🎮 GPU", "[dim]需要 sudo[/dim]", "")
            
        return Panel(table, title="计算资源 (Compute)", border_style="blue")

    def _generate_mem_table(self, metrics):
        """生成内存/磁盘详情表"""
        table = Table(box=box.SIMPLE, show_header=False, expand=True)
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="white")
        
        # Memory
        mem = metrics['mem']
        mem_color = "green" if mem['percent'] < 80 else "yellow"
        table.add_row(
            "🧠 物理内存", 
            f"{mem['percent']}% ({self.format_bytes(mem['used'])}/{self.format_bytes(mem['total'])})"
        )
        
        # Swap
        swap = metrics['swap']
        if swap['total'] > 0:
            table.add_row(
                "💱 交换空间", 
                f"{swap['percent']}% ({self.format_bytes(swap['used'])})"
            )
            
        # Disk
        disk = metrics['disk']
        table.add_row(
            "💿 磁盘空间", 
            f"{disk['percent']}% ({self.format_bytes(disk['used'])})"
        )
        
        return Panel(table, title="存储资源 (Storage)", border_style="green")

    def _generate_io_table(self, metrics):
        """生成网络/IO详情表"""
        table = Table(box=box.SIMPLE, show_header=False, expand=True)
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="white")
        
        net = metrics['net']
        io = metrics['io']
        
        table.add_row("🌐 上传速度", f"↑ {self.format_bytes(net['up'])}/s")
        table.add_row("🌐 下载速度", f"↓ {self.format_bytes(net['down'])}/s")
        table.add_row("💿 读取速度", f"R: {self.format_bytes(io['read'])}/s")
        table.add_row("💿 写入速度", f"W: {self.format_bytes(io['write'])}/s")
        
        return Panel(table, title="I/O 吞吐 (Throughput)", border_style="yellow")

    def _generate_process_table(self):
        """生成进程监控表"""
        table = Table(expand=True, box=box.MINIMAL_HEAVY_HEAD, border_style="bright_black")
        table.add_column("PID", width=6, style="dim")
        table.add_column("Process Name", ratio=3)
        table.add_column("CPU", width=8, justify="right")
        table.add_column("MEM", width=10, justify="right")
        table.add_column("Status", width=10)

        rag_procs = self.get_rag_processes()
        if not rag_procs:
            table.add_row("-", "[dim]暂无 RAG 相关进程活跃[/dim]", "-", "-", "-")
        else:
            for p in rag_procs[:10]: # 只显示前10个
                try:
                    cpu = p.info['cpu_percent']
                    mem = p.memory_info().rss
                    
                    # 样式高亮
                    name_style = "bold white"
                    if "streamlit" in p.info['name'].lower():
                        name_style = "bold red"
                    elif "ollama" in p.info['name'].lower():
                        name_style = "bold cyan"
                        
                    cpu_style = "green" if cpu < 50 else "red"
                    
                    table.add_row(
                        str(p.info['pid']),
                        Text(p.info['name'], style=name_style),
                        Text(f"{cpu:.1f}%", style=cpu_style),
                        self.format_bytes(mem),
                        p.info['status']
                    )
                except:
                    continue
                
        return Panel(table, title="🚀 核心服务监控 (RAG Core Services)", border_style="red")

    def run(self):
        """启动监控循环"""
        # 初始化 CPU 计数 (第一次调用通常为 0)
        psutil.cpu_percent()
        
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_column(
            Layout(name="upper", size=10),
            Layout(name="lower")
        )
        
        layout["upper"].split_row(
            Layout(name="cpu"),
            Layout(name="mem"),
            Layout(name="io")
        )
        
        with Live(layout, refresh_per_second=1, screen=True) as live:
            try:
                while True:
                    metrics = self.get_metrics()
                    
                    # Header
                    uptime = timedelta(seconds=int(time.time() - psutil.boot_time()))
                    header_text = f"RAG Pro Max System Monitor | 🕒 {datetime.now().strftime('%H:%M:%S')} | ⏱️  Uptime: {uptime}"
                    
                    # Battery Info
                    battery = psutil.sensors_battery()
                    if battery:
                        plugged = "⚡" if battery.power_plugged else "🔋"
                        header_text += f" | {plugged} {battery.percent}%"
                        if not battery.power_plugged:
                            header_text += f" ({timedelta(seconds=battery.secsleft)})"

                    if not metrics['gpu']['auth']:
                        header_text += " | ⚠️  Sudo Required for Full GPU Info"
                        
                    layout["header"].update(Panel(Align.center(header_text, vertical="middle"), style="bold white on blue"))
                    
                    # Upper Section (Resources)
                    layout["cpu"].update(self._generate_cpu_table(metrics))
                    layout["mem"].update(self._generate_mem_table(metrics))
                    layout["io"].update(self._generate_io_table(metrics))
                    
                    # Lower Section (Processes)
                    layout["lower"].update(self._generate_process_table())
                    
                    # Footer
                    layout["footer"].update(Align.center("[bold]Ctrl+C[/bold] to Exit", vertical="middle"))
                    
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                pass

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()