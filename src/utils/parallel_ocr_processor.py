"""
并行OCR处理器
真正的多进程OCR处理，充分利用CPU资源
"""

import multiprocessing as mp
import time
from typing import List, Tuple
from PIL import Image
import numpy as np

# 全局OCR实例，避免重复加载
_global_ocr = None
_ocr_initialized = False

def _get_ocr_instance():
    """获取全局OCR实例，只初始化一次"""
    global _global_ocr, _ocr_initialized
    if not _ocr_initialized:
        try:
            # 设置环境变量禁用详细日志
            import os
            os.environ['GLOG_minloglevel'] = '2'  # 只显示错误
            os.environ['FLAGS_logtostderr'] = '0'  # 不输出到stderr
            
            from paddleocr import PaddleOCR
            import logging
            
            # 设置PaddleOCR相关日志级别
            logging.getLogger('ppocr').setLevel(logging.ERROR)
            logging.getLogger('paddle').setLevel(logging.ERROR)
            
            _global_ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            _ocr_initialized = True
            print("🔥 OCR模型已加载")
        except Exception as e:
            print(f"❌ OCR模型加载失败: {e}")
            _global_ocr = None
    return _global_ocr

def _ocr_worker_process(image_data: Tuple[int, np.ndarray]) -> Tuple[int, str]:
    """OCR工作进程 - 必须在模块级别定义"""
    page_num, img_array = image_data  # 先解包，确保变量可用
    
    try:
        # 使用全局OCR实例
        ocr = _get_ocr_instance()
        result = ocr.ocr(img_array)
        
        # 提取文本
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if len(line) >= 2:
                    text_lines.append(line[1][0])
        
        return page_num, '\n'.join(text_lines)
        
    except Exception as e:
        return page_num, f"OCR错误: {str(e)}"


class ParallelOCRProcessor:
    """并行OCR处理器"""
    
    def __init__(self, max_workers: int = None):
        if max_workers is None:
            # 使用90%的CPU核心
            max_workers = max(1, int(mp.cpu_count() * 0.9))
        
        self.max_workers = max_workers
        print(f"🚀 初始化并行OCR处理器: {self.max_workers} 个进程")
    
    def process_images_parallel(self, images: List[Image.Image]) -> List[str]:
        """并行处理图像列表"""
        if not images:
            return []
        
        print(f"🔥 启动OCR处理 {len(images)} 张图片")
        
        # 准备数据
        image_data = []
        for i, image in enumerate(images):
            img_array = np.array(image)
            image_data.append((i, img_array))
        
        start_time = time.time()
        results = {}
        
        # 检查是否在daemon进程中，直接使用串行处理
        try:
            current_process = mp.current_process()
            if current_process.daemon:
                use_serial = True
            else:
                use_serial = False
        except:
            use_serial = True
        
        if use_serial:
            # 串行处理（在daemon进程中）
            print("⚡ 使用串行OCR处理")
            for page_num, img_array in image_data:
                try:
                    page_num, text = _ocr_worker_process((page_num, img_array))
                    results[page_num] = text
                except Exception as ocr_e:
                    results[page_num] = f"OCR错误: {str(ocr_e)}"
        else:
            # 尝试多进程处理
            try:
                print(f"🚀 使用多进程OCR处理 ({self.max_workers}个进程)")
                with mp.Pool(processes=self.max_workers) as pool:
                    pool_results = pool.map(_ocr_worker_process, image_data)
                    for page_num, text in pool_results:
                        results[page_num] = text
            except Exception as e:
                # 回退到串行处理
                print(f"⚠️ 多进程失败，回退到串行处理")
                for page_num, img_array in image_data:
                    try:
                        page_num, text = _ocr_worker_process((page_num, img_array))
                        results[page_num] = text
                    except Exception as ocr_e:
                        results[page_num] = f"OCR错误: {str(ocr_e)}"
        
        # 按顺序组装结果
        ordered_results = []
        for i in range(len(images)):
            ordered_results.append(results.get(i, ""))
        
        elapsed = time.time() - start_time
        speed = len(images) / elapsed if elapsed > 0 else 0
        
        print(f"✅ OCR处理完成: {len(images)}张图片, {elapsed:.1f}秒, {speed:.1f}张/秒")
        
        return ordered_results


# 全局实例
parallel_ocr_processor = ParallelOCRProcessor()
