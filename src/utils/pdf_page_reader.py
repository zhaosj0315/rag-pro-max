"""
PDF页码读取器 - 支持记录页码信息的PDF处理
"""

import os
from typing import List, Dict, Any
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class PDFPageReader(BaseReader):
    """支持页码记录的PDF读取器"""
    
    def __init__(self):
        self.supported_suffixes = [".pdf"]
    
    def load_data(self, file_path: str, extra_info: Dict[str, Any] = None) -> List[Document]:
        """
        加载PDF文档，每页作为一个Document，包含页码信息
        
        Args:
            file_path: PDF文件路径
            extra_info: 额外的元数据信息
            
        Returns:
            List[Document]: 文档列表，每个文档包含页码信息
        """
        # 安全检查：路径验证
        if not file_path or not isinstance(file_path, str):
            raise ValueError("文件路径无效")
        
        # 规范化路径，防止路径遍历攻击
        file_path = os.path.abspath(file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检查文件扩展名
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("文件必须是PDF格式")
        
        # 检查文件权限
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"文件无读取权限: {file_path}")
        
        documents = []
        base_metadata = extra_info or {}
        base_metadata.update({
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_type': 'pdf'
        })
        
        # 优先使用PyMuPDF，其次PyPDF2
        if HAS_PYMUPDF:
            documents = self._read_with_pymupdf(file_path, base_metadata)
        elif HAS_PYPDF2:
            documents = self._read_with_pypdf2(file_path, base_metadata)
        else:
            # 回退到SimpleDirectoryReader
            from llama_index.core import SimpleDirectoryReader
            reader = SimpleDirectoryReader(input_files=[file_path])
            docs = reader.load_data()
            
            # 为没有页码信息的文档添加默认页码
            for i, doc in enumerate(docs):
                doc.metadata.update(base_metadata)
                doc.metadata['page_number'] = i + 1
                doc.metadata['total_pages'] = len(docs)
                documents.append(doc)
        
        return documents
    
    def _read_with_pymupdf(self, file_path: str, base_metadata: Dict) -> List[Document]:
        """使用PyMuPDF读取PDF"""
        documents = []
        
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # 只处理有文本的页面
                    metadata = base_metadata.copy()
                    metadata.update({
                        'page_number': page_num + 1,
                        'total_pages': total_pages,
                        'page_label': f"第{page_num + 1}页"
                    })
                    
                    document = Document(
                        text=text,
                        metadata=metadata
                    )
                    documents.append(document)
            
            doc.close()
            
        except Exception as e:
            raise Exception(f"PyMuPDF读取失败: {e}")
        
        return documents
    
    def _read_with_pypdf2(self, file_path: str, base_metadata: Dict) -> List[Document]:
        """使用PyPDF2读取PDF"""
        documents = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    if text.strip():  # 只处理有文本的页面
                        metadata = base_metadata.copy()
                        metadata.update({
                            'page_number': page_num + 1,
                            'total_pages': total_pages,
                            'page_label': f"第{page_num + 1}页"
                        })
                        
                        document = Document(
                            text=text,
                            metadata=metadata
                        )
                        documents.append(document)
                        
        except Exception as e:
            raise Exception(f"PyPDF2读取失败: {e}")
        
        return documents


def read_pdf_with_pages(file_path: str, extra_info: Dict[str, Any] = None) -> List[Document]:
    """
    便捷函数：读取PDF并返回包含页码信息的文档列表
    
    Args:
        file_path: PDF文件路径
        extra_info: 额外的元数据信息
        
    Returns:
        List[Document]: 包含页码信息的文档列表
    """
    reader = PDFPageReader()
    return reader.load_data(file_path, extra_info)
