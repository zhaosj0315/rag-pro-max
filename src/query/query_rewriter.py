"""
查询改写模块 - Query Rewriter
自动优化用户查询，提升检索准确率
"""

from typing import Optional, Tuple
from llama_index.core.llms import LLM


class QueryRewriter:
    """查询改写器"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
    
    def should_rewrite(self, query: str, top_score: float = 0.0) -> Tuple[bool, str]:
        """
        判断是否需要改写
        
        Args:
            query: 用户查询
            top_score: 检索结果最高分数
            
        Returns:
            (是否需要改写, 原因)
        """
        # 查询过短
        if len(query.strip()) < 5:
            return True, "查询过短"
        
        # 检索结果相似度低
        if top_score > 0 and top_score < 0.5:
            return True, "检索结果相似度低"
        
        # 包含口语化表达
        casual_words = ["啥", "咋", "咋样", "咋办", "啥意思", "干啥的"]
        if any(word in query for word in casual_words):
            return True, "包含口语化表达"
        
        return False, ""
    
    def rewrite(self, query: str, context: Optional[str] = None) -> str:
        """
        改写查询
        
        Args:
            query: 原始查询
            context: 对话上下文（可选）
            
        Returns:
            改写后的查询
        """
        prompt = f"""你是一个查询优化助手。请将用户的问题改写得更清晰、具体，便于检索。

原问题：{query}"""
        
        if context:
            prompt += f"\n对话上下文：{context}"
        
        prompt += """

要求：
1. 保持原意，补充必要信息
2. 使用规范的书面语
3. 明确查询意图
4. 只返回改写后的问题，不要解释

改写后的问题："""
        
        try:
            response = self.llm.complete(prompt)
            rewritten = response.text.strip()
            
            # 清理可能的引号
            rewritten = rewritten.strip('"\'""''')
            
            return rewritten if rewritten else query
        except Exception as e:
            print(f"查询改写失败: {e}")
            return query
    
    def suggest_rewrite(self, query: str, context: Optional[str] = None) -> Optional[str]:
        """
        建议改写（不强制）
        
        Args:
            query: 原始查询
            context: 对话上下文
            
        Returns:
            改写建议，如果不需要改写则返回 None
        """
        should, reason = self.should_rewrite(query)
        if not should:
            return None
        
        return self.rewrite(query, context)
