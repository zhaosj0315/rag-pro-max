#!/usr/bin/env python3
"""统一系统监控工具 - CPU/GPU/内存/磁盘/网络/电池"""
import psutil
import time
import sys
import subprocess
from datetime import datetime, timedelta

def get_gpu_info():
    """获取 Apple Silicon GPU 信息"""
    try:
        result = subprocess.run(
            ['sudo', 'powermetrics', '--samplers', 'gpu_power', '-i', '500', '-n', '1'],
            capture_output=True, text=True, timeout=3
        )
        
        if result.returncode != 0:
            return {'usage': 0.0, 'freq': 'N/A', 'power': 'N/A'}
        
        lines = result.stdout.split('\n')
        
        # 提取使用率（active residency）
        usage = 0.0
        for line in lines:
            if 'GPU HW active residency:' in line:
                # 提取百分比，格式: "GPU HW active residency: 100.00%"
                parts = line.split(':')
                if len(parts) >= 2:
                    percent_str = parts[1].strip().split('%')[0].strip()
                    try:
                        usage = float(percent_str)
                    except:
                        pass
                break
        
        # 提取频率
        freq = 'N/A'
        for line in lines:
            if 'GPU HW active frequency:' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    freq = parts[1].strip()
                break
        
        # 提取功耗
        power = 'N/A'
        for line in lines:
            if 'GPU Power:' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    power = parts[1].strip()
                break
        
        return {'usage': usage, 'freq': freq, 'power': power}
    except Exception as e:
        return {'usage': 0.0, 'freq': 'N/A', 'power': 'N/A'}

