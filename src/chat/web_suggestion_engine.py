"""
基于网页抓取内容的智能推荐问题生成器
"""

import re
import os
from typing import List, Dict
from urllib.parse import urlparse

class WebSuggestionEngine:
    """网页内容推荐问题生成器"""
    
    def __init__(self):
        self.domain_templates = {
            'python.org': [
                "Python有哪些主要特性？",
                "如何开始学习Python？", 
                "Python的最新版本有什么新功能？",
                "Python适合哪些应用场景？"
            ],
            'docs.python.org': [
                "这个功能如何使用？",
                "有哪些相关的API方法？",
                "能否提供一个使用示例？",
                "这个模块的主要用途是什么？"
            ],
            'github.com': [
                "这个项目的主要功能是什么？",
                "如何安装和使用这个项目？",
                "项目有哪些依赖要求？",
                "如何贡献代码到这个项目？"
            ],
            'stackoverflow.com': [
                "这个问题的解决方案是什么？",
                "有其他类似的解决方法吗？",
                "为什么会出现这个问题？",
                "如何避免这类问题？"
            ]
        }
        
        self.content_keywords = {
            'tutorial': [
                "这个教程涵盖了哪些内容？",
                "学习这个需要什么基础？",
                "有实践练习吗？",
                "下一步应该学什么？"
            ],
            'api': [
                "这个API如何调用？",
                "有哪些参数选项？",
                "返回值是什么格式？",
                "有使用限制吗？"
            ],
            'install': [
                "安装过程中可能遇到什么问题？",
                "有其他安装方式吗？",
                "系统要求是什么？",
                "如何验证安装成功？"
            ],
            'config': [
                "如何修改这些配置？",
                "配置文件在哪里？",
                "有哪些重要的配置项？",
                "配置错误如何排查？"
            ]
        }

    def generate_suggestions_from_crawl(self, crawl_url: str, saved_files: List[str]) -> List[str]:
        """
        基于抓取的网页内容生成推荐问题
        
        Args:
            crawl_url: 抓取的起始URL
            saved_files: 抓取保存的文件列表
            
        Returns:
            推荐问题列表
        """
        suggestions = []
        
        # 1. 基于域名生成通用问题
        domain_suggestions = self._get_domain_suggestions(crawl_url)
        suggestions.extend(domain_suggestions)
        
        # 2. 基于文件内容生成具体问题
        content_suggestions = self._analyze_content_suggestions(saved_files)
        suggestions.extend(content_suggestions)
        
        # 3. 基于文件标题生成问题
        title_suggestions = self._generate_title_based_suggestions(saved_files)
        suggestions.extend(title_suggestions)
        
        # 去重并限制数量
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:6]  # 返回最多6个问题

    def _get_domain_suggestions(self, url: str) -> List[str]:
        """基于域名获取推荐问题"""
        domain = urlparse(url).netloc.lower()
        
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # 查找匹配的域名模板
        for template_domain, questions in self.domain_templates.items():
            if template_domain in domain:
                return questions[:2]  # 返回前2个
        
        # 默认通用问题
        return [
            "这个网站的主要内容是什么？",
            "有哪些重要信息？"
        ]

    def _analyze_content_suggestions(self, saved_files: List[str]) -> List[str]:
        """分析文件内容生成推荐问题"""
        suggestions = []
        
        # 分析前3个文件的内容
        for file_path in saved_files[:3]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # 检查内容关键词
                for keyword, questions in self.content_keywords.items():
                    if keyword in content:
                        suggestions.extend(questions[:1])  # 每个关键词取1个问题
                        
            except Exception:
                continue
        
        return suggestions

    def _generate_title_based_suggestions(self, saved_files: List[str]) -> List[str]:
        """基于文件标题生成问题"""
        suggestions = []
        
        for file_path in saved_files[:3]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 提取标题（第二行通常是Title）
                if len(lines) >= 2:
                    title_line = lines[1].strip()
                    if title_line.startswith('Title:'):
                        title = title_line[6:].strip()
                        
                        # 基于标题生成问题
                        if title and title != "No Title":
                            # 清理标题
                            clean_title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title)
                            if len(clean_title) > 5:
                                suggestions.append(f"关于「{clean_title[:30]}」的详细信息？")
                                
            except Exception:
                continue
        
        return suggestions

    def generate_contextual_suggestions(self, kb_name: str, recent_query: str = None) -> List[str]:
        """
        生成上下文相关的推荐问题
        
        Args:
            kb_name: 知识库名称
            recent_query: 最近的查询（可选）
            
        Returns:
            上下文相关的推荐问题
        """
        suggestions = []
        
        # 基于知识库名称推断内容类型
        kb_lower = kb_name.lower()
        
        if 'web_' in kb_lower:
            # 网页抓取的知识库
            if 'python' in kb_lower:
                suggestions = [
                    "Python的核心特性有哪些？",
                    "如何快速上手Python开发？",
                    "Python在哪些领域应用最广？",
                    "Python的性能如何优化？"
                ]
            elif 'doc' in kb_lower:
                suggestions = [
                    "这份文档的主要内容是什么？",
                    "如何按照文档进行操作？",
                    "文档中提到的最佳实践是什么？",
                    "有哪些常见问题和解决方案？"
                ]
            elif 'github' in kb_lower:
                suggestions = [
                    "这个项目解决了什么问题？",
                    "如何快速开始使用？",
                    "项目的技术架构是怎样的？",
                    "如何参与项目贡献？"
                ]
            else:
                suggestions = [
                    "网站的主要功能是什么？",
                    "有哪些重要的使用指南？",
                    "如何获取更多相关信息？",
                    "内容的核心要点是什么？"
                ]
        
        # 基于最近查询调整问题
        if recent_query:
            suggestions = self._adjust_by_recent_query(suggestions, recent_query)
        
        return suggestions[:4]  # 返回4个问题

    def _adjust_by_recent_query(self, suggestions: List[str], recent_query: str) -> List[str]:
        """基于最近查询调整推荐问题"""
        query_lower = recent_query.lower()
        
        # 如果查询包含特定关键词，调整推荐
        if any(word in query_lower for word in ['如何', 'how', '怎么']):
            # 添加更多操作性问题
            suggestions.insert(0, "具体的操作步骤是什么？")
        
        if any(word in query_lower for word in ['为什么', 'why', '原因']):
            # 添加更多解释性问题
            suggestions.insert(0, "背后的原理是什么？")
        
        if any(word in query_lower for word in ['比较', 'vs', '区别']):
            # 添加更多对比性问题
            suggestions.insert(0, "还有哪些类似的选择？")
        
        return suggestions
