#!/usr/bin/env python3
"""
强制触发批量OCR处理
"""

def trigger_batch_ocr():
    """强制触发批量OCR处理"""
    try:
        from src.utils.batch_ocr_processor import batch_ocr_processor
        
        print(f"🔍 检查OCR任务队列...")
        print(f"📋 当前队列中有 {len(batch_ocr_processor.ocr_tasks)} 个OCR任务")
        
        if batch_ocr_processor.ocr_tasks:
            print(f"🚀 强制启动批量OCR处理...")
            
            # 显示任务统计
            task_files = {}
            for task in batch_ocr_processor.ocr_tasks:
                task_id = task['task_id']
                if task_id not in task_files:
                    task_files[task_id] = 0
                task_files[task_id] += 1
            
            print(f"📊 任务分布:")
            for task_id, count in task_files.items():
                print(f"   {task_id[:8]}: {count}页")
            
            # 强制处理
            results = batch_ocr_processor.process_all_ocr_tasks()
            
            print(f"✅ 批量OCR处理完成!")
            print(f"📈 处理了 {len(results)} 个文件的OCR任务")
            
        else:
            print("ℹ️  OCR任务队列为空")
            
    except Exception as e:
        print(f"❌ 批量OCR处理失败: {e}")

def monitor_cpu_during_ocr():
    """监控OCR处理期间的CPU使用率"""
    import psutil
    import time
    import threading
    
    def cpu_monitor():
        print("📊 开始监控CPU使用率...")
        for i in range(30):  # 监控30秒
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_cores = psutil.cpu_percent(percpu=True, interval=0.1)
            active_cores = sum(1 for usage in cpu_cores if usage > 10)
            
            print(f"⏱️  {i+1:2d}s: CPU {cpu_percent:5.1f}%, 活跃核心 {active_cores:2d}/14")
            
            if cpu_percent > 70:
                print("🔥 CPU使用率超过70%，OCR优化生效!")
                break
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=cpu_monitor, daemon=True)
    monitor_thread.start()
    
    return monitor_thread

if __name__ == "__main__":
    print("🚀 强制批量OCR处理工具")
    print("="*50)
    
    # 启动CPU监控
    monitor_thread = monitor_cpu_during_ocr()
    
    # 触发批量OCR
    trigger_batch_ocr()
    
    # 等待监控完成
    monitor_thread.join(timeout=35)
    
    print("\n✅ 处理完成")
