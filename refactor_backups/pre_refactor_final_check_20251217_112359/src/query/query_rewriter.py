"""
查询改写器模块
负责查询优化和改写建议
"""

import re
from src.app_logging import LogManager

logger = LogManager()


class QueryRewriter:
    """查询改写器"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def should_rewrite(self, query):
        """判断是否需要改写查询"""
        # 检查查询长度
        if len(query) < 5:
            return True, "查询过短"
        
        # 检查是否包含模糊词汇
        vague_words = ['这个', '那个', '怎么样', '如何', '什么', '哪个', '哪些']
        if any(word in query for word in vague_words):
            return True, "包含模糊词汇"
        
        # 检查是否缺少关键信息
        if len(query.split()) < 3 and not any(char in query for char in '？?'):
            return True, "缺少关键信息"
        
        # 检查是否是口语化表达
        colloquial_patterns = [
            r'能不能',
            r'可不可以',
            r'有没有',
            r'行不行',
            r'好不好'
        ]
        
        if any(re.search(pattern, query) for pattern in colloquial_patterns):
            return True, "口语化表达"
        
        return False, "查询清晰"
    
    def suggest_rewrite(self, query):
        """建议查询改写"""
        try:
            prompt = f"""
请优化以下查询，使其更适合知识库检索：

原查询：{query}

优化要求：
1. 使用更具体、准确的词汇
2. 添加必要的上下文信息
3. 避免模糊和口语化表达
4. 保持查询的核心意图不变

请直接返回优化后的查询，不要添加其他解释：
"""
            
            response = self.llm.complete(prompt)
            rewritten = response.text.strip()
            
            # 简单验证改写结果
            if rewritten and rewritten != query and len(rewritten) > len(query) * 0.5:
                logger.info(f"💡 查询改写建议: {query} → {rewritten}")
                return rewritten
            
        except Exception as e:
            logger.error(f"查询改写失败: {e}")
        
        return None
    
    def get_rewrite_suggestions(self, query):
        """获取多个改写建议"""
        suggestions = []
        
        # 基于规则的简单改写
        if '怎么' in query:
            suggestions.append(query.replace('怎么', '如何'))
        
        if '什么是' in query:
            suggestions.append(query.replace('什么是', '') + '的定义和特点')
        
        if query.endswith('？') or query.endswith('?'):
            # 移除问号，添加更具体的描述
            base_query = query.rstrip('？?')
            suggestions.append(f"{base_query}的详细信息")
            suggestions.append(f"关于{base_query}的说明")
        
        # 去重并过滤
        suggestions = list(set(suggestions))
        suggestions = [s for s in suggestions if s != query and len(s) > 5]
        
        return suggestions[:3]  # 最多返回3个建议
    
    def analyze_query_quality(self, query):
        """分析查询质量"""
        score = 100
        issues = []
        
        # 长度检查
        if len(query) < 5:
            score -= 30
            issues.append("查询过短")
        elif len(query) > 200:
            score -= 10
            issues.append("查询过长")
        
        # 词汇检查
        vague_count = sum(1 for word in ['这个', '那个', '怎么样'] if word in query)
        score -= vague_count * 15
        if vague_count > 0:
            issues.append(f"包含{vague_count}个模糊词汇")
        
        # 标点检查
        if not any(char in query for char in '？?。！!'):
            score -= 10
            issues.append("缺少标点符号")
        
        # 关键词密度
        words = query.split()
        if len(words) < 3:
            score -= 20
            issues.append("关键词过少")
        
        return {
            'score': max(0, score),
            'issues': issues,
            'quality': 'excellent' if score >= 90 else 'good' if score >= 70 else 'fair' if score >= 50 else 'poor'
        }
    
    def enhance_query_context(self, query, chat_history=None):
        """基于对话历史增强查询上下文"""
        if not chat_history:
            return query
        
        # 获取最近的对话上下文
        recent_context = []
        for msg in chat_history[-4:]:  # 最近4条消息
            if msg['role'] == 'user':
                recent_context.append(msg['content'])
        
        if not recent_context:
            return query
        
        # 检查是否是延续性问题
        continuation_words = ['它', '这', '那', '他们', '继续', '还有', '另外']
        if any(word in query for word in continuation_words):
            context = ' '.join(recent_context[-2:])  # 最近2个问题
            enhanced_query = f"基于前面关于「{context}」的讨论，{query}"
            logger.info(f"💡 上下文增强: {query} → {enhanced_query}")
            return enhanced_query
        
        return query
