"""
多模态文档处理器
支持图片、表格理解
"""

import os
import base64
from typing import Dict, List, Any, Optional
from PIL import Image
import pandas as pd
from src.logging import LogManager

logger = LogManager()

class MultimodalProcessor:
    """多模态文档处理器"""
    
    def __init__(self):
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        self.supported_table_formats = ['.xlsx', '.xls', '.csv']
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """处理多模态文档"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        result = {
            "text_content": "",
            "images": [],
            "tables": [],
            "metadata": {}
        }
        
        try:
            if file_ext in self.supported_image_formats:
                result.update(self._process_image(file_path))
            elif file_ext in self.supported_table_formats:
                result.update(self._process_table(file_path))
            elif file_ext == '.pdf':
                result.update(self._process_pdf_multimodal(file_path))
            else:
                # 标准文本处理
                result["text_content"] = self._extract_text(file_path)
            
            logger.info(f"📄 多模态处理完成: {os.path.basename(file_path)}")
            return result
            
        except Exception as e:
            logger.error(f"多模态处理失败: {e}")
            return result
    
    def _process_image(self, image_path: str) -> Dict[str, Any]:
        """处理图片文件"""
        try:
            with Image.open(image_path) as img:
                # 图片基本信息
                image_info = {
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode
                }
                
                # 转换为base64用于存储
                img_base64 = self._image_to_base64(image_path)
                
                # OCR文字识别（简化版）
                ocr_text = self._extract_text_from_image(img)
                
                return {
                    "text_content": ocr_text,
                    "images": [{
                        "path": image_path,
                        "info": image_info,
                        "base64": img_base64,
                        "ocr_text": ocr_text
                    }],
                    "metadata": {"type": "image", "info": image_info}
                }
        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            return {"text_content": "", "images": [], "tables": []}
    
    def _process_table(self, table_path: str) -> Dict[str, Any]:
        """处理表格文件"""
        try:
            file_ext = os.path.splitext(table_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(table_path, encoding='utf-8')
            else:
                df = pd.read_excel(table_path)
            
            # 表格转文本
            table_text = self._table_to_text(df)
            
            # 表格统计信息
            table_info = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            }
            
            return {
                "text_content": table_text,
                "tables": [{
                    "data": df.to_dict('records'),
                    "info": table_info,
                    "text_representation": table_text
                }],
                "metadata": {"type": "table", "info": table_info}
            }
            
        except Exception as e:
            logger.error(f"表格处理失败: {e}")
            return {"text_content": "", "images": [], "tables": []}
    
    def _process_pdf_multimodal(self, pdf_path: str) -> Dict[str, Any]:
        """处理PDF中的多模态内容"""
        try:
            # 这里可以集成更高级的PDF处理库
            # 如 pymupdf, pdfplumber 等来提取图片和表格
            
            result = {
                "text_content": "",
                "images": [],
                "tables": []
            }
            
            # 简化实现：提取文本
            result["text_content"] = self._extract_text(pdf_path)
            
            # TODO: 实现PDF图片和表格提取
            # result["images"] = self._extract_pdf_images(pdf_path)
            # result["tables"] = self._extract_pdf_tables(pdf_path)
            
            return result
            
        except Exception as e:
            logger.error(f"PDF多模态处理失败: {e}")
            return {"text_content": "", "images": [], "tables": []}
    
    def _extract_text_from_image(self, img: Image.Image) -> str:
        """从图片中提取文字（OCR）"""
        try:
            # 简化版OCR实现
            # 实际应用中可以集成 pytesseract 或其他OCR库
            
            # 检查图片是否包含文字（基于图片特征）
            if self._has_text_content(img):
                return f"[图片包含文字内容，尺寸: {img.size}]"
            else:
                return f"[图片内容，尺寸: {img.size}]"
                
        except Exception as e:
            logger.error(f"OCR处理失败: {e}")
            return "[图片内容]"
    
    def _has_text_content(self, img: Image.Image) -> bool:
        """检测图片是否包含文字"""
        # 简化的文字检测逻辑
        # 实际可以使用更复杂的算法
        width, height = img.size
        return width > 100 and height > 50  # 基本尺寸判断
    
    def _table_to_text(self, df: pd.DataFrame) -> str:
        """表格转换为文本"""
        try:
            # 生成表格的文本描述
            text_parts = []
            
            # 表格基本信息
            text_parts.append(f"表格包含 {len(df)} 行 {len(df.columns)} 列")
            text_parts.append(f"列名: {', '.join(df.columns.tolist())}")
            
            # 前几行数据
            if len(df) > 0:
                text_parts.append("\n表格内容:")
                for i, row in df.head(5).iterrows():
                    row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                    text_parts.append(f"第{i+1}行: {row_text}")
                
                if len(df) > 5:
                    text_parts.append(f"... 还有 {len(df)-5} 行数据")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"表格转文本失败: {e}")
            return "表格内容"
    
    def _image_to_base64(self, image_path: str) -> str:
        """图片转base64"""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图片base64转换失败: {e}")
            return ""
    
    def _extract_text(self, file_path: str) -> str:
        """提取文本内容（回退方法）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return "[无法读取文件内容]"
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的格式"""
        return {
            "images": self.supported_image_formats,
            "tables": self.supported_table_formats,
            "multimodal": ['.pdf']
        }

# 全局多模态处理器
multimodal_processor = MultimodalProcessor()
