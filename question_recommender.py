#!/usr/bin/env python3
"""
智能问题推荐器
"""
import re
from typing import List

class QuestionRecommender:
    def __init__(self):
        self.question_templates = [
            "这个文档的主要观点是什么？",
            "能否详细解释一下{}？",
            "{}的优缺点有哪些？",
            "如何实际应用{}？",
            "{}与其他方案相比有什么特点？"
        ]
    
    def recommend_questions(self, document_content: str) -> List[str]:
        """基于文档内容推荐问题"""
        # 提取关键词
        keywords = self._extract_keywords(document_content)
        
        # 生成推荐问题
        questions = []
        for keyword in keywords[:3]:  # 取前3个关键词
            for template in self.question_templates[:2]:  # 取前2个模板
                if "{}" in template:
                    questions.append(template.format(keyword))
                else:
                    questions.append(template)
        
        return questions[:5]  # 返回前5个问题
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词（简化版）"""
        # 简单的关键词提取
        words = re.findall(r'\b[\w]{3,}\b', content)
        # 过滤常见词汇
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而'}
        keywords = [w for w in words if w not in stop_words]
        
        # 返回出现频率最高的词
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
