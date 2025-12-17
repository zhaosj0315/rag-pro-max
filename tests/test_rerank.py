#!/usr/bin/env python3
"""Re-ranking 功能验证脚本"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

print("🔍 测试 Re-ranking 功能...")
print()

# 1. 测试导入
try:
    from llama_index.core.postprocessor import SentenceTransformerRerank
    print("✅ 1. SentenceTransformerRerank 导入成功")
except ImportError as e:
    print(f"❌ 1. 导入失败: {e}")
    exit(1)

# 2. 测试模型加载
try:
    reranker = SentenceTransformerRerank(
        top_n=3,
        model="BAAI/bge-reranker-base",
        keep_retrieval_score=True,
    )
    print("✅ 2. Re-ranking 模型初始化成功")
except Exception as e:
    print(f"❌ 2. 模型初始化失败: {e}")
    exit(1)

# 3. 测试基本功能
try:
    from llama_index.core import Document, VectorStoreIndex, Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    
    # 设置嵌入模型
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_folder="./hf_cache"
    )
    
    # 创建测试文档
    docs = [
        Document(text="Python 是一种高级编程语言"),
        Document(text="Java 是一种面向对象的编程语言"),
        Document(text="JavaScript 用于网页开发"),
    ]
    
    # 创建索引
    index = VectorStoreIndex.from_documents(docs, show_progress=False)
    
    # 创建查询引擎（带 Re-ranking）
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        node_postprocessors=[reranker]
    )
    
    # 测试查询
    response = query_engine.query("什么是 Python？")
    
    if response and len(response.source_nodes) > 0:
        print("✅ 3. Re-ranking 查询测试成功")
        print(f"   └─ 返回 {len(response.source_nodes)} 个节点")
    else:
        print("❌ 3. 查询返回空结果")
        exit(1)
        
except Exception as e:
    print(f"❌ 3. 功能测试失败: {e}")
    exit(1)

print()
print("✅ Re-ranking 功能验证通过！")
