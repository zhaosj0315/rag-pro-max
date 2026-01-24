"""
系统提示词管理器
负责管理和持久化多角色的系统提示词 (System Prompts)
"""

import json
import os
import uuid
from typing import List, Dict

PROMPTS_FILE = "config/system_prompts.json"

DEFAULT_PROMPTS = [
    {
        "id": "default",
        "name": "🤖 默认助手 (Default)",
        "content": "你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。"
    },
    {
        "id": "coder",
        "name": "👨‍💻 代码专家 (Coder)",
        "content": "你是一个资深全栈工程师。请基于上下文提供高质量、生产就绪的代码示例。优先使用 Python/TypeScript。解释核心逻辑，并遵循最佳实践。"
    },
    {
        "id": "analyst",
        "name": "📊 数据分析师 (Analyst)",
        "content": "你是一个商业数据分析师。请从提供的文档中提取关键数据、趋势和洞察。回答应结构化，多使用列表和 Markdown 表格进行对比分析。"
    },
    {
        "id": "creative",
        "name": "🎨 创意文案 (Creative)",
        "content": "你是一个富有创意的文案策划。请基于已有知识进行发散性思维，生成吸引人的标题、标语或营销文案。语气可以生动活泼。"
    },
    {
        "id": "academic",
        "name": "🎓 学术顾问 (Academic)",
        "content": "你是一个严谨的学术顾问。请基于文档内容撰写学术风格的回答，引用来源，保持中立客观，避免使用口语化表达。"
    }
]

class PromptManager:
    """提示词管理器类"""
    
    @staticmethod
    def load_prompts() -> List[Dict]:
        """加载所有提示词"""
        if not os.path.exists(PROMPTS_FILE):
            # 初始化默认配置
            PromptManager.save_all(DEFAULT_PROMPTS)
            return DEFAULT_PROMPTS
        try:
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data: return DEFAULT_PROMPTS
                return data
        except:
            return DEFAULT_PROMPTS

    @staticmethod
    def save_all(prompts: List[Dict]):
        """保存所有提示词"""
        os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

    @staticmethod
    def add_prompt(name: str, content: str) -> str:
        """添加新提示词"""
        prompts = PromptManager.load_prompts()
        new_id = str(uuid.uuid4())[:8]
        new_prompt = {
            "id": new_id,
            "name": name,
            "content": content
        }
        prompts.append(new_prompt)
        PromptManager.save_all(prompts)
        return new_id

    @staticmethod
    def delete_prompt(prompt_id: str) -> bool:
        """删除提示词 (保护默认提示词)"""
        if prompt_id in ["default", "coder", "analyst"]: 
            return False
        
        prompts = PromptManager.load_prompts()
        original_len = len(prompts)
        prompts = [p for p in prompts if p['id'] != prompt_id]
        
        if len(prompts) < original_len:
            PromptManager.save_all(prompts)
            return True
        return False

    @staticmethod
    def update_prompt(prompt_id: str, name: str, content: str) -> bool:
        """更新提示词"""
        prompts = PromptManager.load_prompts()
        for p in prompts:
            if p['id'] == prompt_id:
                p['name'] = name
                p['content'] = content
                PromptManager.save_all(prompts)
                return True
        return False

    @staticmethod
    def get_content(prompt_id: str) -> str:
        """获取特定提示词的内容"""
        prompts = PromptManager.load_prompts()
        for p in prompts:
            if p['id'] == prompt_id:
                return p['content']
        return DEFAULT_PROMPTS[0]['content']
