"""
搜索结果质量评估模块
"""

import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse

class SearchQualityAnalyzer:
    """搜索结果质量分析器"""
    
    def __init__(self):
        # 权威域名列表 (v2.9.2 扩充)
        self.authority_domains = {
            # 技术与开发
            'github.com', 'stackoverflow.com', 'github.io', 'pypi.org', 'npmjs.com', 
            'mdn.io', 'mozilla.org', 'w3schools.com', 'dev.to', 'medium.com',
            # 官方文档
            'docs.python.org', 'docs.microsoft.com', 'developer.apple.com', 'cloud.google.com',
            'aws.amazon.com', 'react.dev', 'vuejs.org', 'kubernetes.io', 'docker.com',
            # 综合与百科
            'wikipedia.org', 'zhihu.com', 'quora.com', 'arxiv.org', 'researchgate.net',
            # 权威媒体与政务
            'gov.cn', 'edu.cn', 'org.cn', 'gov', 'edu', 'org', 'reuters.com', 'bloomberg.com',
            'news.ycombinator.com', 'techcrunch.com'
        }
        
        # 专业术语关键词 (v2.9.2 扩充 - 中英双语)
        self.professional_keywords = [
            '定义', '概念', '原理', '方法', '标准', '规范', '指标', '部署', '架构',
            '分析', '研究', '报告', '数据', '统计', '调查', '实战', '教程', '指南',
            'API', 'SDK', '算法', '逻辑', '方案', '解决', '性能', '优化', '安全',
            'definition', 'concept', 'principle', 'method', 'standard', 'specification',
            'metrics', 'deployment', 'architecture', 'analysis', 'research', 'report',
            'data', 'statistics', 'survey', 'tutorial', 'guide', 'algorithm', 'logic',
            'solution', 'performance', 'optimization', 'security', 'implementation'
        ]
    
    def analyze_result_quality(self, result: Dict, user_query: str = "") -> Dict:
        """
        分析单个搜索结果的质量 (v2.9.3 增强版)
        增加了基于用户意图的语义相关性分析
        """
        title = result.get('title', '')
        body = result.get('body', '')
        url = result.get('href', '')
        
        # 1. 核心改进：计算语义相关性评分 (Semantic Relevance)
        relevance_score = self._calculate_relevance_score(title, body, user_query)
        
        # 2. 基础质量指标
        authority_score = self._calculate_authority_score(url)
        content_score = self._calculate_content_score(title, body)
        professional_score = self._calculate_professional_score(title, body)
        
        # 3. 噪音判定 (Noise Filter)
        noise_penalty = self._identify_noise(title, body, user_query)
        
        # 综合质量评分 (大幅增加相关性权重)
        total_score = (relevance_score * 0.4 + 
                      authority_score * 0.2 + 
                      content_score * 0.2 + 
                      professional_score * 0.2) - noise_penalty
        
        total_score = max(0.0, min(1.0, total_score))
        
        # 生成质量标签
        quality_label = self._get_quality_label(total_score)
        
        return {
            'quality_score': round(total_score, 2),
            'quality_label': quality_label,
            'relevance_score': relevance_score,
            'is_noise': noise_penalty > 0.3,
            'summary': self._generate_summary(title, body),
            'key_points': self._extract_key_points(body)
        }

    def _calculate_relevance_score(self, title: str, body: str, query: str) -> float:
        """计算内容与用户查询的相关性"""
        if not query: return 0.5
        
        # 提取核心词 (简单分词)
        text = f"{title} {body}".lower()
        query_words = [w for k in re.split(r'[ \-,，]', query.lower()) if (w := k.strip()) and len(w) > 1]
        
        if not query_words: return 0.5
        
        # 统计匹配度
        hit_count = 0
        for word in query_words:
            if word in text:
                hit_count += 1
        
        ratio = hit_count / len(query_words)
        return min(ratio * 1.5, 1.0) # 只要匹配一半以上的词，相关性就很高

    def _identify_noise(self, title: str, body: str, query: str) -> float:
        """识别行业无关噪音 (v2.9.3)"""
        text = f"{title} {body}".lower()
        penalty = 0.0
        
        # 如果是 AI 相关问题，但出现了无关硬件/文件格式词汇
        if 'ai' in query.lower() or '大模型' in query:
            # 噪音词库
            noise_words = ['铁板', '钢板', '铝板', '规格尺寸', 'illustrator', 'photoshop', '军力报告', '五角大楼']
            for word in noise_words:
                if word in text:
                    penalty += 0.5
        
        return penalty
    
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
