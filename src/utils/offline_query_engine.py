
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
                context = "\n\n".join([node.text[:200] + "..." for node in nodes[:3]])
                response = f"基于文档检索结果：\n\n{context}"
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
