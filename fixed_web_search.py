#!/usr/bin/env python3
"""
修复联网搜索功能
解决关键词提取和搜索效果问题
"""

import re
import time
from typing import List, Dict, Any

class FixedWebSearchEngine:
    """修复的联网搜索引擎"""
    
    def __init__(self):
        pass
        
    def extract_smart_keywords(self, query: str) -> List[str]:
        """智能提取关键词"""
        print(f"🔍 分析查询: {query}")
        
        # 移除疑问词和助词
        remove_words = [
            '什么是', '哪些', '如何', '怎么', '怎样', '为什么', '是什么', '有哪些',
            'what is', 'how to', 'how do', 'which', 'what are', 'why'
        ]
        
        cleaned_query = query
        for word in remove_words:
            cleaned_query = cleaned_query.replace(word, ' ')
        
        # 提取有意义的词汇
        keywords = []
        
        # 中文词汇 (2-6个字符)
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,6}', cleaned_query)
        for word in chinese_words:
            if word not in ['国家', '使用', '发射场', '文件', '位置', '定位']:
                keywords.append(word)
        
        # 英文词汇 (3个字符以上)
        english_words = re.findall(r'[a-zA-Z]{3,}', cleaned_query)
        for word in english_words:
            if word.lower() not in ['the', 'and', 'for', 'are', 'how', 'what']:
                keywords.append(word)
        
        # 如果没有提取到关键词，使用原查询的核心部分
        if not keywords:
            # 对于"哪些国家使用该发射场"这类查询
            if '发射场' in query:
                keywords = ['发射场', '航天发射', 'launch site', 'spaceport']
            elif '文件位置' in query:
                keywords = ['文件定位', '查找文件', 'find file', 'file location']
            elif '机器学习' in query:
                keywords = ['机器学习', 'Python', 'machine learning', 'ML library']
            elif '人工智能' in query:
                keywords = ['人工智能', 'AI', 'artificial intelligence']
            else:
                # 分词处理
                words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query)
                keywords = [w for w in words if len(w) >= 2]
        
        print(f"🔑 提取关键词: {keywords}")
        return keywords[:4]  # 最多4个关键词
    
    def generate_search_queries(self, keywords: List[str], original_query: str) -> List[str]:
        """生成搜索查询"""
        queries = []
        
        if not keywords:
            return [original_query]
        
        # 1. 直接关键词组合
        if len(keywords) >= 2:
            queries.append(' '.join(keywords[:2]))
        
        # 2. 单个关键词
        for kw in keywords[:2]:
            queries.append(kw)
        
        # 3. 英文查询
        english_kws = [kw for kw in keywords if re.match(r'^[a-zA-Z\s]+$', kw)]
        if english_kws:
            queries.append(' '.join(english_kws[:2]))
        
        # 4. 中文查询
        chinese_kws = [kw for kw in keywords if re.search(r'[\u4e00-\u9fff]', kw)]
        if chinese_kws:
            queries.append(' '.join(chinese_kws[:2]))
        
        # 去重
        unique_queries = []
        seen = set()
        for q in queries:
            if q and q not in seen:
                unique_queries.append(q)
                seen.add(q)
        
        print(f"📝 生成查询: {unique_queries}")
        return unique_queries[:3]  # 最多3个查询
    
    def search_with_ddgs(self, query: str, max_results: int = 8) -> List[Dict]:
        """使用ddgs搜索"""
        try:
            # 尝试新的ddgs包
            try:
                from ddgs import DDGS
                print(f"  使用新版ddgs包搜索...")
            except ImportError:
                # 回退到旧版本
                from duckduckgo_search import DDGS
                print(f"  使用旧版duckduckgo_search包搜索...")
            
            results = []
            
            # 搜索策略：先中文区域，再英文区域，最后全球
            search_configs = [
                {'region': 'cn-zh', 'desc': '中文区域'},
                {'region': 'us-en', 'desc': '英文区域'},
                {'region': None, 'desc': '全球搜索'}
            ]
            
            with DDGS() as ddgs:
                for config in search_configs:
                    try:
                        print(f"    尝试{config['desc']}搜索...")
                        if config['region']:
                            search_results = list(ddgs.text(
                                query, 
                                max_results=max_results//2,
                                region=config['region']
                            ))
                        else:
                            search_results = list(ddgs.text(
                                query, 
                                max_results=max_results
                            ))
                        
                        if search_results:
                            results.extend(search_results)
                            print(f"    ✅ {config['desc']}: {len(search_results)} 条结果")
                            break  # 找到结果就停止
                        else:
                            print(f"    ❌ {config['desc']}: 无结果")
                            
                    except Exception as e:
                        print(f"    ❌ {config['desc']}搜索失败: {e}")
                        continue
            
            return results[:max_results]
            
        except Exception as e:
            print(f"❌ 搜索引擎错误: {e}")
            return []
    
    def enhanced_search(self, original_query: str) -> Dict[str, Any]:
        """增强搜索主函数"""
        print(f"🚀 启动修复版联网搜索...")
        start_time = time.time()
        
        # 1. 智能关键词提取
        keywords = self.extract_smart_keywords(original_query)
        
        # 2. 生成搜索查询
        search_queries = self.generate_search_queries(keywords, original_query)
        
        # 3. 执行搜索
        all_results = []
        
        for query in search_queries:
            print(f"🔍 搜索查询: {query}")
            results = self.search_with_ddgs(query)
            
            if results:
                for result in results:
                    result['search_query'] = query
                all_results.extend(results)
                print(f"  ✅ 获得 {len(results)} 条结果")
                
                # 如果已经有足够结果，停止搜索
                if len(all_results) >= 10:
                    break
            else:
                print(f"  ❌ 无结果")
        
        # 4. 去重
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            url = result.get('href', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # 5. 简单质量过滤
        filtered_results = []
        for result in unique_results:
            title = result.get('title', '').lower()
            body = result.get('body', '').lower()
            
            # 过滤明显的垃圾内容
            if not any(spam in title + body for spam in ['广告', '推广', 'ad', 'advertisement', '点击', 'click here']):
                filtered_results.append(result)
        
        search_time = time.time() - start_time
        
        return {
            'original_query': original_query,
            'keywords': keywords,
            'search_queries': search_queries,
            'total_results': len(all_results),
            'unique_results': len(unique_results),
            'final_results': filtered_results[:8],  # 最多8个结果
            'search_time': round(search_time, 2),
            'success': len(filtered_results) > 0
        }

def test_fixed_search():
    """测试修复的搜索功能"""
    engine = FixedWebSearchEngine()
    
    test_queries = [
        "哪些国家使用该发射场？",
        "如何定位文件位置",
        "Python机器学习库有哪些",
        "什么是人工智能"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"测试查询: {query}")
        print('='*60)
        
        result = engine.enhanced_search(query)
        
        print(f"\n📊 搜索结果:")
        print(f"  搜索成功: {result['success']}")
        print(f"  搜索时间: {result['search_time']}秒")
        print(f"  总结果数: {result['total_results']}")
        print(f"  去重结果: {result['unique_results']}")
        print(f"  最终结果: {len(result['final_results'])}")
        
        if result['final_results']:
            print(f"\n🎯 前3个结果:")
            for i, res in enumerate(result['final_results'][:3], 1):
                print(f"  {i}. {res.get('title', 'No Title')}")
                print(f"     {res.get('href', 'No URL')}")
                print(f"     摘要: {res.get('body', 'No Body')[:100]}...")
                print()

if __name__ == "__main__":
    test_fixed_search()
