"""
优化OCR处理器 - 解决重复加载模型问题
单例模式 + 模型复用 + 资源限制
"""

import os
import time
import psutil
import threading
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.app_logging.log_manager import LogManager

# 设置环境变量，禁用PaddleOCR详细日志
os.environ['GLOG_minloglevel'] = '3'
os.environ['FLAGS_logtostderr'] = '0'
os.environ['PADDLE_LOG_LEVEL'] = '50'

from .cpu_monitor import get_resource_limiter

class OptimizedOCRProcessor:
    """优化的OCR处理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.initialized = False
        self.ocr_engine = None
        self.resource_limiter = get_resource_limiter(max_cpu_percent=75.0, max_memory_percent=85.0)
        self.max_workers = 3  # 降低最大进程数，避免过载
        self.logger = LogManager()
        
        # 统计信息
        self.total_files_processed = 0
        self.total_processing_time = 0
        self.session_start_time = datetime.now()
        
        self.logger.info("🚀 OCR处理器初始化开始")
        
    def initialize(self) -> bool:
        """初始化OCR引擎（只执行一次）"""
        if self.initialized:
            self.logger.info("✅ OCR引擎已初始化，跳过重复加载")
            return True
            
        try:
            logger.info("🚀 初始化优化OCR处理器...")
            self.logger.info("🚀 开始初始化OCR引擎")
            start_time = time.time()
            
            # 导入PaddleOCR
            from paddleocr import PaddleOCR
            import logging as paddle_logging
            
            # 设置日志级别
            paddle_logging.getLogger('ppocr').setLevel(paddle_logging.ERROR)
            paddle_logging.getLogger('paddle').setLevel(paddle_logging.ERROR)
            
            # 初始化OCR引擎（只初始化一次）
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                det_db_thresh=0.3,
                det_db_box_thresh=0.6
            )
            
            init_time = time.time() - start_time
            self.initialized = True
            
            logger.info("✅ OCR引擎初始化完成")
            self.logger.info(f"✅ OCR引擎初始化成功，耗时: {init_time:.2f}秒")
            return True
            
        except Exception as e:
            error_msg = f"❌ OCR引擎初始化失败: {str(e)}"
            logger.info(error_msg)
            self.logger.error(error_msg)
            return False
    
    def process_images(self, image_paths: List[str], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """批量处理图片"""
        if not self.initialize():
            logger.error("❌ OCR引擎初始化失败，无法处理图片")
            return [{'path': path, 'text': '', 'error': 'OCR初始化失败'} for path in image_paths]
        
        start_time = time.time()
        logger.info(f"🚀 开始批量OCR处理，共 {len(image_paths)} 个文件")
        
        # 检查系统资源
        resources = self.resource_limiter.check_resources()
        logger.info(f"📊 系统资源: CPU {resources['cpu_percent']:.1f}%, 内存 {resources['memory_percent']:.1f}%")
        logger.info(f"📊 系统资源状态: CPU {resources['cpu_percent']:.1f}%, 内存 {resources['memory_percent']:.1f}%")
        
        # 根据资源状况决定处理方式
        if resources['cpu_high'] or len(image_paths) <= 2:
            logger.info("⚡ 使用串行OCR处理")
            logger.info("⚡ 资源紧张或文件较少，使用串行处理")
            result = self._process_serial(image_paths, progress_callback)
        else:
            # 获取安全的工作线程数
            safe_workers = self.resource_limiter.get_safe_worker_count(self.max_workers)
            logger.info(f"🚀 使用并行处理 {len(image_paths)} 张图片 (工作线程: {safe_workers})")
            logger.info(f"🚀 使用并行处理，工作线程: {safe_workers}")
            result = self._process_parallel(image_paths, progress_callback, safe_workers)
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self.total_files_processed += len(image_paths)
        self.total_processing_time += processing_time
        
        # 记录处理结果
        success_count = len([r for r in result if r.get('success', True) and not r.get('error')])
        logger.info(f"✅ OCR处理完成: {success_count}/{len(image_paths)} 成功，耗时: {processing_time:.2f}秒")
        logger.info(f"📊 累计处理文件: {self.total_files_processed} 个，累计耗时: {self.total_processing_time:.2f}秒")
        
        return result
    
    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        session_time = (datetime.now() - self.session_start_time).total_seconds()
        avg_time_per_file = self.total_processing_time / max(self.total_files_processed, 1)
        
        stats = {
            'total_files_processed': self.total_files_processed,
            'total_processing_time': self.total_processing_time,
            'session_duration': session_time,
            'avg_time_per_file': avg_time_per_file,
            'files_per_minute': (self.total_files_processed / max(session_time / 60, 1)),
            'session_start_time': self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"📊 OCR处理统计: {stats}")
        return stats
    
    def print_statistics(self):
        """打印处理统计信息"""
        stats = self.get_statistics()
        logger.info("\n" + "="*50)
        logger.info("📊 OCR处理统计信息")
        logger.info("="*50)
        logger.info(f"📁 总处理文件数: {stats['total_files_processed']} 个")
        logger.info(f"⏱️  总处理时间: {stats['total_processing_time']:.2f} 秒")
        logger.info(f"🕐 会话持续时间: {stats['session_duration']:.2f} 秒")
        logger.info(f"⚡ 平均每文件: {stats['avg_time_per_file']:.2f} 秒")
        logger.info(f"🚀 处理速度: {stats['files_per_minute']:.1f} 文件/分钟")
        logger.info(f"🎯 会话开始: {stats['session_start_time']}")
        logger.info("="*50)
    
    def _process_serial(self, image_paths: List[str], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """串行处理"""
        results = []
        
        for i, image_path in enumerate(image_paths):
            # 检查资源状况
            self.resource_limiter.wait_if_needed(max_wait=2.0)
            
            result = self._process_single_image(image_path)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(image_paths))
                
            # 每处理2张图片检查一次资源
            if i % 2 == 0 and i > 0:
                resources = self.resource_limiter.check_resources()
                if resources['cpu_high']:
                    logger.warning(f"CPU使用率: {resources['cpu_percent']:.1f}%")
                    time.sleep(1.0)
        
        return results
    
    def _process_parallel(self, image_paths: List[str], progress_callback: Optional[Callable] = None, workers: int = 4) -> List[Dict]:
        """并行处理"""
        results = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交任务
            futures = {
                executor.submit(self._process_single_image, path): path 
                for path in image_paths
            }
            
            # 收集结果
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(image_paths))
                        
                    # 每处理几个任务检查一次资源
                    if i % 3 == 0 and i > 0:
                        self.resource_limiter.wait_if_needed(max_wait=1.0)
                        
                except Exception as e:
                    path = futures[future]
                    results.append({
                        'path': path,
                        'text': '',
                        'error': f'处理超时: {e}'
                    })
        
        return results
    
    def _process_single_image(self, image_path: str) -> Dict:
        """处理单张图片"""
        try:
            # 使用已初始化的OCR引擎
            result = self.ocr_engine.ocr(image_path, cls=True)
            
            # 提取文本
            text_lines = []
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text_lines.append(line[1][0])
            
            text = '\n'.join(text_lines)
            
            return {
                'path': image_path,
                'text': text,
                'confidence': self._calculate_confidence(text),
                'error': None
            }
            
        except Exception as e:
            return {
                'path': image_path,
                'text': '',
                'error': str(e)
            }
    
    def _calculate_confidence(self, text: str) -> float:
        """计算置信度"""
        if not text:
            return 0.0
        
        char_count = len(text)
        alpha_count = sum(1 for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff')
        
        if char_count == 0:
            return 0.0
        
        confidence = (alpha_count / char_count) * 100
        return min(confidence, 100.0)

# 全局实例
_ocr_processor = None

def get_ocr_processor() -> OptimizedOCRProcessor:
    """获取OCR处理器实例"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OptimizedOCRProcessor()
    return _ocr_processor

def process_images_optimized(image_paths: List[str], progress_callback: Optional[Callable] = None) -> List[Dict]:
    """优化的图片处理接口"""
    processor = get_ocr_processor()
    return processor.process_images(image_paths, progress_callback)
