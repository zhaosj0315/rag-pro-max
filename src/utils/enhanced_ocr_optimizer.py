def _process_single_image_global(args):
    """处理单张图片 - 全局函数用于多进程"""
    import pytesseract
    image, page_num = args
    try:
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return page_num, text.strip()
    except Exception as e:
        return page_num, f"OCR错误: {str(e)}"

"""
增强OCR优化器
集成自适应调度、GPU加速和实时进度监控
"""

import time
import uuid
from typing import List, Tuple
from PIL import Image

from .adaptive_scheduler import adaptive_scheduler
from .gpu_ocr_accelerator import gpu_ocr_accelerator
from ..ui.progress_monitor import progress_monitor

class EnhancedOCROptimizer:
    """增强OCR优化器"""
    
    def __init__(self):
        self.gpu_available = False
        self.initialize_gpu()
    
    def initialize_gpu(self):
        """初始化GPU加速"""
        try:
            self.gpu_available = gpu_ocr_accelerator.initialize()
            if self.gpu_available:
                print("🚀 GPU OCR加速已启用")
            else:
                print("💻 使用CPU OCR处理")
        except Exception as e:
            print(f"⚠️  GPU初始化失败: {e}")
            self.gpu_available = False
    
    def process_pdf_pages(self, pdf_path: str, images: List[Image.Image]) -> List[str]:
        """
        处理PDF页面，集成所有优化功能
        
        Args:
            pdf_path: PDF文件路径
            images: PDF页面图像列表
            
        Returns:
            OCR识别结果列表
        """
        task_id = str(uuid.uuid4())
        pages_count = len(images)
        
        # 1. 自适应调度 - 获取最优策略
        workers, strategy, confidence = adaptive_scheduler.get_optimal_strategy(pages_count)
        
        print(f"📊 自适应调度策略: {strategy}")
        print(f"   进程数: {workers}")
        print(f"   置信度: {confidence:.1%}")
        print(f"   页面数: {pages_count}")
        
        # 2. 实时进度监控 - 开始任务
        progress_monitor.start_task(
            task_id=task_id,
            task_name=f"OCR处理: {pdf_path}",
            total_items=pages_count
        )
        
        start_time = time.time()
        results = []
        success = True
        
        try:
            # 3. GPU加速处理
            if self.gpu_available and pages_count >= 3:
                results = self._gpu_batch_process(task_id, images)
            else:
                results = self._cpu_process(task_id, images, workers)
            
            # 处理完成
            progress_monitor.complete_task(task_id)
            
        except Exception as e:
            print(f"❌ OCR处理失败: {e}")
            progress_monitor.fail_task(task_id, str(e))
            success = False
            results = [""] * pages_count
        
        # 4. 记录性能数据
        processing_time = time.time() - start_time
        adaptive_scheduler.record_performance(
            workers=workers,
            pages=pages_count,
            processing_time=processing_time,
            success=success
        )
        
        # 输出性能统计
        if success:
            speed = pages_count / processing_time if processing_time > 0 else 0
            print(f"✅ OCR处理完成: {processing_time:.1f}秒, {speed:.1f}页/秒")
        
        return results
    
    def _gpu_batch_process(self, task_id: str, images: List[Image.Image]) -> List[str]:
        """GPU批量处理"""
        print(f"🚀 使用GPU批量处理 {len(images)} 页")
        
        batch_size = gpu_ocr_accelerator.batch_size
        results = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            # 更新进度
            progress_monitor.update_progress(
                task_id, 
                completed=i,
                current_item=f"GPU批量处理 {i+1}-{min(i+len(batch), len(images))}"
            )
            
            # GPU批量OCR
            batch_results = gpu_ocr_accelerator.process_images_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def _cpu_process(self, task_id: str, images: List[Image.Image], workers: int) -> List[str]:
        """CPU多进程处理"""
        print(f"💻 使用CPU处理 {len(images)} 页 (进程数: {workers})")
        
        if workers == 1:
            # 单进程处理
            return self._single_process(task_id, images)
        else:
            # 多进程处理
            return self._multi_process(task_id, images, workers)
    
    def _single_process(self, task_id: str, images: List[Image.Image]) -> List[str]:
        """单进程处理"""
        import pytesseract
        
        results = []
        for i, image in enumerate(images):
            # 更新进度
            progress_monitor.update_progress(
                task_id,
                completed=i,
                current_item=f"处理第 {i+1} 页"
            )
            
            try:
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                results.append(text.strip())
            except Exception as e:
                print(f"⚠️  第{i+1}页OCR失败: {e}")
                results.append("")
        
        return results
    
    def _multi_process(self, task_id: str, images: List[Image.Image], workers: int) -> List[str]:
        """多进程处理"""
        from concurrent.futures import ProcessPoolExecutor
        import pytesseract
        
        def process_single_image(args):
            """处理单张图片"""
            image, page_num = args
            try:
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                return page_num, text.strip()
            except Exception as e:
                return page_num, ""
        
        results = [""] * len(images)
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # 提交任务
            future_to_page = {
                executor.submit(_process_single_image_global, (img, i)): i 
                for i, img in enumerate(images)
            }
            
            completed = 0
            for future in future_to_page:
                try:
                    page_num, text = future.result()
                    results[page_num] = text
                    completed += 1
                    
                    # 更新进度
                    progress_monitor.update_progress(
                        task_id,
                        completed=completed,
                        current_item=f"完成第 {page_num+1} 页"
                    )
                    
                except Exception as e:
                    print(f"⚠️  多进程OCR异常: {e}")
        
        return results
    
    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        stats = adaptive_scheduler.get_performance_stats()
        
        if self.gpu_available:
            gpu_info = gpu_ocr_accelerator.get_device_info()
            stats.update({
                "GPU加速": "已启用",
                "GPU设备": gpu_info.get("gpu_name", "Unknown"),
                "GPU批量大小": gpu_info.get("batch_size", 1)
            })
        else:
            stats["GPU加速"] = "未启用"
        
        return stats
    
    def benchmark_performance(self) -> dict:
        """性能基准测试"""
        print("🧪 开始性能基准测试...")
        
        # 创建测试图像
        test_images = []
        for i in range(10):
            img = Image.new('RGB', (800, 600), color='white')
            test_images.append(img)
        
        results = {}
        
        # GPU测试
        if self.gpu_available:
            gpu_result = gpu_ocr_accelerator.benchmark(10)
            results["GPU性能"] = gpu_result
        
        # CPU测试
        start_time = time.time()
        cpu_results = self._cpu_process("benchmark", test_images, 2)
        cpu_time = time.time() - start_time
        
        results["CPU性能"] = {
            "images_processed": len(cpu_results),
            "total_time": f"{cpu_time:.2f}秒",
            "speed": f"{len(cpu_results) / cpu_time:.1f}张/秒",
            "workers": 2
        }
        
        return results

# 全局实例
enhanced_ocr_optimizer = EnhancedOCROptimizer()
