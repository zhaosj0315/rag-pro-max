"""
强制批量OCR触发器
确保在文件扫描完成后立即处理所有OCR任务
"""

import time
import threading
from typing import List

class ForceBatchOCRTrigger:
    """强制批量OCR触发器"""
    
    def __init__(self):
        self.pending_files = []
        self.processing = False
        self.trigger_timer = None
        
    def add_ocr_file(self, file_info):
        """添加需要OCR的文件"""
        self.pending_files.append(file_info)
        print(f"📋 OCR队列: {len(self.pending_files)} 个文件待处理")
        
        # 重置定时器，5秒后如果没有新文件就触发处理
        if self.trigger_timer:
            self.trigger_timer.cancel()
        
        self.trigger_timer = threading.Timer(5.0, self.force_trigger_batch_ocr)
        self.trigger_timer.start()
    
    def force_trigger_batch_ocr(self):
        """强制触发批量OCR处理"""
        if self.processing or not self.pending_files:
            return
            
        self.processing = True
        
        try:
            from src.utils.batch_ocr_processor import batch_ocr_processor
            
            print(f"\n🚀 强制触发批量OCR处理...")
            print(f"📊 待处理文件: {len(self.pending_files)} 个")
            print(f"📊 OCR任务队列: {len(batch_ocr_processor.ocr_tasks)} 个任务")
            
            if batch_ocr_processor.ocr_tasks:
                # 显示详细统计
                total_pages = len(batch_ocr_processor.ocr_tasks)
                unique_files = len(set(task['task_id'] for task in batch_ocr_processor.ocr_tasks))
                
                print(f"💪 开始高性能批量OCR: {total_pages} 页，来自 {unique_files} 个文件")
                
                # 强制处理
                start_time = time.time()
                results = batch_ocr_processor.process_all_ocr_tasks()
                end_time = time.time()
                
                duration = end_time - start_time
                pages_per_sec = total_pages / duration if duration > 0 else 0
                
                print(f"✅ 批量OCR完成: {duration:.1f}秒, {pages_per_sec:.1f}页/秒")
                print(f"📈 CPU应该已经飙升到70%+")
                
                # 清空待处理列表
                self.pending_files = []
                
            else:
                print("ℹ️  OCR任务队列为空，可能已经被处理")
                
        except Exception as e:
            print(f"❌ 强制批量OCR失败: {e}")
        finally:
            self.processing = False

# 全局触发器实例
force_batch_ocr_trigger = ForceBatchOCRTrigger()
