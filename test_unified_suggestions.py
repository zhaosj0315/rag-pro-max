#!/usr/bin/env python3
"""
测试统一推荐问题生成系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_unified_suggestion_engine():
    """测试统一推荐引擎"""
    print("🧪 测试统一推荐问题生成系统")
    print("=" * 50)
    
    try:
        from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
        
        # 测试不同场景
        engine = get_unified_suggestion_engine("test_kb")
        
        # 1. 测试聊天场景
        print("1️⃣ 测试聊天场景")
        chat_context = "抑郁症的治疗方案包括药物治疗、心理治疗和物理治疗等多种方法。"
        chat_suggestions = engine.generate_suggestions(
            context=chat_context,
            source_type='chat',
            num_questions=3
        )
        print(f"   聊天推荐: {chat_suggestions}")
        
        # 2. 测试网页抓取场景
        print("\n2️⃣ 测试网页抓取场景")
        web_suggestions = engine.generate_suggestions(
            context="Python是一种高级编程语言，广泛用于数据科学和机器学习。",
            source_type='web_crawl',
            metadata={'url': 'https://python.org', 'files': []},
            num_questions=3
        )
        print(f"   网页推荐: {web_suggestions}")
        
        # 3. 测试文件上传场景
        print("\n3️⃣ 测试文件上传场景")
        file_suggestions = engine.generate_suggestions(
            context="本研究分析了机器学习在医疗诊断中的应用，包括深度学习和传统算法的对比。",
            source_type='file_upload',
            metadata={'file_type': 'pdf', 'file_name': '机器学习研究报告.pdf'},
            num_questions=3
        )
        print(f"   文件推荐: {file_suggestions}")
        
        # 4. 测试自定义推荐
        print("\n4️⃣ 测试自定义推荐")
        engine.add_custom_suggestion("这是一个自定义问题")
        custom_suggestions = engine.generate_suggestions(
            context="任意内容",
            source_type='chat',
            num_questions=3
        )
        print(f"   自定义推荐: {custom_suggestions}")
        
        # 5. 测试历史过滤
        print("\n5️⃣ 测试历史过滤")
        # 再次生成相同内容，应该过滤掉历史问题
        filtered_suggestions = engine.generate_suggestions(
            context=chat_context,
            source_type='chat',
            num_questions=3
        )
        print(f"   过滤后推荐: {filtered_suggestions}")
        
        print("\n✅ 统一推荐引擎测试完成！")
        print(f"📊 历史记录数量: {len(engine.history)}")
        print(f"📝 自定义问题数量: {len(engine.custom_suggestions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compatibility():
    """测试与现有系统的兼容性"""
    print("\n🔄 测试兼容性")
    print("=" * 30)
    
    try:
        # 测试是否能正常导入
        from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
        from src.services.configurable_industry_service import get_configurable_industry_service
        
        print("✅ 统一推荐引擎导入成功")
        print("✅ 可配置行业服务导入成功")
        
        # 测试基本功能
        engine = get_unified_suggestion_engine()
        suggestions = engine.generate_suggestions("测试内容", "chat")
        print(f"✅ 基本功能正常: 生成了 {len(suggestions)} 个问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        return False

if __name__ == "__main__":
    success1 = test_unified_suggestion_engine()
    success2 = test_compatibility()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！统一推荐系统可以使用。")
    else:
        print("\n⚠️ 部分测试失败，需要检查配置。")
