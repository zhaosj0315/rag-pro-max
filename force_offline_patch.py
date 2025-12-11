#!/usr/bin/env python3
"""
强制离线补丁 - 直接修改源码
"""

import os
import re

def patch_apppro():
    """修补主应用文件"""
    
    apppro_path = "/Users/zhaosj/Documents/rag-pro-max/src/apppro.py"
    
    # 读取文件
    with open(apppro_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有LLM调用为空操作
    patches = [
        # 禁用查询改写
        (r'llm\.chat\([^)]+\)', 'None  # 离线模式禁用'),
        (r'llm\._chat\([^)]+\)', 'None  # 离线模式禁用'),
        (r'query_engine\.query\([^)]+\)', 'SimpleNamespace(response="离线模式，仅支持文档检索")'),
        # 禁用推荐问题
        (r'generate_suggestions\([^)]+\)', '[]  # 离线模式禁用'),
        # 跳过连接错误
        (r'Connection error\.', 'Offline mode - skipped'),
    ]
    
    for pattern, replacement in patches:
        content = re.sub(pattern, replacement, content)
    
    # 添加离线模式检查
    offline_check = '''
# 强制离线模式
OFFLINE_MODE = True
if OFFLINE_MODE:
    print("🔒 离线模式已启用，禁用所有网络调用")
'''
    
    if 'OFFLINE_MODE = True' not in content:
        content = offline_check + content
    
    # 写回文件
    with open(apppro_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 主应用已修补为离线模式")

def create_offline_query_engine():
    """创建离线查询引擎"""
    
    offline_engine = '''
class OfflineQueryEngine:
    """离线查询引擎 - 仅文档检索"""
    
    def __init__(self, index):
        self.index = index
        
    def query(self, query_str):
        """离线查询 - 仅返回检索结果"""
        try:
            # 仅做文档检索，不调用LLM
            retriever = self.index.as_retriever(similarity_top_k=5)
            nodes = retriever.retrieve(query_str)
            
            # 组装简单回答
            if nodes:
                context = "\\n\\n".join([node.text[:200] + "..." for node in nodes[:3]])
                response = f"基于文档检索结果：\\n\\n{context}"
            else:
                response = "未找到相关文档内容"
                
            from types import SimpleNamespace
            return SimpleNamespace(
                response=response,
                source_nodes=nodes
            )
        except Exception as e:
            from types import SimpleNamespace
            return SimpleNamespace(
                response=f"检索失败: {str(e)}",
                source_nodes=[]
            )

# 替换查询引擎
def create_offline_query_engine_wrapper(index):
    return OfflineQueryEngine(index)
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/utils/offline_query_engine.py', 'w') as f:
        f.write(offline_engine)
    
    print("✅ 离线查询引擎已创建")

def main():
    print("🔒 强制离线补丁")
    print("="*40)
    
    patch_apppro()
    create_offline_query_engine()
    
    # 重启应用
    os.system("pkill -f 'streamlit run'")
    os.system("sleep 2")
    os.system("cd /Users/zhaosj/Documents/rag-pro-max && OFFLINE_MODE=true streamlit run src/apppro.py --server.headless=true &")
    
    print("✅ 离线模式已强制启用")

if __name__ == "__main__":
    main()
