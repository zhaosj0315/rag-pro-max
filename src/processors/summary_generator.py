"""
摘要生成器
提取自 apppro.py 的 generate_doc_summary 函数
"""

import re
from llama_index.core import Settings
from src.logging import LogManager


class SummaryGenerator:
    """摘要生成器"""
    
    def __init__(self):
        self.logger = LogManager()
    
    def generate_doc_summary(self, doc_text: str, filename: str) -> str:
        """
        生成文档摘要
        
        Args:
            doc_text: 文档文本
            filename: 文件名
            
        Returns:
            str: 生成的摘要
        """
        try:
            if not Settings.llm:
                return f"📄 已加载文档: {filename}"
            
            # 限制文本长度，避免超出模型限制
            max_chars = 8000
            if len(doc_text) > max_chars:
                doc_text = doc_text[:max_chars] + "..."
            
            # 构建摘要提示
            prompt = self._build_summary_prompt(doc_text, filename)
            
            # 生成摘要
            response = Settings.llm.complete(prompt)
            summary_text = response.text.strip()
            
            # 清理和格式化摘要
            summary = self._clean_summary(summary_text)
            
            self.logger.info(f"✅ 摘要生成完成: {filename}")
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ 摘要生成失败: {filename} - {str(e)}")
            return f"📄 已加载文档: {filename}（摘要生成失败）"
    
    def _build_summary_prompt(self, doc_text: str, filename: str) -> str:
        """构建摘要提示词"""
        return f"""请为以下文档生成一个简洁的摘要，然后提出3个相关问题。

文档名称：{filename}
文档内容：
{doc_text}

要求：
1. 摘要控制在100字以内，突出核心内容
2. 提出3个具体、有价值的问题
3. 格式：先写摘要，然后每行一个问题（不要编号）

请开始："""
    
    def _clean_summary(self, summary_text: str) -> str:
        """清理和格式化摘要"""
        # 移除多余的空行
        lines = [line.strip() for line in summary_text.split('\n') if line.strip()]
        
        # 确保格式正确
        if lines:
            # 第一行作为摘要
            summary = lines[0]
            
            # 其余行作为问题
            questions = []
            for line in lines[1:]:
                # 清理问题格式
                question = re.sub(r'^[\d\.\-\s\*\•]+', '', line).strip()
                if question and len(question) > 5:
                    questions.append(question)
            
            # 组合结果
            if questions:
                return summary + "\n\n" + "\n".join(questions[:3])
            else:
                return summary
        
        return summary_text


# 全局实例
_generator = None

def get_summary_generator() -> SummaryGenerator:
    """获取摘要生成器实例"""
    global _generator
    if _generator is None:
        _generator = SummaryGenerator()
    return _generator

# 兼容性函数
def generate_doc_summary(doc_text: str, filename: str) -> str:
    """兼容性函数"""
    generator = get_summary_generator()
    return generator.generate_doc_summary(doc_text, filename)
