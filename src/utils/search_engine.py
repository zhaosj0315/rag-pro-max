"""
搜索引擎 - 全文搜索和智能过滤
"""

import re
import json
from typing import List, Dict, Optional
from pathlib import Path

class SearchEngine:
    def __init__(self):
        self.search_history = []
        self.tags = set()
        
    def full_text_search(self, query: str, documents: List[Dict], fields: List[str] = None) -> List[Dict]:
        """全文搜索"""
        if not query.strip():
            return documents
        
        fields = fields or ['content', 'title', 'filename']
        query_lower = query.lower()
        results = []
        
        for doc in documents:
            score = 0
            matches = []
            
            for field in fields:
                if field in doc and doc[field]:
                    content = str(doc[field]).lower()
                    
                    # 精确匹配
                    if query_lower in content:
                        score += 10
                        # 找到匹配位置
                        start = content.find(query_lower)
                        matches.append({
                            'field': field,
                            'snippet': self._extract_snippet(doc[field], start, query)
                        })
                    
                    # 分词匹配
                    query_words = query_lower.split()
                    for word in query_words:
                        if word in content:
                            score += 1
            
            if score > 0:
                doc_result = doc.copy()
                doc_result['search_score'] = score
                doc_result['matches'] = matches
                results.append(doc_result)
        
        # 按相关性排序
        results.sort(key=lambda x: x['search_score'], reverse=True)
        
        # 记录搜索历史
        self.search_history.append(query)
        if len(self.search_history) > 10:
            self.search_history.pop(0)
        
        return results
    
    def filter_by_tags(self, documents: List[Dict], tags: List[str]) -> List[Dict]:
        """按标签过滤"""
        if not tags:
            return documents
        
        results = []
        for doc in documents:
            doc_tags = doc.get('tags', [])
            if any(tag in doc_tags for tag in tags):
                results.append(doc)
        
        return results
    
    def filter_by_date_range(self, documents: List[Dict], start_date: str = None, end_date: str = None) -> List[Dict]:
        """按日期范围过滤"""
        if not start_date and not end_date:
            return documents
        
        results = []
        for doc in documents:
            doc_date = doc.get('date', '')
            if doc_date:
                if start_date and doc_date < start_date:
                    continue
                if end_date and doc_date > end_date:
                    continue
                results.append(doc)
        
        return results
    
    def filter_by_file_type(self, documents: List[Dict], file_types: List[str]) -> List[Dict]:
        """按文件类型过滤"""
        if not file_types:
            return documents
        
        results = []
        for doc in documents:
            file_type = doc.get('file_type', '').lower()
            if any(ft.lower() in file_type for ft in file_types):
                results.append(doc)
        
        return results
    
    def sort_results(self, documents: List[Dict], sort_by: str = 'relevance', reverse: bool = True) -> List[Dict]:
        """排序结果"""
        if sort_by == 'relevance' and 'search_score' in documents[0] if documents else False:
            return sorted(documents, key=lambda x: x.get('search_score', 0), reverse=reverse)
        elif sort_by == 'date':
            return sorted(documents, key=lambda x: x.get('date', ''), reverse=reverse)
        elif sort_by == 'size':
            return sorted(documents, key=lambda x: x.get('size', 0), reverse=reverse)
        elif sort_by == 'name':
            return sorted(documents, key=lambda x: x.get('filename', ''), reverse=not reverse)
        
        return documents
    
    def _extract_snippet(self, text: str, start_pos: int, query: str, context_length: int = 100) -> str:
        """提取搜索结果片段"""
        if not text or start_pos < 0:
            return ""
        
        # 计算片段范围
        snippet_start = max(0, start_pos - context_length // 2)
        snippet_end = min(len(text), start_pos + len(query) + context_length // 2)
        
        snippet = text[snippet_start:snippet_end]
        
        # 高亮查询词
        highlighted = re.sub(
            f'({re.escape(query)})', 
            r'**\1**', 
            snippet, 
            flags=re.IGNORECASE
        )
        
        # 添加省略号
        if snippet_start > 0:
            highlighted = "..." + highlighted
        if snippet_end < len(text):
            highlighted = highlighted + "..."
        
        return highlighted
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """获取搜索建议"""
        suggestions = []
        
        # 从搜索历史中匹配
        for query in reversed(self.search_history):
            if partial_query.lower() in query.lower() and query not in suggestions:
                suggestions.append(query)
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def add_tag_to_document(self, doc_id: str, tag: str):
        """为文档添加标签"""
        self.tags.add(tag)
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        return sorted(list(self.tags))

# 全局搜索引擎
search_engine = SearchEngine()