def get_streamlit_process():
    """获取 Streamlit 进程"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'num_threads']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'streamlit run' in cmdline and 'apppro.py' in cmdline:
                return proc
        except:
            continue
    return None

from src.common.utils import format_bytes

def format_bar(percent, width=20, bar_type='cpu'):
    """格式化进度条"""
    filled = int(width * min(percent, 100) / 100)
    bar = '█' * filled + '░' * (width - filled)
    
    # 根据类型和使用率着色
    if bar_type == 'memory':
        color = '\033[93m'  # 黄色
    elif bar_type == 'disk':
        color = '\033[96m'  # 青色
    elif bar_type == 'gpu':
        color = '\033[95m'  # 紫色
    elif bar_type == 'swap':
        color = '\033[91m' if percent > 50 else '\033[93m'  # 红色/黄色
    elif bar_type == 'battery':
        if percent > 50:
            color = '\033[92m'  # 绿色
        elif percent > 20:
            color = '\033[93m'  # 黄色
        else:
            color = '\033[91m'  # 红色
    elif percent >= 90:
        color = '\033[91m'  # 红色
    else:
        color = '\033[92m'  # 绿色
    
    reset = '\033[0m'
    return f"{color}{bar}{reset}"

def format_uptime(seconds):
    """格式化运行时间"""
    td = timedelta(seconds=int(seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}天 {hours}小时 {minutes}分钟"
    elif hours > 0:
        return f"{hours}小时 {minutes}分钟"
    else:
        return f"{minutes}分钟"

def monitor():
    """实时监控"""
    last_net_io = psutil.net_io_counters()
    last_disk_io = psutil.disk_io_counters()
    last_time = time.time()
    
    try:
        while True:
            sys.stdout.write('\033[2J\033[H')  # 清屏
            now = datetime.now().strftime('%H:%M:%S')
            
            # 系统运行时间
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            uptime_str = format_uptime(uptime)
            
            print("=" * 80)
            print(f"⏰ 时间: {now} | ⏱️  运行时间: {uptime_str}")
            print("=" * 80)
            
            # 电池状态（笔记本才有）
            battery = psutil.sensors_battery()
            if battery:
                charging = "充电中" if battery.power_plugged else "使用电池"
                secs_left = battery.secsleft
                if secs_left > 0:
                    time_left = format_uptime(secs_left)
                    print(f"\n🔋 电池: {battery.percent:.0f}% ({charging}) | 剩余: {time_left}")
                else:
                    print(f"\n🔋 电池: {battery.percent:.0f}% ({charging})")
                print(f"   {format_bar(battery.percent, bar_type='battery')} {battery.percent:.0f}%")
            
            # CPU 信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)
            cores_used = cpu_percent / 100 * cpu_count
            
            print(f"\n💻 CPU 使用率: {cpu_percent:5.1f}% ({cores_used:.1f}/{cpu_count} 核)")
            print(f"   {format_bar(cpu_percent)} {cpu_percent:.1f}%")
            
            # CPU 每核
            print(f"\n   各核心使用率:")
            for i in range(0, len(cpu_per_core), 4):
                cores = cpu_per_core[i:i+4]
                line = "   "
                for j, usage in enumerate(cores):
                    bar = format_bar(usage, width=10)
                    line += f"核{i+j:2d}: {bar} {usage:5.1f}%  "
                print(line)
            
            # GPU 信息
            gpu = get_gpu_info()
            if gpu['freq'] != 'N/A':
                print(f"\n🎮 GPU 使用率: {gpu['usage']:5.1f}% (32 核) | 频率: {gpu['freq']} | 功耗: {gpu['power']}")
                print(f"   {format_bar(gpu['usage'], bar_type='gpu')} {gpu['usage']:.1f}%")
            else:
                print(f"\n🎮 GPU 使用率: 需要 sudo 权限获取详细信息")
                print(f"   提示: 使用 'sudo python3 system_monitor.py' 运行")
            
            # 内存信息
            mem = psutil.virtual_memory()
            print(f"\n💾 内存使用: {mem.percent:5.1f}% ({format_bytes(mem.used)}/{format_bytes(mem.total)})")
            print(f"   {format_bar(mem.percent, bar_type='memory')} {mem.percent:.1f}%")
            
            # Swap 信息
            swap = psutil.swap_memory()
            if swap.total > 0:
                print(f"\n💱 交换内存: {swap.percent:5.1f}% ({format_bytes(swap.used)}/{format_bytes(swap.total)})")
                print(f"   {format_bar(swap.percent, bar_type='swap')} {swap.percent:.1f}%")
            
            # 磁盘信息（使用数据分区）
            try:
                disk = psutil.disk_usage('/System/Volumes/Data')
            except:
                disk = psutil.disk_usage('/')
            print(f"\n💿 磁盘使用: {disk.percent:5.1f}% ({format_bytes(disk.used)}/{format_bytes(disk.total)})")
            print(f"   {format_bar(disk.percent, bar_type='disk')} {disk.percent:.1f}%")
            
            # 磁盘 I/O 速度
            current_disk_io = psutil.disk_io_counters()
            current_time = time.time()
            time_delta = current_time - last_time
            
            read_speed = (current_disk_io.read_bytes - last_disk_io.read_bytes) / time_delta / 1024 / 1024  # MB/s
            write_speed = (current_disk_io.write_bytes - last_disk_io.write_bytes) / time_delta / 1024 / 1024  # MB/s
            
            print(f"\n💿 磁盘 I/O: 读 {read_speed:.2f} MB/s | 写 {write_speed:.2f} MB/s")
            
            # 网络流量
            current_net_io = psutil.net_io_counters()
            
            upload_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_delta / 1024 / 1024  # MB/s
            download_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_delta / 1024 / 1024  # MB/s
            
            print(f"\n🌐 网络流量: ↑ {upload_speed:.2f} MB/s | ↓ {download_speed:.2f} MB/s")
            
            last_net_io = current_net_io
            last_disk_io = current_disk_io
            last_time = current_time
            
            # Streamlit 进程
            proc = get_streamlit_process()
            if proc:
                try:
                    cpu = proc.cpu_percent()
                    mem_rss = proc.memory_info().rss
                    threads = proc.num_threads()
                    
                    print(f"\n🔍 Streamlit 进程: PID {proc.pid} | CPU {cpu:.1f}% | 内存 {format_bytes(mem_rss)} | 线程 {threads}")
                    if cpu > 100:
                        print(f"   🚀 多核运行: {cpu/100:.1f} 核并行")
                except:
                    pass
            
            print("\n" + "=" * 80)
            if gpu['freq'] == 'N/A':
                print("💡 提示: 使用 'sudo python3 system_monitor.py' 获取 GPU 详细信息")
            print("按 Ctrl+C 退出监控")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")
        sys.exit(0)

if __name__ == "__main__":
    monitor()
