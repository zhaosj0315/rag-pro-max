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
        处理PDF页面，使用优化OCR处理器
        
        Args:
            pdf_path: PDF文件路径
            images: PDF页面图像列表
            
        Returns:
            OCR识别结果列表
        """
        import tempfile
        import os
        from .optimized_ocr_processor import process_images_optimized
        
        task_id = str(uuid.uuid4())
        pages_count = len(images)
        
        print(f"📊 使用优化OCR处理器处理 {pages_count} 页")
        
        # 实时进度监控 - 开始任务
        progress_monitor.start_task(
            task_id=task_id,
            task_name=f"OCR处理: {pdf_path}",
            total_items=pages_count
        )
        
        start_time = time.time()
        results = []
        temp_files = []
        
        try:
            # 将PIL图像保存为临时文件
            for i, image in enumerate(images):
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                image.save(temp_file.name, 'JPEG')
                temp_files.append(temp_file.name)
            
            # 进度回调函数
            def progress_callback(completed, total):
                progress_monitor.update_progress(
                    task_id,
                    completed=completed,
                    current_item=f"处理页面 {completed}/{total}"
                )
            
            # 使用优化OCR处理器
            ocr_results = process_images_optimized(temp_files, progress_callback)
            
            # 提取文本结果
            results = [result.get('text', '') for result in ocr_results]
            
            processing_time = time.time() - start_time
            speed = pages_count / processing_time if processing_time > 0 else 0
            
            print(f"✅ OCR处理完成: {processing_time:.1f}秒, {speed:.1f}页/秒")
            
        except Exception as e:
            print(f"❌ OCR处理失败: {e}")
            results = [''] * pages_count
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            # 完成任务
            progress_monitor.complete_task(task_id)
        
        return results
    
    def _gpu_batch_process(self, task_id: str, images: List[Image.Image]) -> List[str]:
        """真正的并行OCR处理"""
        print(f"🚀 使用优化OCR处理 {len(images)} 页")
        
        # 导入优化OCR处理器
        from .optimized_ocr_processor import process_images_optimized
        
        # 更新进度
        progress_monitor.update_progress(
            task_id, 
            completed=0,
            current_item=f"启动优化OCR处理 {len(images)} 页"
        )
        
        # 进度回调函数
        def progress_callback(completed, total):
            progress_monitor.update_progress(
                task_id,
                completed=completed,
                current_item=f"处理中 {completed}/{total}"
            )
        
        # 转换图片路径（假设images是路径列表）
        image_paths = [str(img) if isinstance(img, str) else f"temp_image_{i}.jpg" for i, img in enumerate(images)]
        
        # 使用优化的OCR处理
        results = process_images_optimized(image_paths, progress_callback)
        
        # 更新完成进度
        progress_monitor.update_progress(
            task_id, 
            completed=len(images),
            current_item="优化OCR处理完成"
        )
        
        # 提取文本结果
        return [result.get('text', '') for result in results]
    
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
