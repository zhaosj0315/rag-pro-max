"""
智能路由器 - 自动判断查询类型
"""
import re
from typing import Tuple

class SmartRouter:
    def __init__(self):
        # SQL关键词
        self.sql_keywords = [
            '统计', '计算', '总计', '平均', '最大', '最小', '数量', '排序', 
            '对比', '汇总', '求和', '多少', '几个', '总共', '分组'
        ]
        
        # RAG关键词  
        self.rag_keywords = [
            '什么是', '如何', '为什么', '解释', '说明', '文档', '资料',
            '介绍', '定义', '原理', '方法', '步骤'
        ]
    
    def route_query(self, query: str) -> Tuple[str, float]:
        """
        路由查询到合适引擎
        Returns: (engine_type, confidence)
        """
        # 计算关键词匹配分数
        sql_score = sum(1 for kw in self.sql_keywords if kw in query)
        rag_score = sum(1 for kw in self.rag_keywords if kw in query)
        
        # 数字模式检测
        has_numbers = bool(re.search(r'\d+|数字|金额|费用|预算|价格', query))
        
        # 决策逻辑
        if sql_score > rag_score:
            confidence = 0.8 + (0.1 if has_numbers else 0)
            return 'sql', confidence
        elif rag_score > sql_score:
            return 'rag', 0.8
        elif has_numbers:
            return 'sql', 0.7
        else:
            return 'rag', 0.6  # 默认RAG
