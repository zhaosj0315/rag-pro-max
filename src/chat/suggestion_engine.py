"""推荐问题生成引擎 - v1.5.1 增强版"""

import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from src.chat_utils_improved import generate_follow_up_questions_safe


class SuggestionEngine:
    """推荐问题生成引擎"""
    
    def __init__(self, kb_name: Optional[str] = None):
        self.kb_name = kb_name
        self.history = []
        self.queue = []
        self.custom_suggestions = []  # 用户自定义推荐
        self.history_file = None
        
        if kb_name:
            self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        if not self.kb_name:
            return
        
        history_dir = "suggestion_history"
        os.makedirs(history_dir, exist_ok=True)
        self.history_file = os.path.join(history_dir, f"{self.kb_name}_suggestions.json")
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('history', [])
                    self.custom_suggestions = data.get('custom', [])
            except:
                pass
    
    def _save_history(self):
        """保存历史记录"""
        if not self.history_file:
            return
        
        try:
            data = {
                'kb_name': self.kb_name,
                'history': self.history[-100:],  # 只保留最近100条
                'custom': self.custom_suggestions,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def generate(
        self,
        context: str,
        num_questions: int = 3,
        existing_questions: Optional[List[str]] = None,
        query_engine = None,
        use_custom: bool = True
    ) -> List[str]:
        """生成推荐问题
        
        Args:
            context: 上下文
            num_questions: 生成数量
            existing_questions: 已存在的问题
            query_engine: 查询引擎
            use_custom: 是否优先使用自定义推荐
        """
        # 优先返回自定义推荐
        if use_custom and self.custom_suggestions:
            available_custom = [
                q for q in self.custom_suggestions 
                if q not in (existing_questions or [])
            ]
            if available_custom:
                return available_custom[:num_questions]
        
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
        self._save_history()
        
        return new_questions
    
    def add_custom_suggestion(self, question: str):
        """添加自定义推荐问题"""
        if question and question not in self.custom_suggestions:
            self.custom_suggestions.append(question)
            self._save_history()
            return True
        return False
    
    def remove_custom_suggestion(self, question: str):
        """删除自定义推荐问题"""
        if question in self.custom_suggestions:
            self.custom_suggestions.remove(question)
            self._save_history()
            return True
        return False
    
    def get_custom_suggestions(self) -> List[str]:
        """获取所有自定义推荐"""
        return self.custom_suggestions.copy()
    
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
        self._save_history()
    
    def clear_queue(self):
        """清空队列"""
        self.queue.clear()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "history_count": len(self.history),
            "queue_count": len(self.queue),
            "custom_count": len(self.custom_suggestions)
        }
    
    def get_history(self, limit: int = 10) -> List[str]:
        """获取历史记录"""
        return self.history[-limit:]
