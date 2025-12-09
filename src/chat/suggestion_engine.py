"""推荐问题生成引擎"""

from typing import List, Optional
from src.chat_utils_improved import generate_follow_up_questions_safe


class SuggestionEngine:
    """推荐问题生成引擎"""
    
    def __init__(self):
        self.history = []
        self.queue = []
    
    def generate(
        self,
        context: str,
        num_questions: int = 3,
        existing_questions: Optional[List[str]] = None,
        query_engine = None
    ) -> List[str]:
        """生成推荐问题"""
        # 合并所有已存在的问题
        all_existing = existing_questions or []
        all_existing.extend(self.history)
        all_existing.extend(self.queue)
        
        # 生成新问题
        questions = generate_follow_up_questions_safe(
            context_text=context,
            num_questions=num_questions,
            existing_questions=all_existing,
            query_engine=query_engine
        )
        
        # 去重
        new_questions = [q for q in questions if q not in self.history]
        
        # 添加到历史
        self.history.extend(new_questions)
        
        return new_questions
    
    def add_to_queue(self, question: str):
        """添加问题到队列"""
        if question not in self.queue:
            self.queue.append(question)
    
    def pop_from_queue(self) -> Optional[str]:
        """从队列取出问题"""
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def clear_history(self):
        """清空历史"""
        self.history.clear()
    
    def clear_queue(self):
        """清空队列"""
        self.queue.clear()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "history_count": len(self.history),
            "queue_count": len(self.queue)
        }
