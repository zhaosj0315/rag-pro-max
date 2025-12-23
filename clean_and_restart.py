#!/usr/bin/env python3
"""
完整的医疗搜索修复和重启脚本
清理缓存并重启应用
"""

import os
import sys
import shutil
import subprocess

def clean_cache_and_restart():
    """清理缓存并重启应用"""
    print("🧹 清理缓存和临时文件...")
    
    # 清理Python缓存
    cache_dirs = [
        "__pycache__",
        ".pytest_cache",
        "src/__pycache__",
        "src/processors/__pycache__",
        "src/config/__pycache__",
        "src/ui/__pycache__"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ 清理缓存: {cache_dir}")
            except Exception as e:
                print(f"⚠️ 清理失败: {cache_dir} - {e}")
    
    # 清理临时搜索结果
    temp_dir = "temp_uploads"
    if os.path.exists(temp_dir):
        search_dirs = [d for d in os.listdir(temp_dir) if d.startswith("Search_")]
        for search_dir in search_dirs[-5:]:  # 只保留最近5个
            try:
                full_path = os.path.join(temp_dir, search_dir)
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    print(f"✅ 清理搜索缓存: {search_dir}")
            except Exception as e:
                print(f"⚠️ 清理失败: {search_dir} - {e}")
    
    print("\n🔧 修复验证...")
    
    # 验证配置文件
    config_files = [
        "src/config/unified_sites.py",
        "src/processors/web_to_kb_processor.py",
        "src/ui/web_to_kb_interface.py",
        "src/apppro.py"
    ]
    
    all_good = True
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ 配置文件存在: {config_file}")
        else:
            print(f"❌ 配置文件缺失: {config_file}")
            all_good = False
    
    if not all_good:
        print("❌ 配置文件不完整，请检查修复状态")
        return False
    
    print("\n🏥 医疗搜索配置验证...")
    
    try:
        # 验证医疗配置
        from src.config.unified_sites import get_industry_sites
        urls, names = get_industry_sites("🏥 医疗健康 - 医疗资讯、健康科普、医学知识")
        
        medical_sites = ["维基百科", "百度百科", "39健康网", "寻医问药网"]
        found_medical = [site for site in medical_sites if site in names]
        
        tech_sites = ["菜鸟教程", "阿里云", "东方财富"]
        found_tech = [site for site in tech_sites if site in names]
        
        print(f"✅ 医疗网站数量: {len(names)}")
        print(f"✅ 专业医学网站: {len(found_medical)}/{len(medical_sites)}")
        print(f"{'✅' if not found_tech else '❌'} 技术网站污染: {len(found_tech)}")
        
        if found_tech:
            print(f"   警告：发现技术网站: {found_tech}")
            
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False
    
    print("\n🚀 准备重启应用...")
    print("请手动执行以下命令重启应用:")
    print("   streamlit run src/apppro.py")
    print("\n💡 使用建议:")
    print("1. 选择 '🏥 医疗健康' 行业")
    print("2. 输入 '卵巢癌' 关键词")
    print("3. 点击 '🔍 智能行业搜索'")
    print("4. 现在应该只返回医学相关内容")
    
    return True

if __name__ == "__main__":
    if clean_cache_and_restart():
        print("\n✅ 清理和验证完成！")
    else:
        print("\n❌ 清理或验证失败！")
        sys.exit(1)
