#!/usr/bin/env python3
"""
优化的联网搜索功能
解决搜索效果差的问题，提升搜索质量和准确性
"""

import re
import time
from typing import List, Dict, Any
from urllib.parse import urlparse

class EnhancedWebSearchEngine:
    """增强的联网搜索引擎"""
    
    def __init__(self):
        self.search_engines = {
            'duckduckgo': self._search_duckduckgo,
            'bing': self._search_bing,
            'google': self._search_google_fallback
        }
        
    def optimize_search_query(self, original_query: str) -> Dict[str, Any]:
        """优化搜索查询"""
        print(f"🔍 原始查询: {original_query}")
        
        # 1. 查询意图分析
        intent = self._analyze_query_intent(original_query)
        
        # 2. 关键词提取和优化
        keywords = self._extract_optimized_keywords(original_query, intent)
        
        # 3. 多语言查询生成
        queries = self._generate_multilingual_queries(keywords, intent)
        
        return {
            'intent': intent,
            'keywords': keywords,
            'queries': queries,
            'original': original_query
        }
    
    def _analyze_query_intent(self, query: str) -> str:
        """分析查询意图"""
        # 意图模式匹配
        intent_patterns = {
            'factual': ['什么是', '谁是', '哪些', '多少', '何时', 'what is', 'who is', 'when', 'how many'],
            'howto': ['如何', '怎么', '怎样', 'how to', 'how do', 'how can'],
            'comparison': ['比较', '对比', '区别', 'vs', 'versus', 'compare', 'difference'],
            'list': ['列出', '名单', '清单', 'list', 'names of', '有哪些'],
            'location': ['在哪', '位置', '地点', 'where', 'location', 'place'],
            'definition': ['定义', '含义', '意思', 'definition', 'meaning', 'means']
        }
        
        query_lower = query.lower()
        for intent_type, patterns in intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent_type
        
        return 'general'
    
    def _extract_optimized_keywords(self, query: str, intent: str) -> List[str]:
        """提取优化的关键词"""
        # 移除停用词
        stop_words = {
            'zh': ['的', '了', '在', '是', '有', '和', '与', '或', '但是', '然而', '因为', '所以'],
            'en': ['the', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'because', 'so', 'that', 'this']
        }
        
        # 提取核心名词和动词
        keywords = []
        
        # 中文关键词提取
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', query)
        for word in chinese_chars:
            if len(word) >= 2 and word not in stop_words['zh']:
                keywords.append(word)
        
        # 英文关键词提取
        english_words = re.findall(r'[a-zA-Z]+', query)
        for word in english_words:
            if len(word) >= 3 and word.lower() not in stop_words['en']:
                keywords.append(word)
        
        # 根据意图调整关键词
        if intent == 'list':
            keywords = [kw for kw in keywords if kw not in ['列出', 'list']]
        elif intent == 'location':
            keywords.extend(['位置', 'location'])
        
        return keywords[:5]  # 限制关键词数量
    
    def _generate_multilingual_queries(self, keywords: List[str], intent: str) -> List[str]:
        """生成多语言查询"""
        queries = []
        
        # 基础关键词组合
        if len(keywords) >= 2:
            queries.append(' '.join(keywords[:3]))
        
        # 根据意图生成特定查询
        if intent == 'factual':
            if any('\u4e00' <= c <= '\u9fff' for c in ' '.join(keywords)):
                queries.append(f"{keywords[0]} 是什么")
                if len(keywords) > 1:
                    queries.append(f"{keywords[0]} {keywords[1]} 介绍")
            queries.append(f"what is {' '.join(keywords)}")
            
        elif intent == 'list':
            if any('\u4e00' <= c <= '\u9fff' for c in ' '.join(keywords)):
                queries.append(f"{keywords[0]} 名单")
                queries.append(f"{keywords[0]} 有哪些")
            queries.append(f"list of {' '.join(keywords)}")
            
        elif intent == 'howto':
            if any('\u4e00' <= c <= '\u9fff' for c in ' '.join(keywords)):
                queries.append(f"如何 {keywords[0]}")
            queries.append(f"how to {' '.join(keywords)}")
            
        elif intent == 'location':
            if any('\u4e00' <= c <= '\u9fff' for c in ' '.join(keywords)):
                queries.append(f"{keywords[0]} 位置")
                queries.append(f"{keywords[0]} 在哪里")
            queries.append(f"{' '.join(keywords)} location")
            
        # 添加英文查询变体
        if keywords:
            queries.append(' '.join(keywords))
            if len(keywords) >= 2:
                queries.append(f'"{keywords[0]}" {keywords[1]}')
        
        # 去重并限制数量
        unique_queries = []
        seen = set()
        for q in queries:
            if q not in seen and len(q.strip()) > 2:
                unique_queries.append(q)
                seen.add(q)
        
        return unique_queries[:4]  # 最多4个查询
    
    def _search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict]:
        """DuckDuckGo搜索"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                # 尝试中文区域
                if any('\u4e00' <= c <= '\u9fff' for c in query):
                    try:
                        cn_results = list(ddgs.text(query, max_results=max_results//2, region='cn-zh'))
                        results.extend(cn_results)
                    except:
                        pass
                
                # 尝试英文区域
                try:
                    en_results = list(ddgs.text(query, max_results=max_results//2, region='us-en'))
                    results.extend(en_results)
                except:
                    pass
                
                # 如果结果不够，尝试全球搜索
                if len(results) < max_results // 2:
                    try:
                        global_results = list(ddgs.text(query, max_results=max_results))
                        results.extend(global_results)
                    except:
                        pass
            
            return results
            
        except Exception as e:
            print(f"❌ DuckDuckGo搜索失败: {e}")
            return []
    
    def _search_bing(self, query: str, max_results: int = 10) -> List[Dict]:
        """Bing搜索 (备用)"""
        # 这里可以实现Bing API搜索
        # 目前返回空列表作为占位符
        return []
    
    def _search_google_fallback(self, query: str, max_results: int = 10) -> List[Dict]:
        """Google搜索备用方案"""
        # 这里可以实现Google Custom Search API
        # 目前返回空列表作为占位符
        return []
    
    def enhanced_search(self, original_query: str, max_results: int = 20) -> Dict[str, Any]:
        """增强搜索主函数"""
        print(f"🚀 启动增强联网搜索...")
        start_time = time.time()
        
        # 1. 查询优化
        optimization = self.optimize_search_query(original_query)
        print(f"🎯 查询意图: {optimization['intent']}")
        print(f"🔑 关键词: {optimization['keywords']}")
        print(f"📝 生成查询: {optimization['queries']}")
        
        # 2. 多引擎搜索
        all_results = []
        
        for query in optimization['queries']:
            print(f"🔍 搜索: {query}")
            
            # 尝试DuckDuckGo
            ddg_results = self._search_duckduckgo(query, max_results//len(optimization['queries']))
            if ddg_results:
                for result in ddg_results:
                    result['search_engine'] = 'duckduckgo'
                    result['search_query'] = query
                all_results.extend(ddg_results)
                print(f"  ✅ DuckDuckGo: {len(ddg_results)} 条结果")
            else:
                print(f"  ❌ DuckDuckGo: 无结果")
        
        # 3. 结果去重和质量过滤
        unique_results = self._deduplicate_results(all_results)
        filtered_results = self._filter_quality_results(unique_results, original_query)
        
        search_time = time.time() - start_time
        
        return {
            'query_optimization': optimization,
            'total_raw_results': len(all_results),
            'unique_results': len(unique_results),
            'final_results': filtered_results,
            'search_time': round(search_time, 2),
            'success': len(filtered_results) > 0
        }
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('href', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _filter_quality_results(self, results: List[Dict], original_query: str) -> List[Dict]:
        """过滤高质量结果"""
        if not results:
            return []
        
        # 质量评分
        scored_results = []
        query_keywords = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', original_query.lower()))
        
        for result in results:
            score = 0
            title = result.get('title', '').lower()
            body = result.get('body', '').lower()
            url = result.get('href', '').lower()
            
            # 标题相关性
            title_matches = sum(1 for kw in query_keywords if kw in title)
            score += title_matches * 3
            
            # 内容相关性
            body_matches = sum(1 for kw in query_keywords if kw in body)
            score += body_matches * 1
            
            # URL质量
            domain = urlparse(url).netloc
            if any(trusted in domain for trusted in ['wikipedia', 'baidu', 'zhihu', 'gov', 'edu']):
                score += 2
            
            # 避免垃圾内容
            if any(spam in title + body for spam in ['广告', '推广', 'ad', 'advertisement']):
                score -= 5
            
            result['quality_score'] = score
            if score > 0:
                scored_results.append(result)
        
        # 按质量排序
        scored_results.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return scored_results[:10]  # 返回前10个高质量结果

def test_enhanced_search():
    """测试增强搜索功能"""
    engine = EnhancedWebSearchEngine()
    
    test_queries = [
        "哪些国家使用该发射场？",
        "如何定位文件位置",
        "Python机器学习库有哪些",
        "什么是人工智能"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"测试查询: {query}")
        print('='*50)
        
        result = engine.enhanced_search(query)
        
        print(f"搜索成功: {result['success']}")
        print(f"搜索时间: {result['search_time']}秒")
        print(f"原始结果: {result['total_raw_results']} 条")
        print(f"去重结果: {result['unique_results']} 条")
        print(f"最终结果: {len(result['final_results'])} 条")
        
        if result['final_results']:
            print("\n前3个结果:")
            for i, res in enumerate(result['final_results'][:3], 1):
                print(f"{i}. {res.get('title', 'No Title')}")
                print(f"   URL: {res.get('href', 'No URL')}")
                print(f"   评分: {res.get('quality_score', 0)}")

if __name__ == "__main__":
    test_enhanced_search()
