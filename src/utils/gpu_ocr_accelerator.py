"""
GPU OCR加速器
使用PaddleOCR GPU版本和批量推理加速OCR处理
"""

import os
import time
import torch
import numpy as np
from typing import List, Tuple, Optional
from PIL import Image
import logging

# 设置PaddleOCR日志级别
logging.getLogger('ppocr').setLevel(logging.ERROR)

class GPUOCRAccelerator:
    """GPU OCR加速器"""
    
    def __init__(self):
        self.ocr_engine = None
        self.device = self._detect_device()
        self.batch_size = self._get_optimal_batch_size()
        self.initialized = False
        
    def _detect_device(self) -> str:
        """检测可用的GPU设备"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _get_optimal_batch_size(self) -> int:
        """获取最优批量大小"""
        if self.device == "cuda":
            # CUDA设备根据显存大小调整
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                if gpu_memory >= 8:
                    return 8
                elif gpu_memory >= 4:
                    return 4
                else:
                    return 2
            except:
                return 2
        elif self.device == "mps":
            # Apple Silicon设备
            return 4
        else:
            # CPU设备
            return 1
    
    def initialize(self) -> bool:
        """初始化OCR引擎"""
        if self.initialized:
            return True
        
        try:
            # 尝试导入PaddleOCR
            from paddleocr import PaddleOCR
            
            print(f"🚀 初始化GPU OCR加速器...")
            print(f"   设备: {self.device}")
            print(f"   批量大小: {self.batch_size}")
            
            # 初始化PaddleOCR
            # 设备检测已在初始化中处理
            
            # 根据设备类型设置参数
            if self.device == "cuda":
                self.ocr_engine = PaddleOCR(
                    use_angle_use_angle_cls=True,
                    lang='ch',
                    # GPU优化参数
                    det_db_thresh=0.3,
                    det_db_box_thresh=0.6,
                    det_db_unclip_ratio=1.5,
                    det_limit_side_len=960,
                    det_limit_type='max'
                )
            else:
                # CPU或MPS设备
                self.ocr_engine = PaddleOCR(
                    use_angle_use_angle_cls=True,
                    lang='ch',
                    det_db_thresh=0.3,
                    det_db_box_thresh=0.6,
                    det_db_unclip_ratio=1.5,
                    det_limit_side_len=960,
                    det_limit_type='max'
                )
            
            # 预热模型
            self._warmup()
            
            self.initialized = True
            print(f"✅ GPU OCR加速器初始化成功")
            return True
            
        except ImportError:
            print("⚠️  PaddleOCR未安装，回退到CPU OCR")
            return False
        except Exception as e:
            print(f"❌ GPU OCR初始化失败: {e}")
            return False
    
    def _warmup(self):
        """预热模型"""
        try:
            # 创建测试图像
            test_image = Image.new('RGB', (100, 50), color='white')
            self.ocr_engine.ocr(np.array(test_image))
            print("🔥 模型预热完成")
        except Exception as e:
            print(f"⚠️  模型预热失败: {e}")
    
    def process_images_batch(self, images: List[Image.Image]) -> List[str]:
        """批量处理图像"""
        if not self.initialized:
            if not self.initialize():
                return self._fallback_ocr(images)
        
        results = []
        
        # 分批处理
        for i in range(0, len(images), self.batch_size):
            batch = images[i:i + self.batch_size]
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
            
            # GPU内存清理
            if self.device in ["cuda", "mps"]:
                self._cleanup_gpu_memory()
        
        return results
    
    def _process_batch(self, batch: List[Image.Image]) -> List[str]:
        """处理单个批次"""
        batch_texts = []
        
        try:
            start_time = time.time()
            
            for image in batch:
                # 转换为numpy数组
                img_array = np.array(image)
                
                # OCR识别
                try:
                    result = self.ocr_engine.ocr(img_array)
                except Exception as ocr_error:
                    print(f"❌ GPU OCR处理失败: {ocr_error}")
                    result = None
                
                # 提取文本
                text = self._extract_text_from_result(result)
                batch_texts.append(text)
            
            elapsed = time.time() - start_time
            speed = len(batch) / elapsed if elapsed > 0 else 0
            
            print(f"🚀 GPU批量OCR: {len(batch)}张图片, {elapsed:.2f}秒, {speed:.1f}张/秒")
            
        except Exception as e:
            print(f"❌ GPU OCR批量处理失败: {e}")
            # 回退到逐张处理
            batch_texts = self._fallback_ocr(batch)
        
        return batch_texts
    
    def _extract_text_from_result(self, result) -> str:
        """从OCR结果中提取文本"""
        if not result or not result[0]:
            return ""
        
        texts = []
        for line in result[0]:
            if len(line) >= 2:
                text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                if text.strip():
                    texts.append(text.strip())
        
        return '\n'.join(texts)
    
    def _fallback_ocr(self, images: List[Image.Image]) -> List[str]:
        """回退到CPU OCR"""
        try:
            import pytesseract
            
            print(f"🔄 回退到CPU OCR处理 {len(images)} 张图片")
            results = []
            
            for image in images:
                try:
                    text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                    results.append(text.strip())
                except Exception as e:
                    print(f"⚠️  CPU OCR失败: {e}")
                    results.append("")
            
            return results
            
        except ImportError:
            print("❌ 未安装pytesseract，无法进行OCR")
            return [""] * len(images)
    
    def _cleanup_gpu_memory(self):
        """清理GPU内存"""
        try:
            if self.device == "cuda":
                torch.cuda.empty_cache()
            elif self.device == "mps":
                torch.mps.empty_cache()
        except Exception as e:
            print(f"⚠️  GPU内存清理失败: {e}")
    
    def get_device_info(self) -> dict:
        """获取设备信息"""
        info = {
            "device": self.device,
            "batch_size": self.batch_size,
            "initialized": self.initialized
        }
        
        if self.device == "cuda":
            try:
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_memory"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB"
                info["gpu_memory_used"] = f"{torch.cuda.memory_allocated(0) / 1024**3:.1f}GB"
            except:
                pass
        elif self.device == "mps":
            info["gpu_name"] = "Apple Silicon GPU"
            
        return info
    
    def benchmark(self, test_images: int = 10) -> dict:
        """性能基准测试"""
        if not self.initialized:
            if not self.initialize():
                return {"error": "初始化失败"}
        
        # 创建测试图像
        test_imgs = []
        for i in range(test_images):
            img = Image.new('RGB', (800, 600), color='white')
            test_imgs.append(img)
        
        # 测试处理时间
        start_time = time.time()
        results = self.process_images_batch(test_imgs)
        elapsed = time.time() - start_time
        
        return {
            "images_processed": len(results),
            "total_time": f"{elapsed:.2f}秒",
            "speed": f"{len(results) / elapsed:.1f}张/秒",
            "device": self.device,
            "batch_size": self.batch_size
        }

# 全局实例
gpu_ocr_accelerator = GPUOCRAccelerator()
