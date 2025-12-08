#!/usr/bin/env python3
"""测试 chat_engine 的维度问题"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.llms.ollama import Ollama
from custom_embeddings import create_custom_embedding

# 1. 加载嵌入模型
print("=" * 60)
print("1. 加载嵌入模型")
print("=" * 60)
embed_model = create_custom_embedding(
    model_name="BAAI/bge-large-zh-v1.5",
    cache_folder="./hf_cache",
    batch_size=64,
    device="cpu"
)
Settings.embed_model = embed_model
print(f"✅ 嵌入模型维度: {len(embed_model._get_text_embedding('test'))}")

# 2. 加载 LLM
print("\n" + "=" * 60)
print("2. 加载 LLM")
print("=" * 60)
llm = Ollama(model="gpt-oss", base_url="http://127.0.0.1:11434", request_timeout=120.0)
Settings.llm = llm
print("✅ LLM 加载完成")

# 3. 加载知识库
print("\n" + "=" * 60)
print("3. 加载知识库")
print("=" * 60)
kb_path = "vector_db_storage/batch_1765157212"
storage_context = StorageContext.from_defaults(persist_dir=kb_path)
index = load_index_from_storage(storage_context)
print("✅ 知识库加载完成")

# 4. 创建 chat_engine
print("\n" + "=" * 60)
print("4. 创建 chat_engine")
print("=" * 60)
chat_engine = index.as_chat_engine(
    chat_mode="context",
    similarity_top_k=3
)
print("✅ chat_engine 创建完成")

# 5. 测试查询
print("\n" + "=" * 60)
print("5. 测试查询")
print("=" * 60)
try:
    response = chat_engine.chat("请简要总结这个知识库的内容")
    print(f"✅ 查询成功: {response.response[:100]}...")
except Exception as e:
    print(f"❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()
