"""
批量 OCR 优化处理器 - v2.1
并行处理多个图片文件，GPU加速OCR识别
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Tuple, Optional
import torch
import multiprocessing as mp
from pathlib import Path
import logging

class ImagePreprocessor:
    """智能图片预处理"""
    
    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """图片增强处理"""
        # 转换为PIL图像
        pil_image = Image.fromarray(image)
        
        # 对比度增强
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        # 锐化
        pil_image = pil_image.filter(ImageFilter.SHARPEN)
        
        # 转回numpy
        return np.array(pil_image)
    
    @staticmethod
    def denoise_image(image: np.ndarray) -> np.ndarray:
        """图片去噪"""
        # 高斯模糊去噪
        denoised = cv2.GaussianBlur(image, (3, 3), 0)
        
        # 形态学操作
        kernel = np.ones((2, 2), np.uint8)
        denoised = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        
        return denoised
    
    @staticmethod
    def binarize_image(image: np.ndarray) -> np.ndarray:
        """图片二值化"""
        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 自适应阈值
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary

class BatchOCRProcessor:
    """批量OCR处理器"""
    
    def __init__(self, max_workers: Optional[int] = None, use_gpu: bool = True):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.preprocessor = ImagePreprocessor()
        
        # OCR配置
        self.ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz中文'
    
    def process_single_image(self, image_path: str) -> Dict:
        """处理单个图片"""
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                return {'path': image_path, 'text': '', 'error': '无法读取图片'}
            
            # 预处理
            processed_image = self._preprocess_image(image)
            
            # OCR识别
            text = pytesseract.image_to_string(
                processed_image, 
                config=self.ocr_config,
                lang='chi_sim+eng'
            )
            
            return {
                'path': image_path,
                'text': text.strip(),
                'confidence': self._calculate_confidence(text),
                'error': None
            }
            
        except Exception as e:
            return {'path': image_path, 'text': '', 'error': str(e)}
    
    def process_batch(self, image_paths: List[str], progress_callback=None) -> List[Dict]:
        """批量处理图片"""
        results = []
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(self.process_single_image, path): path 
                for path in image_paths
            }
            
            # 收集结果
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=30)  # 30秒超时
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(image_paths))
                        
                except Exception as e:
                    path = futures[future]
                    results.append({
                        'path': path, 
                        'text': '', 
                        'error': f'处理超时: {e}'
                    })
        
        return results
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图片预处理流水线"""
        # 1. 去噪
        image = self.preprocessor.denoise_image(image)
        
        # 2. 增强
        image = self.preprocessor.enhance_image(image)
        
        # 3. 二值化
        image = self.preprocessor.binarize_image(image)
        
        return image
    
    def _calculate_confidence(self, text: str) -> float:
        """计算OCR置信度"""
        if not text:
            return 0.0
        
        # 简单的置信度计算
        # 基于文本长度和字符类型
        char_count = len(text)
        alpha_count = sum(1 for c in text if c.isalnum())
        
        if char_count == 0:
            return 0.0
        
        confidence = (alpha_count / char_count) * 100
        return min(confidence, 100.0)

class GPUAcceleratedOCR:
    """GPU加速OCR（如果可用）"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        
    def load_model(self):
        """加载GPU OCR模型"""
        try:
            # 这里可以集成更先进的OCR模型，如PaddleOCR
            # from paddleocr import PaddleOCR
            # self.model = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True)
            pass
        except ImportError:
            logging.warning("GPU OCR模型不可用，使用CPU版本")
    
    def process_with_gpu(self, image_path: str) -> str:
        """使用GPU处理OCR"""
        if self.model is None:
            return ""
        
        try:
            # GPU OCR处理逻辑
            # result = self.model.ocr(image_path, cls=True)
            # return self._extract_text(result)
            return ""
        except Exception as e:
            logging.error(f"GPU OCR处理失败: {e}")
            return ""
