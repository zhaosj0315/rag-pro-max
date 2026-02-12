import re
import os
from typing import Optional, Tuple, List
from src.kb.kb_manager import KBManager
from src.app_logging import LogManager
from src.auth.session_manager import get_visible_kbs

logger = LogManager()

class MentionRouter:
    """
    跨域引用路由器
    解析用户输入中的 @KB_Name 语法，实现跨库即时调用
    """
    
    def __init__(self):
        self.kb_manager = KBManager()
        
    def parse_mention(self, user_input: str, username: str = 'guest', role: str = 'guest') -> Tuple[Optional[List[str]], str]:
        """
        解析输入，返回 (目标KB候选列表, 实际问题)
        支持单目标 (@name) 和 多目标 (@MULTI:name1|name2)
        """
        # 0. 优先检查多目标内部协议
        if user_input.startswith("@MULTI:"):
            try:
                # 格式: @MULTI:KB1|KB2 实际问题
                header, query = user_input.split(" ", 1)
                targets = header[7:].split("|")
                return targets, query
            except ValueError:
                return None, user_input

        # 匹配模式: @目标 [空格] 问题
        match = re.match(r'^@(\S+)\s+(.*)', user_input.strip())
        # ... (rest is same)
        
        target_hint = None
        actual_query = user_input
        
        if match:
            target_hint = match.group(1)
            actual_query = match.group(2)
        else:
            # 尝试匹配无空格但以@开头的情况
            match_tight = re.match(r'^@([^\s，,。?？]+)[，,。?？\s]*(.*)', user_input.strip())
            if match_tight:
                target_hint = match_tight.group(1)
                actual_query = match_tight.group(2) or user_input

        if not target_hint:
            return None, user_input

        # 执行模糊匹配找到真实的 KB ID 列表 (带权限校验)
        candidates = self._fuzzy_match_kb(target_hint, username, role)
        
        return candidates, actual_query

    def _fuzzy_match_kb(self, hint: str, username: str, role: str) -> Optional[List[str]]:
        """
        模糊匹配知识库名称，返回匹配到的所有候选列表
        """
        all_kbs = self.kb_manager.list_all()
        
        # [Security] 权限过滤：只保留用户可见的 KB
        allowed_kbs = get_visible_kbs(username, role, all_kbs)
        
        # [Fix] 过滤掉纯对话虚拟库
        allowed_kbs = [k for k in allowed_kbs if not k.endswith('_pure_chat') and k != 'pure_chat']
        
        # 1. 精确匹配
        if hint in allowed_kbs:
            return [hint]
            
        candidates = []
        
        # 2. 前缀/包含匹配
        for kb in allowed_kbs:
            if hint.lower() in kb.lower():
                candidates.append(kb)
        
        if not candidates:
            return None
            
        # 按长度排序 (通常最短的那个最接近 hint)
        candidates.sort(key=len)
        return candidates

    @staticmethod
    def is_mention_format(text: str) -> bool:
        return text.strip().startswith("@")
