#!/usr/bin/env python3
"""
文档质量评估器
自动评估上传文档的质量并提供改进建议
"""

import streamlit as st
from pathlib import Path
import re
from typing import Dict, List, Tuple

class DocumentQualityAssessor:
    """文档质量评估器"""
    
    def __init__(self):
        self.quality_metrics = {
            'readability': 0,
            'structure': 0, 
            'content_density': 0,
            'language_quality': 0,
            'overall': 0
        }
    
    def assess_document(self, content: str, filename: str = "") -> Dict:
        """评估文档质量"""
        
        # 基础检查
        if not content or len(content.strip()) < 50:
            return self._create_low_quality_result("文档内容过短")
        
        # 计算各项指标
        readability = self._assess_readability(content)
        structure = self._assess_structure(content)
        content_density = self._assess_content_density(content)
        language_quality = self._assess_language_quality(content)
        
        # 计算总分
        overall = (readability + structure + content_density + language_quality) / 4
        
        return {
            'scores': {
                'readability': readability,
                'structure': structure,
                'content_density': content_density,
                'language_quality': language_quality,
                'overall': overall
            },
            'grade': self._get_quality_grade(overall),
            'suggestions': self._generate_suggestions(readability, structure, content_density, language_quality),
            'filename': filename,
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    
    def _assess_readability(self, content: str) -> float:
        """评估可读性"""
        sentences = re.split(r'[.!?。！？]', content)
        words = content.split()
        
        if not sentences or not words:
            return 0.0
        
        # 平均句长
        avg_sentence_length = len(words) / len([s for s in sentences if s.strip()])
        
        # 理想句长15-25词
        if 15 <= avg_sentence_length <= 25:
            sentence_score = 100
        elif avg_sentence_length < 15:
            sentence_score = max(60, 100 - (15 - avg_sentence_length) * 3)
        else:
            sentence_score = max(40, 100 - (avg_sentence_length - 25) * 2)
        
        # 段落结构
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            paragraph_score = min(100, len(paragraphs) * 10)
        else:
            paragraph_score = 50
        
        return (sentence_score + paragraph_score) / 2
    
    def _assess_structure(self, content: str) -> float:
        """评估文档结构"""
        score = 0
        
        # 检查标题
        if re.search(r'^#+ ', content, re.MULTILINE):
            score += 30
        elif re.search(r'^\d+\.|\*|-', content, re.MULTILINE):
            score += 20
        
        # 检查列表
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            score += 20
        
        # 检查编号列表
        if re.search(r'^\s*\d+\.\s+', content, re.MULTILINE):
            score += 20
        
        # 检查段落分隔
        if '\n\n' in content:
            score += 20
        
        # 检查代码块
        if '```' in content or '    ' in content:
            score += 10
        
        return min(100, score)
    
    def _assess_content_density(self, content: str) -> float:
        """评估内容密度"""
        words = content.split()
        
        # 词汇多样性
        unique_words = set(word.lower() for word in words if len(word) > 3)
        diversity = len(unique_words) / len(words) if words else 0
        
        # 信息密度
        info_words = [w for w in words if len(w) > 4]
        info_density = len(info_words) / len(words) if words else 0
        
        # 重复度检查
        word_freq = {}
        for word in words:
            word_freq[word.lower()] = word_freq.get(word.lower(), 0) + 1
        
        max_freq = max(word_freq.values()) if word_freq else 1
        repetition_penalty = min(20, max_freq - 1) * 2
        
        density_score = (diversity * 50 + info_density * 50) - repetition_penalty
        return max(0, min(100, density_score))
    
    def _assess_language_quality(self, content: str) -> float:
        """评估语言质量"""
        score = 80  # 基础分
        
        # 检查常见问题
        issues = 0
        
        # 过多感叹号
        if content.count('!') > len(content) / 100:
            issues += 1
        
        # 过多问号
        if content.count('?') > len(content) / 50:
            issues += 1
        
        # 重复标点
        if re.search(r'[.!?]{3,}', content):
            issues += 1
        
        # 全大写词汇过多
        caps_words = re.findall(r'\b[A-Z]{3,}\b', content)
        if len(caps_words) > len(content.split()) / 20:
            issues += 1
        
        return max(40, score - issues * 10)
    
    def _get_quality_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "及格"
        else:
            return "需改进"
    
    def _generate_suggestions(self, readability: float, structure: float, 
                            content_density: float, language_quality: float) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if readability < 70:
            suggestions.append("📝 建议优化句子长度，控制在15-25词之间")
            suggestions.append("📝 增加段落分隔，提高可读性")
        
        if structure < 70:
            suggestions.append("🏗️ 建议添加标题和子标题来组织内容")
            suggestions.append("🏗️ 使用列表和编号来突出重点")
        
        if content_density < 70:
            suggestions.append("💡 建议增加内容的信息密度")
            suggestions.append("💡 减少重复词汇，提高词汇多样性")
        
        if language_quality < 70:
            suggestions.append("✏️ 建议检查标点符号使用")
            suggestions.append("✏️ 避免过度使用大写字母")
        
        if not suggestions:
            suggestions.append("🎉 文档质量很好，继续保持！")
        
        return suggestions
    
    def _create_low_quality_result(self, reason: str) -> Dict:
        """创建低质量结果"""
        return {
            'scores': {
                'readability': 0,
                'structure': 0,
                'content_density': 0,
                'language_quality': 0,
                'overall': 0
            },
            'grade': "需改进",
            'suggestions': [f"❌ {reason}", "📝 请提供更多有意义的内容"],
            'filename': "",
            'word_count': 0,
            'char_count': 0
        }

def show_quality_assessment(content: str, filename: str = "") -> None:
    """显示文档质量评估结果"""
    assessor = DocumentQualityAssessor()
    result = assessor.assess_document(content, filename)
    
    # 显示总体评分
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = result['scores']['overall']
        if score >= 80:
            st.success(f"📊 总体评分: {score:.1f}")
        elif score >= 60:
            st.warning(f"📊 总体评分: {score:.1f}")
        else:
            st.error(f"📊 总体评分: {score:.1f}")
    
    with col2:
        st.info(f"🏆 质量等级: {result['grade']}")
    
    with col3:
        st.info(f"📄 字数: {result['word_count']}")
    
    # 详细评分
    st.markdown("### 📋 详细评分")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📖 可读性", f"{result['scores']['readability']:.1f}")
        st.metric("💡 内容密度", f"{result['scores']['content_density']:.1f}")
    
    with col2:
        st.metric("🏗️ 结构性", f"{result['scores']['structure']:.1f}")
        st.metric("✏️ 语言质量", f"{result['scores']['language_quality']:.1f}")
    
    # 改进建议
    if result['suggestions']:
        st.markdown("### 💡 改进建议")
        for suggestion in result['suggestions']:
            st.write(f"• {suggestion}")

# 全局评估器实例
quality_assessor = DocumentQualityAssessor()
