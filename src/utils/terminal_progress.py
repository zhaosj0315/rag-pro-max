"""
终端进度显示 - 清晰简洁的实时输出
"""

import time
import psutil
from datetime import datetime

class TerminalProgress:
    def __init__(self):
        self.start_time = time.time()
        self.ocr_stats = {'files': 0, 'pages': 0, 'success': 0, 'failed': 0}
        self.current_step = 0
        
    def check_memory(self):
        """检查内存使用率"""
        memory = psutil.virtual_memory()
        if memory.percent > 95:
            print(f"\n🚨 内存告警: {memory.percent:.1f}% - 系统即将耗尽内存!")
            return True
        elif memory.percent > 85:
            print(f"⚠️  内存警告: {memory.percent:.1f}%")
        return False
    
    def log_step(self, step, total, name):
        """记录步骤"""
        self.current_step = step
        elapsed = (time.time() - self.start_time) / 60
        print(f"\n{'='*50}")
        print(f"📂 [{datetime.now().strftime('%H:%M:%S')}] 步骤 {step}/{total}: {name}")
        print(f"⏱️  已耗时: {elapsed:.1f}分钟")
        self.check_memory()
        print(f"{'='*50}")
    
    def log_ocr_batch(self, file_count, total_pages):
        """OCR批次开始"""
        print(f"\n🔍 OCR批次: {file_count}文件, {total_pages}页")
        self.ocr_batch_start = time.time()
    
    def log_ocr_result(self, filename, pages, duration, success):
        """OCR单文件结果"""
        speed = pages / duration if duration > 0 else 0
        status = "✅" if success else "❌"
        
        self.ocr_stats['files'] += 1
        self.ocr_stats['pages'] += pages
        if success:
            self.ocr_stats['success'] += 1
        else:
            self.ocr_stats['failed'] += 1
        
        print(f"   {status} {filename}: {pages}页, {speed:.1f}页/秒")
        
        # 检查内存
        if self.check_memory():
            print("   🛑 内存不足，建议暂停处理")
    
    def log_ocr_summary(self):
        """OCR批次汇总"""
        if self.ocr_stats['files'] == 0:
            return
            
        success_rate = (self.ocr_stats['success'] / self.ocr_stats['files']) * 100
        batch_time = time.time() - self.ocr_batch_start
        
        print(f"\n📊 OCR汇总: {self.ocr_stats['files']}文件, 成功率{success_rate:.0f}%, {batch_time/60:.1f}分钟")
    
    def log_vector_progress(self, current, total):
        """向量化进度"""
        progress = (current / total) * 100
        print(f"\r🧠 向量化: {progress:.1f}% ({current:,}/{total:,})", end="", flush=True)
        
        # 每10%检查一次内存
        if current % (total // 10) == 0:
            if self.check_memory():
                print(f"\n🛑 内存不足，向量化可能失败")
    
    def log_final(self):
        """最终汇总"""
        total_time = (time.time() - self.start_time) / 60
        memory = psutil.virtual_memory()
        
        print(f"\n\n🎉 处理完成! 总耗时: {total_time:.1f}分钟")
        print(f"📊 OCR: {self.ocr_stats['files']}文件, 成功{self.ocr_stats['success']}, 失败{self.ocr_stats['failed']}")
        print(f"💾 最终内存: {memory.percent:.1f}%")

# 全局实例
terminal_progress = TerminalProgress()
