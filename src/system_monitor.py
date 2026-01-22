#!/usr/bin/env python3
"""
RAG Pro Max 系统监控大屏 v3.0
------------------------------------------------
优化布局：全宽度核心展示，消除进度条截断。
"""

import os
import sys
import time
import psutil
import subprocess
from datetime import datetime, timedelta
from collections import deque

# 自动处理路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from rich.console import Console, Group
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich import box
except ImportError:
    print("❌ 错误: 缺少 'rich' 库。请运行: pip install rich")
    sys.exit(1)

from src.app_logging.log_manager import LogManager
logger = LogManager(enable_terminal=False)

class SystemMonitor:
    def __init__(self):
        self.console = Console()
        self.net_io = psutil.net_io_counters()
        self.disk_io = psutil.disk_io_counters()
        self.last_time = time.time()

    def get_apple_silicon_stats(self):
        try:
            # 增加 ane_power 和 thermal 采样
            result = subprocess.run(
                ['sudo', 'powermetrics', '--samplers', 'cpu_power,gpu_power,ane_power,thermal', '-i', '200', '-n', '1'],
                capture_output=True, text=True, timeout=1
            )
            if result.returncode != 0: return {'gpu_usage': 0.0, 'ane_usage': 0.0, 'total_p': 'N/A', 'auth': False}
            lines = result.stdout.split('\n')
            gpu_usage, ane_usage = 0.0, 0.0
            total_p = '0 mW'
            thermal_level = "Normal"
            
            for line in lines:
                if 'GPU HW active residency:' in line:
                    gpu_usage = float(line.split(':')[1].strip().split('%')[0])
                elif 'ANE HW active residency:' in line:
                    ane_usage = float(line.split(':')[1].strip().split('%')[0])
                elif 'Combined Power' in line: total_p = line.split(':')[1].strip()
                elif 'Thermal pressure:' in line: thermal_level = line.split(':')[1].strip()
            
            return {
                'gpu_usage': gpu_usage, 'ane_usage': ane_usage,
                'total_p': total_p, 'thermal': thermal_level, 'auth': True
            }
        except:
            return {'gpu_usage': 0.0, 'ane_usage': 0.0, 'total_p': 'N/A', 'auth': False}

    def format_bytes(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024: return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def make_bar(self, pct, color="green", width=15):
        filled = int((pct / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return Text(bar, style=color)

    def _gen_cpu_summary(self, metrics):
        table = Table(box=None, show_header=False, expand=True)
        table.add_column("L", width=15); table.add_column("V", width=10); table.add_column("B", ratio=1)
        
        cpu_pct = metrics['cpu']['total']
        color = "green" if cpu_pct < 60 else "yellow" if cpu_pct < 85 else "red"
        table.add_row("💻 CPU 总利用率", f"{cpu_pct:>5.1f}%", self.make_bar(cpu_pct, color))
        
        stats = metrics['apple']
        if stats['auth']:
            table.add_row("🎮 GPU 核心使用", f"{stats['gpu_usage']:>5.1f}%", self.make_bar(stats['gpu_usage'], "magenta"))
            table.add_row("🧠 ANE (AI加速)", f"{stats['ane_usage']:>5.1f}%", self.make_bar(stats['ane_usage'], "bright_magenta"))
            table.add_row("🔥 热态压力", stats['thermal'], "")
        else:
            table.add_row("🎮 GPU/ANE", "[dim]Need sudo[/dim]", "")
            
        load = metrics['cpu']['load']
        table.add_row("⚖️  平均负载", f"{load[0]:.2f} / {load[1]:.2f}", "[dim]1/5 min[/dim]")
        return Panel(table, title="[bold blue]计算资源 (Compute)[/]", border_style="blue")

    def _gen_mem_summary(self, metrics):
        table = Table(box=None, show_header=False, expand=True)
        # 调整宽度：L(标签) 12, V(数值) 18, B(进度条) 剩余
        table.add_column("L", width=12); table.add_column("V", width=18); table.add_column("B", ratio=1)
        
        mem = metrics['mem']
        table.add_row("🧠 物理内存", f"{self.format_bytes(mem['used'])}/{self.format_bytes(mem['total'])}", self.make_bar(mem['percent'], "green"))
        swap = metrics['swap']
        if swap['total'] > 0:
            table.add_row("💱 交换空间", f"{self.format_bytes(swap['used'])}/{self.format_bytes(swap['total'])}", self.make_bar(swap['percent'], "yellow"))
        disk = metrics['disk']
        table.add_row("💿 磁盘空间", f"{self.format_bytes(disk['used'])}/{self.format_bytes(disk['total'])}", self.make_bar(disk['percent'], "cyan"))
        return Panel(table, title="[bold green]存储资源 (Storage)[/]", border_style="green")

    def _gen_cores_grid(self, metrics):
        cores = metrics['cpu']['cores']
        cols = 4
        table = Table(box=None, show_header=False, expand=True, padding=(0,0))
        for _ in range(cols): table.add_column(ratio=1, no_wrap=True)
        
        for i in range(0, len(cores), cols):
            row = []
            for j in range(cols):
                idx = i + j
                if idx < len(cores):
                    u = cores[idx]
                    is_pcore = idx < 10
                    # 更加丰富的颜色梯度
                    if u > 85: color = "bold red"
                    elif u > 60: color = "bold yellow"
                    elif u > 30: color = "bright_cyan" if is_pcore else "cyan"
                    else: color = "bright_green" if is_pcore else "green"
                    
                    label = "P" if is_pcore else "E"
                    bar_len = 7 
                    filled = int((u / 100) * bar_len)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    
                    # 精简格式: "00P █░░ 10%"
                    core_text = Text.assemble(
                        (f"{idx:2d}{label} ", "dim"),
                        (bar, color),
                        (f" {u:>3.0f}%", "white")
                    )
                    row.append(core_text)
                else: row.append("")
            table.add_row(*row)
        return Panel(table, title="[bold cyan]14-Core CPU (P:性能核 | E:能效核)[/]", border_style="cyan")

    def _gen_io_panel(self, metrics):
        table = Table(box=None, show_header=False, expand=True)
        for _ in range(3): table.add_column(ratio=1)
        net, io, stats = metrics['net'], metrics['io'], metrics['apple']
        table.add_row(f"🌐 Net: ↑{self.format_bytes(net['up'])} ↓{self.format_bytes(net['down'])}",
                      f"💿 Disk: R{self.format_bytes(io['read'])} W{self.format_bytes(io['write'])}",
                      f"⚡ Total Power: [bold yellow]{stats.get('total_p', 'N/A')}[/]")
        return Panel(table, title="[bold yellow]实时 I/O 与 功耗[/]", border_style="yellow")

    def _gen_process_table(self):
        table = Table(expand=True, box=box.MINIMAL_HEAVY_HEAD, border_style="bright_black")
        table.add_column("PID", width=8); table.add_column("Process", ratio=3); table.add_column("CPU", width=10, justify="right")
        table.add_column("MEM", width=12, justify="right"); table.add_column("Status", width=10)
        
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                if p.info['cpu_percent'] > 0.1 or 'ollama' in p.info['name'].lower() or 'python' in p.info['name'].lower():
                    procs.append(p.info)
            except: continue
        
        for p in sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:6]:
            color = "red" if p['cpu_percent'] > 50 else "white"
            table.add_row(str(p['pid']), p['name'], f"{p['cpu_percent']:.1f}%", self.format_bytes(p['memory_info'].rss), p['status'], style=color)
        return Panel(table, title="[bold red]核心进程监控[/]", border_style="red")

    def run(self):
        psutil.cpu_percent()
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="top", size=8),
            Layout(name="cores", size=7),
            Layout(name="io", size=3),
            Layout(name="proc", ratio=1)
        )
        layout["top"].split_row(Layout(name="cpu_sum"), Layout(name="mem_sum"))

        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                now = time.time(); delta = now - self.last_time; self.last_time = now
                cpu_p = psutil.cpu_percent(percpu=True); cpu_t = psutil.cpu_percent()
                mem = psutil.virtual_memory(); swap = psutil.swap_memory()
                net_now = psutil.net_io_counters(); disk_now = psutil.disk_io_counters()

                # 优先获取用户数据卷的真实占用
                try:
                    # 在 macOS 上，项目所在的路径通常就在 Data 卷上
                    disk_usage = psutil.disk_usage(os.getcwd())
                except:
                    disk_usage = psutil.disk_usage('/')

                metrics = {
                    "cpu": {"total": cpu_t, "cores": cpu_p, "load": psutil.getloadavg()},
                    "apple": self.get_apple_silicon_stats(),
                    "mem": {"percent": mem.percent, "total": mem.total, "used": mem.used},
                    "swap": {"percent": swap.percent, "total": swap.total, "used": swap.used},
                    "disk": {"percent": disk_usage.percent, "total": disk_usage.total, "used": disk_usage.used},
                    "net": {"up": (net_now.bytes_sent - self.net_io.bytes_sent)/delta, "down": (net_now.bytes_recv - self.net_io.bytes_recv)/delta},
                    "io": {"read": (disk_now.read_bytes - self.disk_io.read_bytes)/delta, "write": (disk_now.write_bytes - self.disk_io.write_bytes)/delta}
                }
                self.net_io, self.disk_io = net_now, disk_now
                
                # Header
                bat = psutil.sensors_battery()
                bat_str = f" | 🔋 {bat.percent}%" if bat else ""
                layout["header"].update(Panel(Align.center(f"RAG Pro Max Monitor | {datetime.now().strftime('%H:%M:%S')}{bat_str}", vertical="middle"), style="bold white on blue"))
                
                layout["cpu_sum"].update(self._gen_cpu_summary(metrics))
                layout["mem_sum"].update(self._gen_mem_summary(metrics))
                layout["cores"].update(self._gen_cores_grid(metrics))
                layout["io"].update(self._gen_io_panel(metrics))
                layout["proc"].update(self._gen_process_table())
                time.sleep(1)

if __name__ == "__main__":
    SystemMonitor().run()
