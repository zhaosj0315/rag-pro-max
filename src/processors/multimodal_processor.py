"""多模态处理器 - 支持图片、表格等多模态内容处理"""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import tempfile

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import pandas as pd
    import tabula
    HAS_TABLE_EXTRACTION = True
except ImportError:
    HAS_TABLE_EXTRACTION = False

from ..app_logging import LogManager

logger = LogManager()


class MultimodalProcessor:
    """多模态处理器"""
    
    def __init__(self):
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        self.supported_table_formats = {'.pdf', '.xlsx', '.xls', '.csv'}
        self.ocr_languages = 'chi_sim+eng'  # 中文简体 + 英文
    
    def detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return 'pdf_multimodal'  # PDF可能包含图片和表格，优先处理
        elif ext in self.supported_image_formats:
            return 'image'
        elif ext in self.supported_table_formats:
            return 'table'
        else:
            return 'text'
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """从图片中提取文字"""
        if not HAS_OCR:
            logger.log_warning("OCR功能不可用", "请安装 pillow 和 pytesseract")
            return {'text': '', 'confidence': 0, 'error': 'OCR不可用'}
        
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # OCR识别
            text = pytesseract.image_to_string(image, lang=self.ocr_languages)
            
            # 获取置信度信息
            data = pytesseract.image_to_data(image, lang=self.ocr_languages, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text.strip(),
                'confidence': avg_confidence,
                'word_count': len(text.split()),
                'image_size': image.size,
                'format': image.format
            }
            
        except Exception as e:
            logger.log_error(f"图片OCR失败: {image_path}", str(e))
            return {'text': '', 'confidence': 0, 'error': str(e)}
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """从PDF中提取表格"""
        if not HAS_TABLE_EXTRACTION:
            logger.log_warning("表格提取功能不可用", "请安装 pandas 和 tabula-py")
            return []
        
        try:
            # 使用tabula提取表格
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
            
            extracted_tables = []
            for i, table in enumerate(tables):
                if not table.empty:
                    table_info = {
                        'table_id': f"table_{i+1}",
                        'shape': table.shape,
                        'columns': table.columns.tolist(),
                        'data': table.to_dict('records'),
                        'csv_string': table.to_csv(index=False),
                        'html_string': table.to_html(index=False)
                    }
                    extracted_tables.append(table_info)
            
            return extracted_tables
            
        except Exception as e:
            logger.log_error(f"PDF表格提取失败: {pdf_path}", str(e))
            return []
    
    def extract_tables_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """从Excel中提取表格"""
        if not HAS_TABLE_EXTRACTION:
            return []
        
        try:
            # 读取所有工作表
            excel_file = pd.ExcelFile(excel_path)
            extracted_tables = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                if not df.empty:
                    table_info = {
                        'table_id': f"sheet_{sheet_name}",
                        'sheet_name': sheet_name,
                        'shape': df.shape,
                        'columns': df.columns.tolist(),
                        'data': df.to_dict('records'),
                        'csv_string': df.to_csv(index=False),
                        'html_string': df.to_html(index=False)
                    }
                    extracted_tables.append(table_info)
            
            return extracted_tables
            
        except Exception as e:
            logger.log_error(f"Excel表格提取失败: {excel_path}", str(e))
            return []
    
    def process_multimodal_file(self, file_path: str) -> Dict[str, Any]:
        """处理多模态文件"""
        file_type = self.detect_file_type(file_path)
        result = {
            'file_path': file_path,
            'file_type': file_type,
            'text_content': '',
            'images': [],
            'tables': [],
            'metadata': {}
        }
        
        try:
            if file_type == 'image':
                # 处理图片
                ocr_result = self.extract_text_from_image(file_path)
                result['text_content'] = ocr_result.get('text', '')
                result['images'] = [{
                    'source': file_path,
                    'ocr_result': ocr_result
                }]
                
            elif file_type == 'table' or file_type == 'pdf_multimodal':
                # 处理表格
                if file_path.endswith('.pdf'):
                    tables = self.extract_tables_from_pdf(file_path)
                elif file_path.endswith(('.xlsx', '.xls')):
                    tables = self.extract_tables_from_excel(file_path)
                else:
                    tables = []
                
                result['tables'] = tables
                
                # 将表格内容转换为文本
                table_texts = []
                for table in tables:
                    table_texts.append(f"表格 {table['table_id']}:\n{table['csv_string']}")
                result['text_content'] = '\n\n'.join(table_texts)
            
            # 添加元数据
            result['metadata'] = {
                'file_size': os.path.getsize(file_path),
                'processed_at': pd.Timestamp.now().isoformat() if HAS_TABLE_EXTRACTION else '',
                'has_ocr': HAS_OCR,
                'has_table_extraction': HAS_TABLE_EXTRACTION
            }
            
        except Exception as e:
            logger.log_error(f"多模态文件处理失败: {file_path}", str(e))
            result['error'] = str(e)
        
        return result
    
    async def query(self, kb_name: str, query: str, include_images: bool = True, 
                   include_tables: bool = True, top_k: int = 5) -> Dict[str, Any]:
        """多模态查询"""
        from src.app_logging.log_manager import LogManager
        logger = LogManager()
        
        # ⚠️ MOCK IMPLEMENTATION: Real multimodal retrieval (images/tables) is pending integration.
        logger.warning("执行 MOCK 多模态查询 - v3.2.2 版本功能未完整实现", stage="多模态处理")
        
        # 这里需要集成向量检索，支持文本、图片、表格的混合检索
        
        result = {
            'answer': f'多模态查询结果: {query}',
            'text_sources': [],
            'image_sources': [],
            'table_sources': [],
            'metadata': {
                'kb_name': kb_name,
                'query': query,
                'include_images': include_images,
                'include_tables': include_tables,
                'top_k': top_k
            }
        }
        
        return result
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的格式"""
        return {
            'images': list(self.supported_image_formats),
            'tables': list(self.supported_table_formats),
            'ocr_available': HAS_OCR,
            'table_extraction_available': HAS_TABLE_EXTRACTION
        }
