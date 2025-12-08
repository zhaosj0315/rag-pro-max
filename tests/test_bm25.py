#!/usr/bin/env python3
"""BM25 混合检索功能验证脚本"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

print("🔍 测试 BM25 混合检索功能...")
print()

# 1. 测试导入
try:
    from llama_index.retrievers.bm25 import BM25Retriever
    from llama_index.core.retrievers import QueryFusionRetriever
    print("✅ 1. BM25Retriever 导入成功")
except ImportError as e:
    print(f"❌ 1. 导入失败: {e}")
    exit(1)

# 2. 测试基本功能
try:
    from llama_index.core import Document, VectorStoreIndex, Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    
    # 设置嵌入模型
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-zh-v1.5",
        cache_folder="./hf_cache"
    )
    
    # 创建测试文档
    docs = [
        Document(text="Python 3.8 是一个编程语言版本"),
        Document(text="Java 是面向对象的编程语言"),
        Document(text="JavaScript 用于网页开发"),
        Document(text="Python 非常适合数据分析"),
    ]
    
    # 创建索引
    index = VectorStoreIndex.from_documents(docs, show_progress=False)
    print("✅ 2. 向量索引创建成功")
    
    # 获取所有节点
    nodes = list(index.docstore.docs.values())
    
    # 创建 BM25 检索器
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes,
        similarity_top_k=2
    )
    print("✅ 3. BM25 检索器创建成功")
    
    # 创建向量检索器
    vector_retriever = index.as_retriever(similarity_top_k=2)
    print("✅ 4. 向量检索器创建成功")
    
    # 创建融合检索器
    fusion_retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=3,
        num_queries=1,
        mode="reciprocal_rerank",
        use_async=False,
    )
    print("✅ 5. 融合检索器创建成功")
    
    # 测试查询
    results = fusion_retriever.retrieve("Python 3.8")
    
    if results and len(results) > 0:
        print(f"✅ 6. 混合检索测试成功")
        print(f"   └─ 返回 {len(results)} 个节点")
        print(f"   └─ 最相关: {results[0].text[:30]}...")
    else:
        print("❌ 6. 查询返回空结果")
        exit(1)
        
except Exception as e:
    print(f"❌ 功能测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("✅ BM25 混合检索功能验证通过！")
