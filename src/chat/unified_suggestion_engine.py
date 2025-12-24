"""
统一推荐问题生成引擎
整合所有推荐问题生成功能，避免重复建设
"""

import json
import os
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime

class UnifiedSuggestionEngine:
    """统一推荐问题生成引擎"""
    
    def __init__(self, kb_name: Optional[str] = None):
        self.kb_name = kb_name
        self.history = []
        self.custom_suggestions = []
        self._load_config()
    
    def _load_config(self):
        """加载配置和历史"""
        if not self.kb_name:
            return
        
        config_dir = "suggestion_config"
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, f"{self.kb_name}_config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('history', [])[-50:]  # 只保留最近50条
                    self.custom_suggestions = data.get('custom', [])
            except:
                pass
    
    def generate_suggestions(self, 
                           context: str,
                           source_type: str = 'chat',  # 'file_upload' | 'web_crawl' | 'chat'
                           query_engine = None,
                           metadata: Dict = None,
                           num_questions: int = 3,
                           existing_history: List[str] = None) -> List[str]:
        """
        统一的推荐问题生成入口
        
        Args:
            context: 上下文内容（回答内容或文档内容）
            source_type: 来源类型
            query_engine: 查询引擎，用于验证问题可答性
            metadata: 元数据（URL、文件信息等）
            num_questions: 生成问题数量
            existing_history: 已存在的历史问题列表（用于过滤）
        """
        suggestions = []
        
        # 1. 优先使用自定义推荐
        if self.custom_suggestions:
            suggestions.extend(self.custom_suggestions[:2])
        
        # 2. 基于来源类型生成特定问题
        if source_type == 'web_crawl':
            suggestions.extend(self._generate_web_questions(context, metadata))
        elif source_type == 'file_upload':
            suggestions.extend(self._generate_file_questions(context, metadata))
        else:  # chat
            suggestions.extend(self._generate_chat_questions(context))
        
        # 3. 基于知识库内容生成验证过的问题
        if query_engine:
            kb_questions = self._generate_kb_aware_questions(context, query_engine)
            suggestions.extend(kb_questions)
        
        # 4. 去重、过滤历史、验证可答性
        final_suggestions = self._filter_and_validate(suggestions, query_engine, existing_history)
        
        # 5. 更新历史
        self.history.extend(final_suggestions)
        self._save_config()
        
        return final_suggestions[:num_questions]
    
    def _generate_web_questions(self, context: str, metadata: Dict) -> List[str]:
        """生成网页抓取相关问题"""
        questions = []
        
        if not metadata:
            return ["网站的主要内容是什么？", "有哪些重要信息？"]
        
        url = metadata.get('url', '')
        domain = urlparse(url).netloc.lower().replace('www.', '') if url else ''
        
        # 基于域名的问题模板
        domain_templates = {
            'python.org': ["Python有哪些主要特性？", "如何开始学习Python？"],
            'github.com': ["这个项目的主要功能是什么？", "如何安装和使用？"],
            'stackoverflow.com': ["这个问题的解决方案是什么？", "有其他解决方法吗？"],
            'docs.': ["这个功能如何使用？", "有使用示例吗？"]
        }
        
        for key, templates in domain_templates.items():
            if key in domain:
                questions.extend(templates)
                break
        
        # 基于内容关键词
        content_lower = context.lower()
        if 'tutorial' in content_lower or '教程' in content_lower:
            questions.append("这个教程涵盖了哪些内容？")
        if 'api' in content_lower:
            questions.append("这个API如何调用？")
        if 'install' in content_lower or '安装' in content_lower:
            questions.append("安装过程中可能遇到什么问题？")
        
        return questions[:3]
    
    def _generate_file_questions(self, context: str, metadata: Dict) -> List[str]:
        """生成文件上传相关问题"""
        questions = []
        
        if not metadata:
            return ["文档的主要内容是什么？", "有哪些关键信息？"]
        
        file_type = metadata.get('file_type', '').lower()
        file_name = metadata.get('file_name', '').lower()
        
        # 基于文件类型
        if file_type in ['pdf', 'doc', 'docx']:
            questions.extend([
                "文档中提到的具体方法是什么？",
                "有哪些实际案例或示例？",
                "文档的核心观点是什么？"
            ])
        elif file_type in ['txt', 'md']:
            questions.extend([
                "文本中的关键要点有哪些？",
                "如何实际应用这些内容？"
            ])
        
        # 基于文件名推断内容
        if any(word in file_name for word in ['研究', 'research', '分析', 'analysis']):
            questions.append("研究的主要结论是什么？")
        if any(word in file_name for word in ['指南', 'guide', '教程', 'tutorial']):
            questions.append("具体的操作步骤是什么？")
        if any(word in file_name for word in ['报告', 'report', '总结', 'summary']):
            questions.append("报告中的关键数据有哪些？")
        
        return questions[:3]
    
    def _generate_chat_questions(self, context: str) -> List[str]:
        """生成对话相关问题"""
        questions = []
        
        # 基于回答内容特征
        if any(word in context for word in ['方案', '解决', '处理', '应对', '建议', '做法']):
            questions.extend([
                "这个方案的具体实施步骤是什么？",
                "可能遇到哪些实际问题？",
                "有没有其他替代方案？"
            ])
        elif any(word in context for word in ['分析', '研究', '数据', '结果', '统计']):
            questions.extend([
                "这个分析的数据来源是什么？",
                "结论的可靠性如何？",
                "还有哪些相关的研究？"
            ])
        elif any(word in context for word in ['原理', '机制', '原因', '为什么', '心态', '要点']):
            questions.extend([
                "背后的具体原理是什么？",
                "这种机制如何运作？",
                "有哪些影响因素？"
            ])
        elif any(word in context for word in ['时间', '管理', '效率', '工作', '习惯']):
            questions.extend([
                "如何在实际工作中应用这些方法？",
                "有哪些常见的执行障碍？",
                "如何衡量改进效果？"
            ])
        else:
            questions.extend([
                "能否提供更多详细信息？",
                "有哪些相关的内容？",
                "如何进一步了解这个话题？"
            ])
        
        return questions[:3]
    
    def _generate_kb_aware_questions(self, context: str, query_engine) -> List[str]:
        """基于知识库内容生成可验证的问题"""
        if not query_engine:
            return []
        
        questions = []
        
        try:
            # 提取关键实体
            entities = self._extract_key_entities(context)
            
            for entity in entities[:2]:  # 只处理前2个实体
                candidate_questions = [
                    f"关于{entity}还有哪些详细信息？",
                    f"{entity}的具体应用场景是什么？",
                    f"文档中提到的{entity}相关案例有哪些？"
                ]
                
                # 验证问题是否能从知识库中找到答案
                for question in candidate_questions:
                    if self._can_answer_from_kb(question, query_engine):
                        questions.append(question)
                        break  # 每个实体只取一个有效问题
        except:
            pass
        
        return questions
    
    def _extract_key_entities(self, text: str) -> List[str]:
        """提取关键实体"""
        # 简单的关键词提取
        entities = []
        
        # 提取中文词汇（2-6个字符）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
        
        # 过滤常见词汇
        stop_words = {'这个', '那个', '可以', '需要', '应该', '因为', '所以', '但是', '然后', '如果', '虽然', '由于'}
        entities = [word for word in chinese_words if word not in stop_words]
        
        # 提取英文术语
        english_terms = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
        entities.extend(english_terms)
        
        # 去重并返回前5个
        return list(dict.fromkeys(entities))[:5]
    
    def _can_answer_from_kb(self, question: str, query_engine) -> bool:
        """检查问题是否能从知识库中找到答案"""
        try:
            result = query_engine.query(question)
            response = result.response if hasattr(result, 'response') else str(result)
            
            # 检查回答质量
            if not response or len(response.strip()) < 20:
                return False
            
            # 检查是否包含"没有相关信息"等否定回答
            negative_indicators = ['没有相关', '无法找到', '不清楚', '没有提到', '无相关信息']
            if any(indicator in response for indicator in negative_indicators):
                return False
            
            return True
        except:
            return False
    
    def _normalize(self, text: str) -> str:
        """归一化文本：去除标点、空白，转小写"""
        if not text: return ""
        text = text.lower().strip()
        # 只保留中英文和数字
        text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
        return text

    def _filter_and_validate(self, suggestions: List[str], query_engine, existing_history: List[str] = None) -> List[str]:
        """过滤和验证问题"""
        # 去重 (保留顺序)
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            norm = self._normalize(s)
            if norm and norm not in seen:
                seen.add(norm)
                unique_suggestions.append(s)
        
        # 准备归一化的历史记录
        normalized_history = set()
        if self.history:
            normalized_history.update(self._normalize(h) for h in self.history[-10:]) # 增加内部历史回溯深度
        
        if existing_history:
            normalized_history.update(self._normalize(h) for h in existing_history)
            
        # 过滤历史问题
        filtered = [q for q in unique_suggestions if self._normalize(q) not in normalized_history]
        
        # 如果没有过滤后的问题，返回原始问题（但排除绝对重复的）
        if not filtered and unique_suggestions:
            if existing_history:
                # 尽量找一个差异最大的
                filtered = unique_suggestions[:3]
            else:
                filtered = unique_suggestions[:3]
        
        # 确保至少有3个问题
        if len(filtered) < 3 and len(unique_suggestions) >= 3:
            for q in unique_suggestions:
                if q not in filtered and self._normalize(q) not in normalized_history:
                     filtered.append(q)
                if len(filtered) >= 3: break
            
            # 如果还是不够，被迫使用一些重复的（但尽量避免）
            if len(filtered) < 3:
                remaining = [q for q in unique_suggestions if q not in filtered]
                filtered.extend(remaining[:3-len(filtered)])
        
        # 如果有查询引擎，验证可答性（但保留至少2个问题）
        if query_engine and filtered:
            validated = []
            for question in filtered:
                # 验证前也检查一下是否完全重复
                if self._can_answer_from_kb(question, query_engine):
                    validated.append(question)
            
            # 如果验证后问题太少，保留前2个原始问题
            if len(validated) < 2 and len(filtered) >= 2:
                validated = filtered[:2]
            elif not validated and filtered:
                validated = [filtered[0]]
            
            return validated
        
        return filtered
    
    def _save_config(self):
        """保存配置"""
        if not self.kb_name:
            return
        
        try:
            config_dir = "suggestion_config"
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, f"{self.kb_name}_config.json")
            
            data = {
                'kb_name': self.kb_name,
                'history': self.history[-50:],  # 只保留最近50条
                'custom': self.custom_suggestions,
                'updated': datetime.now().isoformat()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_custom_suggestion(self, question: str):
        """添加自定义推荐问题"""
        if question and question not in self.custom_suggestions:
            self.custom_suggestions.append(question)
            self._save_config()
    
    def remove_custom_suggestion(self, question: str):
        """删除自定义推荐问题"""
        if question in self.custom_suggestions:
            self.custom_suggestions.remove(question)
            self._save_config()
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_config()

# 全局实例管理
_engines = {}

def get_unified_suggestion_engine(kb_name: Optional[str] = None) -> UnifiedSuggestionEngine:
    """获取统一推荐引擎实例"""
    key = kb_name or 'default'
    if key not in _engines:
        _engines[key] = UnifiedSuggestionEngine(kb_name)
    return _engines[key]
