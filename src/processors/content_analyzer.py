"""
内容质量分析器
实现内容去重、质量评估和相关性评分
"""

import re
import hashlib
from typing import List, Dict, Set, Tuple
from collections import Counter
import jieba
from difflib import SequenceMatcher

class ContentQualityAnalyzer:
    """内容质量分析器"""
    
    def __init__(self):
        self.content_hashes = set()  # 用于去重
        self.stop_words = self._load_stop_words()
        
    def _load_stop_words(self) -> Set[str]:
        """加载停用词"""
        # 基础中文停用词
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '它', '他', '她', '们', '这个', '那个', '什么', '怎么',
            '为什么', '哪里', '哪个', '如何', '或者', '但是', '然后', '因为', '所以'
        }
        return stop_words
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值用于去重"""
        # 清理内容
        cleaned = re.sub(r'\s+', ' ', content.strip())
        # 计算MD5哈希
        return hashlib.md5(cleaned.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _extract_keywords(self, content: str, top_k: int = 20) -> List[str]:
        """提取关键词"""
        # 使用jieba分词
        words = jieba.lcut(content)
        
        # 过滤停用词和短词
        filtered_words = [
            word.strip() for word in words 
            if len(word.strip()) > 1 and word.strip() not in self.stop_words
        ]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 返回top_k个关键词
        return [word for word, freq in word_freq.most_common(top_k)]
    
    def calculate_quality_score(self, content: str, title: str = "") -> Dict:
        """计算内容质量评分"""
        if not content:
            return {
                'total_score': 0,
                'length_score': 0,
                'structure_score': 0,
                'readability_score': 0,
                'information_density': 0,
                'details': {}
            }
        
        scores = {}
        
        # 1. 长度评分 (0-25分)
        content_length = len(content)
        if content_length < 100:
            length_score = content_length / 100 * 10  # 太短扣分
        elif content_length < 500:
            length_score = 15
        elif content_length < 2000:
            length_score = 25  # 理想长度
        elif content_length < 5000:
            length_score = 20
        else:
            length_score = 15  # 太长可能有噪音
        
        scores['length_score'] = length_score
        scores['content_length'] = content_length
        
        # 2. 结构化评分 (0-25分)
        structure_indicators = {
            '段落': len(content.split('\n\n')),
            '句子': len(re.findall(r'[。！？]', content)),
            '数字': len(re.findall(r'\d+', content)),
            '列表': len(re.findall(r'[•·\-\*]\s', content)),
            '标点': len(re.findall(r'[，。！？；：]', content))
        }
        
        structure_score = 0
        if structure_indicators['段落'] > 1:
            structure_score += 5
        if structure_indicators['句子'] > 3:
            structure_score += 5
        if structure_indicators['数字'] > 0:
            structure_score += 5
        if structure_indicators['列表'] > 0:
            structure_score += 5
        if structure_indicators['标点'] > 10:
            structure_score += 5
            
        scores['structure_score'] = structure_score
        scores['structure_indicators'] = structure_indicators
        
        # 3. 可读性评分 (0-25分)
        # 计算平均句子长度
        sentences = re.split(r'[。！？]', content)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if valid_sentences:
            avg_sentence_length = sum(len(s) for s in valid_sentences) / len(valid_sentences)
            # 理想句子长度15-30字符
            if 15 <= avg_sentence_length <= 30:
                readability_score = 25
            elif 10 <= avg_sentence_length <= 40:
                readability_score = 20
            else:
                readability_score = 15
        else:
            readability_score = 5
        
        scores['readability_score'] = readability_score
        scores['avg_sentence_length'] = avg_sentence_length if valid_sentences else 0
        scores['sentence_count'] = len(valid_sentences)
        
        # 4. 信息密度评分 (0-25分)
        keywords = self._extract_keywords(content)
        unique_words = set(jieba.lcut(content))
        
        # 关键词密度
        keyword_density = len(keywords) / max(len(content.split()), 1)
        # 词汇丰富度
        vocabulary_richness = len(unique_words) / max(len(content.split()), 1)
        
        info_density = (keyword_density * 50 + vocabulary_richness * 50) / 2
        information_density = min(info_density * 25, 25)
        
        scores['information_density'] = information_density
        scores['keyword_count'] = len(keywords)
        scores['vocabulary_richness'] = vocabulary_richness
        scores['top_keywords'] = keywords[:10]
        
        # 计算总分
        total_score = (
            scores['length_score'] + 
            scores['structure_score'] + 
            scores['readability_score'] + 
            scores['information_density']
        )
        
        return {
            'total_score': total_score,
            'length_score': scores['length_score'],
            'structure_score': scores['structure_score'],
            'readability_score': scores['readability_score'],
            'information_density': scores['information_density'],
            'details': {
                'content_length': scores['content_length'],
                'structure_indicators': scores['structure_indicators'],
                'avg_sentence_length': scores['avg_sentence_length'],
                'sentence_count': scores['sentence_count'],
                'keyword_count': scores['keyword_count'],
                'vocabulary_richness': scores['vocabulary_richness'],
                'top_keywords': scores['top_keywords']
            }
        }
    
    def calculate_relevance_score(self, content: str, keywords: List[str]) -> float:
        """计算内容与关键词的相关性评分"""
        if not content or not keywords:
            return 0.0
        
        content_lower = content.lower()
        content_words = set(jieba.lcut(content_lower))
        
        # 计算关键词匹配度
        matches = 0
        total_weight = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            weight = len(keyword)  # 长关键词权重更高
            total_weight += weight
            
            # 直接匹配
            if keyword_lower in content_lower:
                matches += weight
            # 分词匹配
            elif keyword_lower in content_words:
                matches += weight * 0.8
            # 部分匹配
            elif any(keyword_lower in word for word in content_words):
                matches += weight * 0.5
        
        if total_weight == 0:
            return 0.0
        
        relevance_score = matches / total_weight
        return min(relevance_score, 1.0)
    
    def deduplicate_content(self, contents: List[Dict], similarity_threshold: float = 0.8) -> List[Dict]:
        """内容去重"""
        if not contents:
            return []
        
        unique_contents = []
        seen_hashes = set()
        
        for content_item in contents:
            content = content_item.get('content', '')
            if not content:
                continue
            
            # 计算哈希值
            content_hash = self._calculate_content_hash(content)
            
            # 检查是否已存在相同内容
            if content_hash in seen_hashes:
                continue
            
            # 检查与已有内容的相似度
            is_duplicate = False
            for existing_item in unique_contents:
                existing_content = existing_item.get('content', '')
                similarity = self._calculate_similarity(content, existing_content)
                
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    # 保留质量更高的内容
                    existing_score = existing_item.get('quality_score', {}).get('total_score', 0)
                    current_score = content_item.get('quality_score', {}).get('total_score', 0)
                    
                    if current_score > existing_score:
                        # 替换为质量更高的内容
                        unique_contents.remove(existing_item)
                        unique_contents.append(content_item)
                        seen_hashes.add(content_hash)
                    break
            
            if not is_duplicate:
                unique_contents.append(content_item)
                seen_hashes.add(content_hash)
        
        return unique_contents
    
    def analyze_and_filter_contents(self, contents: List[Dict], 
                                  search_keywords: List[str] = None,
                                  min_quality_score: float = 40.0,
                                  max_results: int = 50) -> List[Dict]:
        """分析并过滤内容"""
        if not contents:
            return []
        
        analyzed_contents = []
        
        # 1. 质量评估
        for content_item in contents:
            content = content_item.get('content', '')
            title = content_item.get('title', '')
            
            if not content:
                continue
            
            # 计算质量评分
            quality_score = self.calculate_quality_score(content, title)
            content_item['quality_score'] = quality_score
            
            # 计算相关性评分
            if search_keywords:
                relevance_score = self.calculate_relevance_score(content, search_keywords)
                content_item['relevance_score'] = relevance_score
            else:
                content_item['relevance_score'] = 1.0
            
            # 计算综合评分
            total_quality = quality_score['total_score']
            relevance = content_item['relevance_score'] * 100
            content_item['final_score'] = (total_quality * 0.7 + relevance * 0.3)
            
            analyzed_contents.append(content_item)
        
        # 2. 过滤低质量内容
        filtered_contents = [
            item for item in analyzed_contents 
            if item['quality_score']['total_score'] >= min_quality_score
        ]
        
        # 3. 去重
        unique_contents = self.deduplicate_content(filtered_contents)
        
        # 4. 按综合评分排序
        sorted_contents = sorted(
            unique_contents, 
            key=lambda x: x['final_score'], 
            reverse=True
        )
        
        # 5. 限制结果数量
        return sorted_contents[:max_results]

# 使用示例
if __name__ == "__main__":
    analyzer = ContentQualityAnalyzer()
    
    # 测试内容
    test_contents = [
        {
            'title': 'Python教程',
            'content': 'Python是一种高级编程语言。它具有简洁的语法和强大的功能。Python广泛应用于Web开发、数据分析、人工智能等领域。学习Python可以帮助你快速入门编程。',
            'url': 'https://example.com/python'
        },
        {
            'title': 'Python基础',
            'content': 'Python编程语言简单易学。语法清晰，功能强大。',
            'url': 'https://example.com/python-basic'
        }
    ]
    
    # 分析和过滤
    search_keywords = ['Python', '编程', '教程']
    results = analyzer.analyze_and_filter_contents(
        test_contents, 
        search_keywords=search_keywords,
        min_quality_score=30.0
    )
    
    print(f"分析结果: {len(results)} 个内容")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   质量评分: {result['quality_score']['total_score']:.1f}")
        print(f"   相关性: {result['relevance_score']:.2f}")
        print(f"   综合评分: {result['final_score']:.1f}")
        print(f"   关键词: {result['quality_score']['details']['top_keywords'][:5]}")
