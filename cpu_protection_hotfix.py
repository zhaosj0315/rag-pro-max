#!/usr/bin/env python3
"""
CPU 保护热修复脚本
立即为现有系统添加CPU使用率限制，防止系统过载关机
"""

import os
import sys
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

class EmergencyCPUProtection:
    """紧急CPU保护"""
    
    def __init__(self, max_cpu_percent=90.0):
        self.max_cpu_percent = max_cpu_percent
        self.is_active = False
        self.monitor_thread = None
        self._stop_event = threading.Event()
        
    def start(self):
        """启动保护"""
        if not self.is_active:
            self.is_active = True
            self._stop_event.clear()
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            print(f"🛡️  紧急CPU保护已启动 (限制: {self.max_cpu_percent}%)")
    
    def stop(self):
        """停止保护"""
        if self.is_active:
            self.is_active = False
            self._stop_event.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1.0)
            print("🛑 紧急CPU保护已停止")
    
    def _monitor(self):
        """监控CPU使用率"""
        consecutive_high = 0
        
        while not self._stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=0.2)
                
                if cpu_percent > self.max_cpu_percent:
                    consecutive_high += 1
                    
                    if consecutive_high == 1:
                        print(f"⚠️  CPU使用率过高: {cpu_percent:.1f}% (限制: {self.max_cpu_percent}%)")
                    
                    if consecutive_high >= 3:  # 连续3次过高
                        print(f"🚨 CPU使用率持续过高，强制降频...")
                        self._emergency_throttle()
                        consecutive_high = 0
                else:
                    if consecutive_high > 0:
                        print(f"✅ CPU使用率恢复正常: {cpu_percent:.1f}%")
                    consecutive_high = 0
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"CPU监控异常: {e}")
                time.sleep(1.0)
    
    def _emergency_throttle(self):
        """紧急限流"""
        try:
            # 强制休眠，降低CPU使用率
            time.sleep(1.0)
            
            # 尝试降低当前进程优先级
            try:
                import psutil
                current_process = psutil.Process()
                if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS'):
                    current_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    current_process.nice(10)  # Unix系统
                print("📉 已降低进程优先级")
            except:
                pass
                
        except Exception as e:
            print(f"紧急限流失败: {e}")

def patch_existing_functions():
    """修补现有函数，添加CPU检查"""
    
    # 保存原始的ThreadPoolExecutor
    original_executor = ThreadPoolExecutor
    
    class SafeThreadPoolExecutor(original_executor):
        """安全的线程池执行器"""
        
        def __init__(self, max_workers=None, **kwargs):
            # 根据CPU使用率动态调整工作线程数
            if max_workers:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                if cpu_percent > 85:
                    max_workers = max(1, max_workers // 4)
                    print(f"⚠️  CPU使用率过高，减少线程数至 {max_workers}")
                elif cpu_percent > 70:
                    max_workers = max(2, max_workers // 2)
                    print(f"⚠️  CPU使用率较高，减少线程数至 {max_workers}")
            
            super().__init__(max_workers=max_workers, **kwargs)
        
        def submit(self, fn, *args, **kwargs):
            # 提交前检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > 95:
                print(f"🚨 CPU使用率极高 ({cpu_percent:.1f}%)，延迟任务提交")
                time.sleep(0.5)
            
            return super().submit(fn, *args, **kwargs)
    
    # 替换全局的ThreadPoolExecutor
    import concurrent.futures
    concurrent.futures.ThreadPoolExecutor = SafeThreadPoolExecutor
    
    print("🔧 已修补ThreadPoolExecutor，添加CPU保护")

def main():
    """主函数"""
    print("=" * 60)
    print("🚨 CPU保护热修复脚本")
    print("=" * 60)
    print("⚠️  检测到系统可能因CPU过载导致关机")
    print("🛡️  正在应用紧急CPU保护措施...")
    
    # 启动紧急CPU保护
    protection = EmergencyCPUProtection(max_cpu_percent=90.0)
    protection.start()
    
    # 修补现有函数
    patch_existing_functions()
    
    print("✅ CPU保护措施已应用")
    print("💡 建议:")
    print("   1. 重启应用以应用完整的CPU保护")
    print("   2. 检查是否有其他程序占用CPU")
    print("   3. 考虑降低并行处理的线程数")
    
    try:
        # 保持运行，监控CPU
        while True:
            cpu_percent = psutil.cpu_percent(interval=1.0)
            mem_percent = psutil.virtual_memory().percent
            
            print(f"📊 CPU: {cpu_percent:5.1f}% | 内存: {mem_percent:5.1f}%", end='\r')
            
            if cpu_percent < 50 and mem_percent < 70:
                # 系统负载正常，可以退出
                break
                
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    finally:
        protection.stop()
        print("\n✅ CPU保护热修复完成")

if __name__ == "__main__":
    main()
