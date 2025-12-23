#!/usr/bin/env python3
"""
医疗搜索修复验证脚本
验证医疗健康搜索是否正确配置
"""

def test_medical_search_config():
    """测试医疗搜索配置"""
    print("🏥 医疗搜索配置验证")
    print("=" * 50)
    
    try:
        # 测试统一网站配置
        from src.config.unified_sites import get_industry_sites, get_industry_list
        
        # 1. 检查行业列表
        industries = get_industry_list()
        medical_found = any("医疗健康" in industry for industry in industries)
        print(f"1. 医疗健康行业存在: {'✅' if medical_found else '❌'}")
        
        # 2. 检查医疗网站配置
        medical_industry = "🏥 医疗健康 - 医疗资讯、健康科普、医学知识"
        urls, names = get_industry_sites(medical_industry)
        print(f"2. 医疗网站数量: {len(names)} 个")
        
        # 3. 检查是否包含医学专业网站
        medical_sites = ["维基百科", "百度百科", "丁香园", "好大夫在线", "春雨医生", "39健康网"]
        found_medical = [site for site in medical_sites if site in names]
        print(f"3. 专业医学网站: {len(found_medical)}/{len(medical_sites)} 个")
        
        # 4. 检查是否避免了技术网站
        tech_sites = ["菜鸟教程", "Python文档", "阿里云", "CSDN", "GitHub"]
        found_tech = [site for site in tech_sites if site in names]
        print(f"4. 技术网站污染: {len(found_tech)} 个 {'❌' if found_tech else '✅'}")
        
        if found_tech:
            print(f"   发现技术网站: {found_tech}")
        
        print("\n📋 医疗健康网站列表:")
        for i, (name, url) in enumerate(zip(names, urls), 1):
            print(f"   {i:2d}. {name}")
        
        # 5. 测试关键词推荐
        try:
            from src.processors.web_to_kb_processor import WebToKBProcessor
            processor = WebToKBProcessor()
            recommended = processor.recommend_sites_for_keyword("卵巢癌")
            print(f"\n5. 关键词推荐测试: {len(recommended)} 个网站")
            print(f"   推荐网站: {', '.join(recommended)}")
            
            # 检查推荐是否包含医学网站
            medical_in_rec = any(site in recommended for site in ["丁香园", "好大夫在线", "春雨医生"])
            print(f"   包含专业医学网站: {'✅' if medical_in_rec else '❌'}")
            
        except Exception as e:
            print(f"5. 关键词推荐测试: ❌ 错误 - {e}")
        
        print("\n" + "=" * 50)
        
        # 总结
        if medical_found and len(names) >= 5 and not found_tech:
            print("✅ 医疗搜索配置正确！")
            print("💡 现在搜索'卵巢癌'应该只返回医学相关内容")
        else:
            print("❌ 医疗搜索配置存在问题")
            if not medical_found:
                print("   - 缺少医疗健康行业")
            if len(names) < 5:
                print("   - 医疗网站数量不足")
            if found_tech:
                print("   - 存在技术网站污染")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

if __name__ == "__main__":
    test_medical_search_config()
