#!/usr/bin/env python3
"""
测试可配置行业网站系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_configurable_system():
    """测试可配置系统"""
    print("🧪 测试可配置行业网站系统")
    print("=" * 50)
    
    try:
        # 测试服务导入
        from src.services.configurable_industry_service import get_configurable_industry_service
        service = get_configurable_industry_service()
        print("✅ 配置服务导入成功")
        
        # 测试获取行业列表
        industries = service.get_all_industries()
        print(f"✅ 获取行业列表: {len(industries)} 个行业")
        for industry in industries:
            print(f"   • {industry}")
        
        # 测试关键词推荐
        test_keywords = ["python编程", "卵巢癌治疗", "股票投资"]
        for keyword in test_keywords:
            recommended = service.recommend_sites_for_keyword(keyword)
            print(f"✅ 关键词 '{keyword}' 推荐: {recommended}")
        
        # 测试获取网站列表
        if industries:
            first_industry = industries[0]
            sites = service.get_industry_sites(first_industry)
            print(f"✅ {first_industry} 包含 {len(sites)} 个网站")
            for site in sites[:3]:  # 只显示前3个
                print(f"   • {site['name']}: {site['url']}")
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_configurable_system()
