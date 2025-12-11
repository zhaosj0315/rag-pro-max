#!/usr/bin/env python3
"""
OCR性能实时监控工具
监控OCR处理过程中的CPU和内存使用情况
"""

import psutil
import time
import threading
from datetime import datetime

class OCRMonitor:
    """OCR性能监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = []
        
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.stats = []
        
        def monitor_loop():
            while self.monitoring:
                try:
                    # 获取系统状态
                    cpu_percent = psutil.cpu_percent(interval=0.5)
                    memory = psutil.virtual_memory()
                    
                    # 获取各核心使用率
                    cpu_per_core = psutil.cpu_percent(percpu=True, interval=0.1)
                    
                    # 记录统计
                    stat = {
                        'time': datetime.now(),
                        'cpu_total': cpu_percent,
                        'cpu_cores': cpu_per_core,
                        'memory_percent': memory.percent,
                        'memory_used_gb': memory.used / (1024**3)
                    }
                    self.stats.append(stat)
                    
                    # 实时显示
                    self.print_realtime_stats(stat)
                    
                except Exception as e:
                    print(f"监控错误: {e}")
                    
                time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔍 开始OCR性能监控...")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)
        print("\n⏹️  停止OCR性能监控")
        
    def print_realtime_stats(self, stat):
        """打印实时统计"""
        # 清屏并移动到顶部
        print("\033[2J\033[H", end="")
        
        print("=" * 60)
        print(f"🔍 OCR性能监控 - {stat['time'].strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # CPU总使用率
        cpu_bar = "█" * int(stat['cpu_total'] / 5) + "░" * (20 - int(stat['cpu_total'] / 5))
        print(f"💻 CPU总使用率: {stat['cpu_total']:5.1f}% [{cpu_bar}]")
        
        # 各核心使用率
        print("\n   各核心使用率:")
        cores_per_row = 4
        for i in range(0, len(stat['cpu_cores']), cores_per_row):
            row_cores = stat['cpu_cores'][i:i+cores_per_row]
            row_str = ""
            for j, core_usage in enumerate(row_cores):
                core_num = i + j
                bar = "█" * int(core_usage / 10) + "░" * (10 - int(core_usage / 10))
                row_str += f"核{core_num:2d}: {bar} {core_usage:5.1f}%  "
            print(f"   {row_str}")
        
        # 内存使用率
        mem_bar = "█" * int(stat['memory_percent'] / 5) + "░" * (20 - int(stat['memory_percent'] / 5))
        print(f"\n💾 内存使用率: {stat['memory_percent']:5.1f}% [{mem_bar}] ({stat['memory_used_gb']:.1f}GB)")
        
        # 性能建议
        print(f"\n📊 性能分析:")
        if stat['cpu_total'] < 30:
            print("   ✅ CPU负载较低，可以增加OCR进程数")
        elif stat['cpu_total'] < 70:
            print("   ⚡ CPU负载适中，当前配置合理")
        else:
            print("   ⚠️  CPU负载较高，建议减少进程数")
            
        if stat['memory_percent'] > 80:
            print("   ⚠️  内存使用率过高，可能影响性能")
        
        # 活跃核心统计
        active_cores = sum(1 for usage in stat['cpu_cores'] if usage > 10)
        total_cores = len(stat['cpu_cores'])
        print(f"   🔥 活跃核心: {active_cores}/{total_cores} ({active_cores/total_cores*100:.0f}%)")
        
        print("\n按 Ctrl+C 停止监控")
    
    def print_summary(self):
        """打印监控总结"""
        if not self.stats:
            print("没有监控数据")
            return
            
        print("\n" + "=" * 60)
        print("📊 OCR性能监控总结")
        print("=" * 60)
        
        # 计算平均值
        avg_cpu = sum(s['cpu_total'] for s in self.stats) / len(self.stats)
        max_cpu = max(s['cpu_total'] for s in self.stats)
        avg_memory = sum(s['memory_percent'] for s in self.stats) / len(self.stats)
        max_memory = max(s['memory_percent'] for s in self.stats)
        
        print(f"⏱️  监控时长: {len(self.stats)} 秒")
        print(f"💻 CPU使用率: 平均 {avg_cpu:.1f}%, 峰值 {max_cpu:.1f}%")
        print(f"💾 内存使用率: 平均 {avg_memory:.1f}%, 峰值 {max_memory:.1f}%")
        
        # 核心利用率分析
        if self.stats:
            last_stat = self.stats[-1]
            active_cores = sum(1 for usage in last_stat['cpu_cores'] if usage > 10)
            total_cores = len(last_stat['cpu_cores'])
            print(f"🔥 核心利用率: {active_cores}/{total_cores} ({active_cores/total_cores*100:.0f}%)")
        
        # 性能评估
        if avg_cpu < 30:
            print("✅ 整体性能: CPU资源充足，可以提高并发")
        elif avg_cpu < 70:
            print("⚡ 整体性能: 资源利用合理")
        else:
            print("⚠️  整体性能: CPU负载较高")

def main():
    """主函数"""
    monitor = OCRMonitor()
    
    try:
        monitor.start_monitoring()
        
        # 保持监控运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        monitor.print_summary()

if __name__ == "__main__":
    main()
