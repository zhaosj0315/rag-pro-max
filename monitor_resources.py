#!/usr/bin/env python3
"""
RAG Pro Max 实时资源监控
监控CPU、内存、GPU使用情况
"""

import psutil
import time
import os
import subprocess
from datetime import datetime

def get_gpu_info():
    """获取GPU信息"""
    try:
        # 尝试获取GPU信息
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                               '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpu_info = []
            for line in lines:
                parts = line.split(', ')
                if len(parts) >= 3:
                    gpu_info.append({
                        'utilization': int(parts[0]),
                        'memory_used': int(parts[1]),
                        'memory_total': int(parts[2])
                    })
            return gpu_info
    except:
        pass
    
    # 如果是Mac，尝试获取MPS信息
    try:
        import torch
        if torch.backends.mps.is_available():
            return [{'type': 'MPS', 'available': True}]
    except:
        pass
    
    return []

def get_rag_processes():
    """获取RAG相关进程"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if any(keyword in proc.info['name'].lower() for keyword in ['python', 'streamlit', 'uvicorn']):
                # 检查命令行参数
                cmdline = ' '.join(proc.cmdline())
                if any(keyword in cmdline.lower() for keyword in ['rag', 'apppro', 'streamlit']):
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent']
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def format_bytes(bytes_value):
    """格式化字节数"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}TB"

def monitor_resources():
    """监控资源使用"""
    print("🔍 RAG Pro Max 资源监控器")
    print("=" * 60)
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            # 清屏
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # 时间戳
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"🕐 {now}")
            print("=" * 60)
            
            # CPU信息
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_avg = sum(cpu_percent) / len(cpu_percent)
            
            print(f"💻 CPU: {cpu_count}核心")
            print(f"   平均使用率: {cpu_avg:.1f}%")
            print(f"   各核心: {' '.join([f'{c:.0f}%' for c in cpu_percent])}")
            
            # 内存信息
            memory = psutil.virtual_memory()
            print(f"\n💾 内存:")
            print(f"   总计: {format_bytes(memory.total)}")
            print(f"   已用: {format_bytes(memory.used)} ({memory.percent:.1f}%)")
            print(f"   可用: {format_bytes(memory.available)}")
            
            # GPU信息
            gpu_info = get_gpu_info()
            if gpu_info:
                print(f"\n🎮 GPU:")
                for i, gpu in enumerate(gpu_info):
                    if 'type' in gpu:
                        print(f"   GPU {i}: {gpu['type']} - 可用")
                    else:
                        mem_percent = (gpu['memory_used'] / gpu['memory_total']) * 100
                        print(f"   GPU {i}: {gpu['utilization']}% | 显存: {gpu['memory_used']}MB/{gpu['memory_total']}MB ({mem_percent:.1f}%)")
            else:
                print(f"\n🎮 GPU: 未检测到或不可用")
            
            # RAG进程信息
            rag_processes = get_rag_processes()
            if rag_processes:
                print(f"\n🚀 RAG 进程:")
                for proc in rag_processes:
                    print(f"   PID {proc['pid']}: {proc['name']} - CPU: {proc['cpu']:.1f}% | 内存: {proc['memory']:.1f}%")
            else:
                print(f"\n🚀 RAG 进程: 未运行")
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            print(f"\n💿 磁盘:")
            print(f"   总计: {format_bytes(disk.total)}")
            print(f"   已用: {format_bytes(disk.used)} ({disk.used/disk.total*100:.1f}%)")
            print(f"   可用: {format_bytes(disk.free)}")
            
            # 网络信息
            net_io = psutil.net_io_counters()
            print(f"\n🌐 网络:")
            print(f"   发送: {format_bytes(net_io.bytes_sent)}")
            print(f"   接收: {format_bytes(net_io.bytes_recv)}")
            
            print("\n" + "=" * 60)
            print("💡 提示: 观察CPU使用率是否充分利用多核")
            print("📊 理想状态: 处理时CPU应该接近80%，多核均匀分布")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 监控已停止")

if __name__ == '__main__':
    monitor_resources()
