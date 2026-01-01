"""
增强日志记录器 - 提供结构化、易读的日志输出
"""

import time
from datetime import datetime
from collections import defaultdict

class EnhancedLogger:
    def __init__(self):
        self.start_time = time.time()
        self.step_times = {}
        self.ocr_stats = defaultdict(int)
        self.current_step = 0
        self.total_steps = 6
        
    def log_step_start(self, step_num, step_name, total_items=None):
        """记录步骤开始"""
        self.current_step = step_num
        self.step_times[step_num] = time.time()
        
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{'='*60}")
        print(f"📂 [{timestamp}] 步骤 {step_num}/{self.total_steps}: {step_name}")
        print(f"⏱️  总耗时: {elapsed/60:.1f}分钟")
        if total_items:
            print(f"📊 待处理: {total_items:,} 项")
        print(f"{'='*60}")
    
    def log_step_end(self, step_num, step_name, result_summary=None):
        """记录步骤结束"""
        if step_num in self.step_times:
            step_duration = time.time() - self.step_times[step_num]
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n✅ [{timestamp}] 步骤 {step_num} 完成: {step_name}")
            print(f"⏱️  耗时: {step_duration/60:.1f}分钟")
            if result_summary:
                for key, value in result_summary.items():
                    print(f"📊 {key}: {value}")
    
    def log_ocr_batch_start(self, file_count, total_pages):
        """记录OCR批次开始"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🔍 [{timestamp}] OCR批次处理开始")
        print(f"   📄 文件数: {file_count}")
        print(f"   📑 总页数: {total_pages}")
        self.ocr_batch_start = time.time()
    
    def log_ocr_file_result(self, filename, pages, duration, success, error_msg=None):
        """记录单个OCR文件结果"""
        speed = pages / duration if duration > 0 else 0
        status = "✅" if success else "❌"
        
        self.ocr_stats['total_files'] += 1
        self.ocr_stats['total_pages'] += pages
        self.ocr_stats['total_time'] += duration
        
        if success:
            self.ocr_stats['success_files'] += 1
        else:
            self.ocr_stats['failed_files'] += 1
        
        print(f"   {status} {filename}: {pages}页, {duration:.1f}秒, {speed:.1f}页/秒")
        if not success and error_msg:
            print(f"      ⚠️  {error_msg}")
    
    def log_ocr_batch_summary(self):
        """记录OCR批次汇总"""
        if self.ocr_stats['total_files'] == 0:
            return
            
        batch_duration = time.time() - self.ocr_batch_start
        success_rate = (self.ocr_stats['success_files'] / self.ocr_stats['total_files']) * 100
        avg_speed = self.ocr_stats['total_pages'] / self.ocr_stats['total_time'] if self.ocr_stats['total_time'] > 0 else 0
        
        print(f"\n📊 OCR批次汇总:")
        print(f"   📄 处理文件: {self.ocr_stats['total_files']}")
        print(f"   📑 处理页数: {self.ocr_stats['total_pages']:,}")
        print(f"   ✅ 成功: {self.ocr_stats['success_files']} ({success_rate:.1f}%)")
        print(f"   ❌ 失败: {self.ocr_stats['failed_files']}")
        print(f"   ⏱️  总耗时: {batch_duration/60:.1f}分钟")
        print(f"   🚀 平均速度: {avg_speed:.1f}页/秒")
    
    def log_vector_progress(self, current, total, batch_size=2048):
        """记录向量化进度"""
        progress = (current / total) * 100
        batches_done = current // batch_size
        total_batches = (total + batch_size - 1) // batch_size
        
        # 计算预计剩余时间
        if hasattr(self, 'vector_start_time'):
            elapsed = time.time() - self.vector_start_time
            if current > 0:
                estimated_total = elapsed * total / current
                remaining = estimated_total - elapsed
                remaining_str = f", 预计剩余: {remaining/60:.1f}分钟"
            else:
                remaining_str = ""
        else:
            self.vector_start_time = time.time()
            remaining_str = ""
        
        print(f"\r🧠 向量化进度: {progress:.1f}% ({current:,}/{total:,}) | 批次: {batches_done}/{total_batches}{remaining_str}", end="", flush=True)
    
    def log_final_summary(self):
        """记录最终汇总"""
        total_duration = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n\n{'='*60}")
        print(f"🎉 [{timestamp}] 处理完成!")
        print(f"⏱️  总耗时: {total_duration/60:.1f}分钟")
        
        if self.ocr_stats['total_files'] > 0:
            print(f"\n📊 OCR处理汇总:")
            print(f"   📄 文件: {self.ocr_stats['total_files']}")
            print(f"   📑 页数: {self.ocr_stats['total_pages']:,}")
            print(f"   ✅ 成功率: {(self.ocr_stats['success_files']/self.ocr_stats['total_files']*100):.1f}%")
        
        print(f"{'='*60}")

# 全局增强日志器
enhanced_logger = EnhancedLogger()

def demo_usage():
    """演示用法"""
    logger = EnhancedLogger()
    
    # 步骤1: 文件扫描
    logger.log_step_start(1, "文件扫描", 1000)
    time.sleep(1)
    logger.log_step_end(1, "文件扫描", {"发现文件": "1000个", "支持格式": "PDF, DOCX, TXT"})
    
    # 步骤2: OCR处理
    logger.log_step_start(2, "OCR文档识别")
    logger.log_ocr_batch_start(5, 100)
    
    # 模拟OCR处理
    files = [("doc1.pdf", 20), ("doc2.pdf", 30), ("doc3.pdf", 15)]
    for filename, pages in files:
        time.sleep(0.5)  # 模拟处理时间
        success = True  # 模拟成功
        logger.log_ocr_file_result(filename, pages, 0.5, success)
    
    logger.log_ocr_batch_summary()
    logger.log_step_end(2, "OCR文档识别")
    
    # 步骤3: 向量化
    logger.log_step_start(3, "向量化处理", 10000)
    for i in range(0, 10001, 1000):
        time.sleep(0.1)
        logger.log_vector_progress(i, 10000)
    
    logger.log_final_summary()

if __name__ == "__main__":
    demo_usage()
