#!/usr/bin/env python3
"""
RAG Pro Max v2.4.1 功能可行性测试
测试智能爬取优化功能的完整性和可用性
"""

import sys
import os
import traceback
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crawl_optimizer():
    """测试智能爬取优化器"""
    try:
        from src.processors.crawl_optimizer import CrawlOptimizer
        
        optimizer = CrawlOptimizer()
        
        # 测试网站分析
        test_urls = [
            "https://docs.python.org/",
            "https://36kr.com/", 
            "https://apple.com/",
            "https://stackoverflow.com/"
        ]
        
        for url in test_urls:
            result = optimizer.analyze_website(url)
            
            # 验证返回结果
            required_keys = ['site_type', 'recommended_depth', 'recommended_pages', 
                           'estimated_pages', 'confidence', 'description']
            
            for key in required_keys:
                if key not in result:
                    return False, f"缺少必需字段: {key}"
            
            # 验证数据类型和范围
            if not isinstance(result['recommended_depth'], int) or result['recommended_depth'] < 1:
                return False, f"推荐深度无效: {result['recommended_depth']}"
            
            if not isinstance(result['recommended_pages'], int) or result['recommended_pages'] < 1:
                return False, f"推荐页数无效: {result['recommended_pages']}"
            
            if not isinstance(result['confidence'], (int, float)) or not 0 <= result['confidence'] <= 1:
                return False, f"置信度无效: {result['confidence']}"
        
        return True, "智能爬取优化器测试通过"
        
    except Exception as e:
        return False, f"智能爬取优化器测试失败: {str(e)}"



def test_website_type_recognition():
    """测试网站类型识别"""
    try:
        from src.processors.crawl_optimizer import CrawlOptimizer
        
        optimizer = CrawlOptimizer()
        
        # 测试用例：URL -> 期望类型
        test_cases = [
            ("https://docs.python.org/", "documentation"),
            ("https://36kr.com/", "news"),
            ("https://stackoverflow.com/", "forum"),
            ("https://medium.com/", "blog"),
            ("https://apple.com/", "corporate"),
            ("https://wikipedia.org/", "wiki")
        ]
        
        correct_predictions = 0
        total_tests = len(test_cases)
        
        for url, expected_type in test_cases:
            result = optimizer.analyze_website(url)
            actual_type = result['site_type']
            
            if actual_type == expected_type:
                correct_predictions += 1
            else:
                print(f"  ⚠️ 类型识别偏差: {url} -> 期望:{expected_type}, 实际:{actual_type}")
        
        accuracy = correct_predictions / total_tests
        
        if accuracy >= 0.7:  # 70%准确率阈值
            return True, f"网站类型识别测试通过 (准确率: {accuracy:.1%})"
        else:
            return False, f"网站类型识别准确率过低: {accuracy:.1%}"
        
    except Exception as e:
        return False, f"网站类型识别测试失败: {str(e)}"

def test_realistic_estimation():
    """测试现实预估算法"""
    try:
        from src.processors.crawl_optimizer import CrawlOptimizer
        
        optimizer = CrawlOptimizer()
        
        # 测试预估合理性
        test_cases = [
            ("https://apple.com/", 100),      # 企业官网应该预估较少
            ("https://docs.python.org/", 500), # 文档网站应该预估适中
            ("https://stackoverflow.com/", 1000) # 论坛网站可以预估较多
        ]
        
        for url, max_reasonable in test_cases:
            result = optimizer.analyze_website(url)
            estimated = result['estimated_pages']
            
            if estimated > max_reasonable:
                return False, f"预估过高: {url} -> {estimated}页 (上限:{max_reasonable})"
            
            if estimated < 10:
                return False, f"预估过低: {url} -> {estimated}页 (下限:10)"
        
        return True, "现实预估算法测试通过"
        
    except Exception as e:
        return False, f"现实预估算法测试失败: {str(e)}"

def test_ui_integration():
    """测试UI集成"""
    try:
        # 检查主应用中是否正确集成了新功能
        with open('src/apppro.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键集成点
        integration_checks = [
            "from src.processors.crawl_optimizer import CrawlOptimizer",
            "智能分析",
            "crawl_optimizer",
            "crawl_analysis"
        ]
        
        for check in integration_checks:
            if check not in content:
                return False, f"UI集成缺少: {check}"
        
        return True, "UI集成测试通过"
        
    except Exception as e:
        return False, f"UI集成测试失败: {str(e)}"

def run_all_tests():
    """运行所有v2.4.1可行性测试"""
    
    print("=" * 60)
    print("  RAG Pro Max v2.4.1 功能可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("智能爬取优化器", test_crawl_optimizer),

        ("网站类型识别", test_website_type_recognition),
        ("现实预估算法", test_realistic_estimation),
        ("UI集成", test_ui_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"🧪 测试: {test_name}")
            success, message = test_func()
            
            if success:
                print(f"✅ {message}")
                passed += 1
            else:
                print(f"❌ {message}")
                failed += 1
                
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {str(e)}")
            print(f"   {traceback.format_exc()}")
            failed += 1
        
        print()
    
    # 测试总结
    print("=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{passed + failed}")
    print(f"❌ 失败: {failed}/{passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有v2.4.1功能测试通过！智能爬取系统可以发布。")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，需要修复后再发布。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
