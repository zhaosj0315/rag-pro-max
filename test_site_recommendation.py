#!/usr/bin/env python3
"""
网站推荐功能测试脚本
用于验证关键词搜索时的智能网站推荐功能
"""

def recommend_sites_for_keyword(keyword: str):
    """根据关键词智能推荐合适的网站"""
    keyword_lower = keyword.lower()
    
    # 技术相关关键词
    tech_keywords = [
        'python', 'java', 'javascript', 'react', 'vue', 'node', 'docker', 'kubernetes',
        'ai', 'ml', 'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'programming', 'coding', 'algorithm', 'data structure', 'database', 'sql',
        '编程', '代码', '算法', '数据结构', '数据库', '人工智能', '机器学习', '深度学习',
        'github', 'git', 'api', 'framework', 'library', '框架', '库', '开发', '软件'
    ]
    
    # 医学相关关键词
    medical_keywords = [
        'cancer', 'disease', 'medicine', 'health', 'treatment', 'diagnosis',
        '癌症', '疾病', '医学', '健康', '治疗', '诊断', '药物', '症状', '病理',
        '卵巢癌', '肺癌', '胃癌', '肝癌', '乳腺癌', '医院', '医生', '手术'
    ]
    
    # 检查是否为技术相关
    is_tech = any(tech_word in keyword_lower for tech_word in tech_keywords)
    is_medical = any(med_word in keyword_lower for med_word in medical_keywords)
    
    if is_tech:
        return ["维基百科", "知乎", "CSDN", "GitHub", "Stack Overflow"]
    elif is_medical:
        return ["维基百科", "百度百科", "知乎"]
    else:
        # 默认推荐百科和问答类
        return ["维基百科", "百度百科", "知乎"]

def test_recommendations():
    """测试各种关键词的推荐结果"""
    test_cases = [
        # 医学相关
        ("卵巢癌", "医学"),
        ("肺癌治疗", "医学"),
        ("糖尿病症状", "医学"),
        ("心脏病诊断", "医学"),
        
        # 技术相关
        ("Python编程", "技术"),
        ("机器学习算法", "技术"),
        ("React框架", "技术"),
        ("Docker容器", "技术"),
        ("数据库设计", "技术"),
        
        # 一般关键词
        ("历史文化", "一般"),
        ("经济学原理", "一般"),
        ("文学作品", "一般"),
        ("地理知识", "一般"),
    ]
    
    print("🧪 网站推荐功能测试")
    print("=" * 50)
    
    for keyword, category in test_cases:
        recommended = recommend_sites_for_keyword(keyword)
        print(f"关键词: {keyword:12} | 类别: {category:4} | 推荐: {', '.join(recommended)}")
    
    print("\n✅ 测试完成！")
    print("\n📋 修复说明:")
    print("1. 医学关键词（如'卵巢癌'）只推荐百科和问答类网站")
    print("2. 技术关键词会推荐技术类网站")
    print("3. 一般关键词默认推荐百科类网站")
    print("4. 避免了医学搜索返回技术内容的问题")

if __name__ == "__main__":
    test_recommendations()
