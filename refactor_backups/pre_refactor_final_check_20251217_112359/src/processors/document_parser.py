"""
文档解析器
提取自 apppro.py 的文档解析函数
"""

import warnings
from typing import List, Dict, Any


class DocumentParser:
    """文档解析器"""
    
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        warnings.filterwarnings('ignore')
    
    def parse_single_doc(self, doc_text: str) -> List[Dict[str, Any]]:
        """
        单个文档解析（多进程安全）- 返回字典而非对象
        
        Args:
            doc_text: 文档文本
            
        Returns:
            List[Dict]: 文档块列表
        """
        chunks = []
        
        # 预处理：清理和标准化文本
        doc_text = doc_text.strip()
        lines = doc_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                line = ' '.join(line.split())
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        
        # 分块处理
        for i in range(0, len(cleaned_text), self.chunk_size - self.chunk_overlap):
            chunk = cleaned_text[i:i + self.chunk_size]
            if chunk.strip():
                word_count = len(chunk.split())
                char_count = len(chunk)
                
                chunks.append({
                    'text': chunk,
                    'start_idx': i,
                    'word_count': word_count,
                    'char_count': char_count
                })
        
        return chunks
    
    def parse_batch_docs(self, doc_texts_batch: List[str]) -> List[Dict[str, Any]]:
        """
        批量处理文档（减少进程间通信）
        
        Args:
            doc_texts_batch: 文档文本列表
            
        Returns:
            List[Dict]: 所有文档块列表
        """
        all_chunks = []
        for doc_text in doc_texts_batch:
            chunks = self.parse_single_doc(doc_text)
            all_chunks.extend(chunks)
        return all_chunks


# 全局解析器实例
_parser = None

def get_document_parser(chunk_size: int = 1024, chunk_overlap: int = 100) -> DocumentParser:
    """获取文档解析器实例"""
    global _parser
    if _parser is None:
        _parser = DocumentParser(chunk_size, chunk_overlap)
    return _parser

# 兼容性函数（保持原有接口）
def _parse_single_doc(doc_text: str) -> List[Dict[str, Any]]:
    """兼容性函数"""
    parser = get_document_parser()
    return parser.parse_single_doc(doc_text)

def _parse_batch_docs(doc_texts_batch: List[str]) -> List[Dict[str, Any]]:
    """兼容性函数"""
    parser = get_document_parser()
    return parser.parse_batch_docs(doc_texts_batch)
