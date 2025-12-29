"""
搜索结果质量评估模块
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from urllib.parse import urlparse

class SearchQualityAnalyzer:
    """搜索结果质量分析器"""
    
    def __init__(self):
        # 权威域名列表
        self.authority_domains = {
            'gov.cn', 'edu.cn', 'org.cn', 'gov', 'edu', 'org',
            'wikipedia.org', 'baidu.com', 'zhihu.com', 'cnki.net'
        }
        
        # 专业术语关键词
        self.professional_keywords = [
            '定义', '概念', '原理', '方法', '标准', '规范', '指标',
            '分析', '研究', '报告', '数据', '统计', '调查'
        ]
    
    def analyze_result_quality(self, result: Dict) -> Dict:
        """分析单个搜索结果的质量"""
        title = result.get('title', '')
        body = result.get('body', '')
        url = result.get('href', '')
        
        # 计算各项质量指标
        authority_score = self._calculate_authority_score(url)
        content_score = self._calculate_content_score(title, body)
        completeness_score = self._calculate_completeness_score(body)
        professional_score = self._calculate_professional_score(title, body)
        
        # 综合质量评分
        total_score = (authority_score * 0.3 + 
                      content_score * 0.3 + 
                      completeness_score * 0.2 + 
                      professional_score * 0.2)
        
        # 生成质量标签
        quality_label = self._get_quality_label(total_score)
        
        # 提取关键信息
        key_points = self._extract_key_points(body)
        
        return {
            'quality_score': round(total_score, 2),
            'quality_label': quality_label,
            'authority_score': authority_score,
            'content_score': content_score,
            'completeness_score': completeness_score,
            'professional_score': professional_score,
            'key_points': key_points,
            'summary': self._generate_summary(title, body)
        }
    
    def _calculate_authority_score(self, url: str) -> float:
        """计算来源权威性评分"""
        if not url:
            return 0.3
            
        domain = urlparse(url).netloc.lower()
        
        # 检查是否为权威域名
        for auth_domain in self.authority_domains:
            if auth_domain in domain:
                return 0.9
        
        # 检查域名特征
        if any(x in domain for x in ['gov', 'edu', 'org']):
            return 0.8
        elif any(x in domain for x in ['baidu', 'zhihu', 'wikipedia']):
            return 0.7
        elif domain.endswith('.com'):
            return 0.6
        else:
            return 0.4
    
    def _calculate_content_score(self, title: str, body: str) -> float:
        """计算内容质量评分"""
        if not body:
            return 0.2
        
        score = 0.5  # 基础分
        
        # 内容长度评分
        if len(body) > 500:
            score += 0.2
        elif len(body) > 200:
            score += 0.1
        
        # 结构化程度
        if '。' in body or '.' in body:
            score += 0.1
        if any(x in body for x in ['：', ':', '（', '(']):
            score += 0.1
        
        # 标题相关性
        if title and any(word in body for word in title.split()[:3]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_completeness_score(self, body: str) -> float:
        """计算内容完整性评分"""
        if not body:
            return 0.2
        
        score = 0.5
        
        # 检查是否被截断
        if body.endswith('...') or body.endswith('…'):
            score -= 0.3
        
        # 检查内容结构
        sentences = re.split(r'[。.!！?？]', body)
        if len(sentences) >= 3:
            score += 0.3
        elif len(sentences) >= 2:
            score += 0.2
        
        # 检查是否有完整段落
        if '\n' in body or len(body) > 300:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_professional_score(self, title: str, body: str) -> float:
        """计算专业性评分"""
        text = f"{title} {body}".lower()
        
        # 统计专业术语出现次数
        professional_count = sum(1 for keyword in self.professional_keywords 
                               if keyword in text)
        
        # 检查数字和数据
        number_count = len(re.findall(r'\d+', text))
        
        score = min(professional_count * 0.1 + number_count * 0.05, 1.0)
        return max(score, 0.2)  # 最低0.2分
    
    def _get_quality_label(self, score: float) -> Tuple[str, str]:
        """根据评分生成质量标签"""
        if score >= 0.8:
            return ("🏆", "高质量")
        elif score >= 0.6:
            return ("⭐", "中等质量")
        else:
            return ("⚠️", "需验证")
    
    def _extract_key_points(self, body: str) -> List[str]:
        """提取关键信息点"""
        if not body:
            return []
        
        # 按句子分割
        sentences = re.split(r'[。.!！?？]', body)
        
        # 筛选关键句子（包含重要词汇的句子）
        key_sentences = []
        for sentence in sentences[:5]:  # 只取前5句
            sentence = sentence.strip()
            if len(sentence) > 10 and any(keyword in sentence 
                                        for keyword in self.professional_keywords):
                key_sentences.append(sentence)
        
        return key_sentences[:3]  # 最多返回3个要点
    
    def _generate_summary(self, title: str, body: str) -> str:
        """生成智能摘要"""
        if not body:
            return title or "无内容摘要"
        
        # 取前200字符作为摘要
        summary = body[:200].strip()
        
        # 如果被截断，尝试在句号处截断
        if len(body) > 200:
            last_period = summary.rfind('。')
            if last_period > 100:
                summary = summary[:last_period + 1]
            else:
                summary += "..."
        
        return summary

# 全局实例
search_quality_analyzer = SearchQualityAnalyzer()
