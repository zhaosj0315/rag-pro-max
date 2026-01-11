import os
import sys
import json
from unittest.mock import MagicMock

# 模拟环境
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def test_engine_structure():
    print("🔍 正在测试 DataAnalystEngine 结构...")
    try:
        from src.processors.data_analyst import DataAnalystEngine
        # 使用真实的知识库路径尝试初始化
        kb_path = "vector_db_storage/guest_user_csv知识库_20260111"
        if not os.path.exists(kb_path):
            os.makedirs(kb_path, exist_ok=True)
            
        engine = DataAnalystEngine(kb_path)
        
        # 验证核心方法是否存在
        methods = ["execute_analysis", "execute_sql", "_recover_data_from_docstore"]
        for m in methods:
            if hasattr(engine, m):
                print(f"  ✅ 方法 {m} 存在")
            else:
                raise AttributeError(f"  ❌ 缺失核心方法: {m}")
        
        # 验证接口兼容性 (ChatMessage)
        print("🔍 正在测试 LlamaIndex ChatMessage 兼容性...")
        from llama_index.core.base.llms.types import ChatMessage, MessageRole
        msg = ChatMessage(role=MessageRole.USER, content="test")
        print(f"  ✅ ChatMessage 对象创建成功: {msg.role}")
        
        print("\n🎉 [SUCCESS] DataAnalystEngine 逻辑结构验证通过，无语法或接口错误。")
        return True
    except Exception as e:
        print(f"\n❌ [FAILED] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_engine_structure():
        sys.exit(0)
    else:
        sys.exit(1)
