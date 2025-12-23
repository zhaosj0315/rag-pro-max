#!/usr/bin/env python3
"""
查询错误诊断脚本
分析查询处理中的错误原因
"""

import sys
import os
sys.path.append('src')

def diagnose_query_error():
    """诊断查询错误"""
    print("🔍 诊断查询处理错误...")
    
    try:
        # 1. 检查知识库加载器
        from src.kb.kb_loader import KnowledgeBaseLoader
        print("✅ KnowledgeBaseLoader 导入成功")
        
        # 2. 检查嵌入模型
        from src.utils.model_manager import get_embed
        print("✅ get_embed 导入成功")
        
        # 3. 检查配置
        from src.config import ConfigLoader
        config = ConfigLoader.load()
        print(f"✅ 配置加载成功: {len(config)} 项")
        
        # 4. 测试知识库加载
        kb_loader = KnowledgeBaseLoader("vector_db_storage")
        print("✅ KnowledgeBaseLoader 初始化成功")
        
        # 5. 列出可用知识库
        from src.kb import KBManager
        kb_manager = KBManager()
        kb_manager.base_path = "vector_db_storage"
        kbs = kb_manager.list_all()
        print(f"✅ 发现 {len(kbs)} 个知识库: {kbs[:3]}...")
        
        if kbs:
            # 6. 尝试加载第一个知识库
            test_kb = kbs[0]
            print(f"🧪 测试加载知识库: {test_kb}")
            
            try:
                chat_engine, error_msg, kb_index = kb_loader.load_knowledge_base(
                    test_kb, "ollama", "all-MiniLM-L6-v2", "", "http://localhost:11434"
                )
                
                if chat_engine:
                    print("✅ 知识库加载成功")
                    print(f"   chat_engine 类型: {type(chat_engine)}")
                    print(f"   是否有 stream_chat: {hasattr(chat_engine, 'stream_chat')}")
                    print(f"   是否有 query: {hasattr(chat_engine, 'query')}")
                    
                    # 7. 测试简单查询
                    try:
                        test_query = "测试查询"
                        print(f"🧪 测试查询: {test_query}")
                        
                        if hasattr(chat_engine, 'query'):
                            result = chat_engine.query(test_query)
                            print(f"✅ query 方法正常: {type(result)}")
                        
                        if hasattr(chat_engine, 'stream_chat'):
                            result = chat_engine.stream_chat(test_query)
                            print(f"✅ stream_chat 方法正常: {type(result)}")
                            
                            # 尝试获取第一个token
                            try:
                                first_token = next(result.response_gen)
                                print(f"✅ 流式响应正常: {first_token[:50]}...")
                            except Exception as e:
                                print(f"❌ 流式响应错误: {e}")
                        
                    except Exception as e:
                        print(f"❌ 查询测试失败: {e}")
                        import traceback
                        traceback.print_exc()
                        
                else:
                    print(f"❌ 知识库加载失败: {error_msg}")
                    
            except Exception as e:
                print(f"❌ 知识库加载异常: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 RAG Pro Max 查询错误诊断")
    print("=" * 50)
    
    success = diagnose_query_error()
    
    if success:
        print("\n✅ 诊断完成")
    else:
        print("\n❌ 诊断失败")
