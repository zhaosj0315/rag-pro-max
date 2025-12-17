#!/usr/bin/env python3
"""
文件服务模块 - 统一文件处理逻辑
"""

import os
import mimetypes
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class FileService:
    """统一的文件处理服务"""
    
    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {
        '.txt', '.md', '.pdf', '.docx', '.doc', '.xlsx', '.xls', 
        '.pptx', '.ppt', '.csv', '.json', '.html', '.htm', '.zip'
    }
    
    # 文件大小限制 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    def __init__(self):
        self.processed_files = []
        self.failed_files = []
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        验证文件是否可以处理
        
        Returns:
            dict: 验证结果 {'valid': bool, 'reason': str, 'info': dict}
        """
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'reason': '文件不存在', 'info': {}}
            
            if not os.path.isfile(file_path):
                return {'valid': False, 'reason': '不是文件', 'info': {}}
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                return {
                    'valid': False, 
                    'reason': f'文件过大 ({file_size / 1024 / 1024:.1f}MB > 100MB)', 
                    'info': {'size': file_size}
                }
            
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                return {
                    'valid': False, 
                    'reason': f'不支持的文件类型: {file_ext}', 
                    'info': {'extension': file_ext}
                }
            
            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                return {'valid': False, 'reason': '文件无读取权限', 'info': {}}
            
            # 获取文件信息
            file_info = {
                'size': file_size,
                'extension': file_ext,
                'mime_type': mimetypes.guess_type(file_path)[0],
                'name': os.path.basename(file_path),
                'modified': os.path.getmtime(file_path)
            }
            
            return {'valid': True, 'reason': '验证通过', 'info': file_info}
            
        except Exception as e:
            return {'valid': False, 'reason': f'验证失败: {str(e)}', 'info': {}}
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """获取文件统计信息"""
        from src.common.utils import get_file_stats
        return get_file_stats(file_path)
    
    def process_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        处理单个文件
        
        Returns:
            dict: 处理结果 {'success': bool, 'content': str, 'metadata': dict, 'error': str}
        """
        # 验证文件
        validation = self.validate_file(file_path)
        if not validation['valid']:
            return {
                'success': False,
                'content': '',
                'metadata': validation['info'],
                'error': validation['reason']
            }
        
        try:
            # 提取文件内容
            content = self.extract_content(file_path, **kwargs)
            
            if content:
                self.processed_files.append(file_path)
                return {
                    'success': True,
                    'content': content,
                    'metadata': validation['info'],
                    'error': ''
                }
            else:
                self.failed_files.append(file_path)
                return {
                    'success': False,
                    'content': '',
                    'metadata': validation['info'],
                    'error': '内容提取失败'
                }
                
        except Exception as e:
            self.failed_files.append(file_path)
            return {
                'success': False,
                'content': '',
                'metadata': validation.get('info', {}),
                'error': f'处理失败: {str(e)}'
            }
    
    def extract_content(self, file_path: str, **kwargs) -> str:
        """
        提取文件内容
        
        Args:
            file_path: 文件路径
            **kwargs: 额外参数
            
        Returns:
            str: 提取的文本内容
        """
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.txt':
                return self._extract_txt(file_path)
            elif file_ext == '.md':
                return self._extract_markdown(file_path)
            elif file_ext == '.pdf':
                return self._extract_pdf(file_path, **kwargs)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_word(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self._extract_excel(file_path)
            elif file_ext == '.csv':
                return self._extract_csv(file_path)
            elif file_ext == '.json':
                return self._extract_json(file_path)
            elif file_ext in ['.html', '.htm']:
                return self._extract_html(file_path)
            else:
                return f"不支持的文件类型: {file_ext}"
                
        except Exception as e:
            raise Exception(f"内容提取失败: {str(e)}")
    
    def _extract_txt(self, file_path: str) -> str:
        """提取TXT文件内容"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _extract_markdown(self, file_path: str) -> str:
        """提取Markdown文件内容"""
        return self._extract_txt(file_path)
    
    def _extract_pdf(self, file_path: str, **kwargs) -> str:
        """提取PDF文件内容"""
        try:
            import PyMuPDF as fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                return text
            except ImportError:
                return "PDF处理库未安装 (需要 PyMuPDF 或 PyPDF2)"
    
    def _extract_word(self, file_path: str) -> str:
        """提取Word文档内容"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            return "Word处理库未安装 (需要 python-docx)"
    
    def _extract_excel(self, file_path: str) -> str:
        """提取Excel文件内容"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string()
        except ImportError:
            return "Excel处理库未安装 (需要 pandas 和 openpyxl)"
    
    def _extract_csv(self, file_path: str) -> str:
        """提取CSV文件内容"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_string()
        except ImportError:
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                return '\n'.join([','.join(row) for row in reader])
    
    def _extract_json(self, file_path: str) -> str:
        """提取JSON文件内容"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _extract_html(self, file_path: str) -> str:
        """提取HTML文件内容"""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text()
        except ImportError:
            # 简单的HTML标签移除
            import re
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()
                return re.sub(r'<[^>]+>', '', html)
    
    def process_batch(self, file_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        批量处理文件
        
        Returns:
            dict: 批量处理结果
        """
        results = []
        success_count = 0
        
        for file_path in file_paths:
            result = self.process_file(file_path, **kwargs)
            results.append({
                'file_path': file_path,
                'result': result
            })
            if result['success']:
                success_count += 1
        
        return {
            'total': len(file_paths),
            'success': success_count,
            'failed': len(file_paths) - success_count,
            'results': results
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'processed_files': len(self.processed_files),
            'failed_files': len(self.failed_files),
            'success_rate': len(self.processed_files) / (len(self.processed_files) + len(self.failed_files)) if (len(self.processed_files) + len(self.failed_files)) > 0 else 0
        }

# 全局文件服务实例
_file_service = None

def get_file_service() -> FileService:
    """获取文件服务实例"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
