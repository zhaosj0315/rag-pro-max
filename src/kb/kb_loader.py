"""
知识库加载器模块
负责知识库的挂载、初始化和配置
"""

import os
import time
import json
import glob
import threading
import streamlit as st
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.memory import ChatMemoryBuffer

from src.logging import LogManager
from src.config import ManifestManager
from src.utils.model_manager import load_embedding_model

logger = LogManager()


class KnowledgeBaseLoader:
    """知识库加载器"""
    
    def __init__(self, output_base):
        self.output_base = output_base
    
    def get_kb_embedding_dim(self, db_path):
        """检测知识库的向量维度"""
        try:
            # 尝试读取 .kb_info.json
            kb_info_file = os.path.join(db_path, ".kb_info.json")
            if os.path.exists(kb_info_file):
                with open(kb_info_file, 'r') as f:
                    kb_info = json.load(f)
                    model = kb_info.get('embedding_model', '')
                    # 根据模型名推断维度
                    if 'small' in model:
                        return 512
                    elif 'base' in model:
                        return 768
                    elif 'm3' in model:
                        return 1024
            
            # 尝试从向量文件推断
            vector_files = glob.glob(os.path.join(db_path, "**/*.json"), recursive=True)
            if vector_files:
                # 简单启发式：根据文件大小推断
                total_size = sum(os.path.getsize(f) for f in vector_files) / (1024 * 1024)
                if total_size < 50:
                    return 512  # 小模型
                elif total_size < 200:
                    return 768  # 中模型
                else:
                    return 1024  # 大模型
        except:
            pass
        return None
    
    def load_knowledge_base(self, kb_name, embed_provider, embed_model, embed_key, embed_url):
        """加载知识库"""
        db_path = os.path.join(self.output_base, kb_name)
        
        if not os.path.exists(db_path):
            return None, "知识库不存在"
        
        try:
            logger.log("INFO", f"开始加载知识库: {kb_name}", stage="知识库加载")
            
            # 检测知识库的向量维度
            kb_dim = self.get_kb_embedding_dim(db_path)
            if kb_dim:
                model_map = {
                    512: "BAAI/bge-small-zh-v1.5",
                    768: "BAAI/bge-base-zh-v1.5", 
                    1024: "BAAI/bge-m3"
                }
                
                if kb_dim in model_map:
                    required_model = model_map[kb_dim]
                    if embed_model != required_model:
                        logger.warning(f"⚠️ 知识库维度: {kb_dim}D，自动切换模型: {required_model}")
                        embed_model = required_model
                        embed = load_embedding_model(embed_provider, embed_model, embed_key, embed_url)
                        if embed:
                            from llama_index.core import Settings
                            Settings.embed_model = embed
            
            # 检查知识库大小
            vector_files = glob.glob(os.path.join(db_path, "**/*.json"), recursive=True)
            total_size = sum(os.path.getsize(f) for f in vector_files) / (1024 * 1024)
            is_large_kb = len(vector_files) > 100 or total_size > 100
            
            if is_large_kb:
                return self._load_large_kb(db_path, kb_name, vector_files, total_size)
            else:
                return self._load_small_kb(db_path, kb_name, embed_provider, embed_model, embed_key, embed_url)
                
        except Exception as e:
            logger.log("ERROR", f"知识库加载失败: {kb_name} - {str(e)}", stage="知识库加载")
            return None, f"知识库挂载失败：{e}"
    
    def _load_large_kb(self, db_path, kb_name, vector_files, total_size):
        """加载大型知识库"""
        load_start = time.time()
        logger.info(f"📊 知识库统计: {len(vector_files)} 个文件, {total_size:.1f}MB")
        
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0, text="⏳ 准备加载知识库... 0%")
        
        with st.status(f"📚 正在挂载大型知识库: {kb_name}（{len(vector_files)} 个文件, {total_size:.1f}MB）", expanded=True) as status:
            # 阶段1: 加载向量数据
            status.write("⏳ [1/3] 正在加载向量数据...")
            logger.processing("[1/3] 开始加载向量数据...")
            
            stage1_start = time.time()
            storage_context = self._load_with_progress(
                lambda: StorageContext.from_defaults(persist_dir=db_path),
                progress_bar, 5, 39, "[1/3] 加载向量数据"
            )
            stage1_time = time.time() - stage1_start
            
            progress_bar.progress(40, text=f"✅ [1/3] 向量数据加载完成 ({stage1_time:.1f}s) - 40%")
            status.write(f"✅ [1/3] 向量数据加载完成 (耗时 {stage1_time:.1f}s)")
            
            # 阶段2: 构建索引
            status.write("⏳ [2/3] 正在构建索引...")
            logger.processing("[2/3] 开始构建索引...")
            
            stage2_start = time.time()
            index = self._load_with_progress(
                lambda: load_index_from_storage(storage_context),
                progress_bar, 45, 79, "[2/3] 构建索引"
            )
            stage2_time = time.time() - stage2_start
            
            progress_bar.progress(80, text=f"✅ [2/3] 索引构建完成 ({stage2_time:.1f}s) - 80%")
            status.write(f"✅ [2/3] 索引构建完成 (耗时 {stage2_time:.1f}s)")
            
            # 阶段3: 初始化问答引擎
            status.write("⏳ [3/3] 正在初始化问答引擎...")
            logger.processing("[3/3] 初始化问答引擎...")
            
            stage3_start = time.time()
            chat_engine = self._create_chat_engine(index, db_path, status)
            stage3_time = time.time() - stage3_start
            load_time = time.time() - load_start
            
            progress_bar.progress(100, text=f"✅ 全部完成！总耗时: {load_time:.1f}s - 100%")
            status.write(f"✅ [3/3] 问答引擎初始化完成 (耗时 {stage3_time:.1f}s)")
            status.update(label=f"✅ 知识库 '{kb_name}' 挂载成功！总耗时: {load_time:.1f}s", state="complete")
            
            # 清理进度条
            time.sleep(1.5)
            progress_placeholder.empty()
            
            return chat_engine, None
    
    def _load_small_kb(self, db_path, kb_name, embed_provider, embed_model, embed_key, embed_url):
        """加载小型知识库"""
        with st.spinner(f"📚 正在挂载知识库: {kb_name}..."):
            try:
                # 读取知识库信息
                kb_info_file = os.path.join(db_path, ".kb_info.json")
                if os.path.exists(kb_info_file):
                    with open(kb_info_file, 'r') as f:
                        kb_info = json.load(f)
                        kb_embed_model = kb_info.get('embedding_model', 'BAAI/bge-large-zh-v1.5')
                else:
                    kb_manifest = ManifestManager.load(db_path)
                    kb_embed_model = kb_manifest.get('embed_model', 'BAAI/bge-large-zh-v1.5')
                
                # 使用知识库的模型加载
                embed = load_embedding_model(embed_provider, kb_embed_model, embed_key, embed_url)
                if embed:
                    from llama_index.core import Settings
                    Settings.embed_model = embed
                else:
                    raise ValueError(f"无法加载嵌入模型: {kb_embed_model}")
                
                storage_context = StorageContext.from_defaults(persist_dir=db_path)
                index = load_index_from_storage(storage_context)
                
                chat_engine = index.as_chat_engine(
                    chat_mode="context",
                    memory=ChatMemoryBuffer.from_defaults(token_limit=2000),
                    similarity_top_k=3,
                    streaming=True,
                    timeout=25.0,
                    system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。"
                )
                
                return chat_engine, None
                
            except Exception as e:
                if "shapes" in str(e) and "not aligned" in str(e):
                    return None, self._handle_dimension_mismatch(embed_model, str(e))
                else:
                    raise
    
    def _load_with_progress(self, load_func, progress_bar, start_progress, end_progress, stage_name):
        """带进度显示的加载"""
        result = [None]
        
        def load_task():
            result[0] = load_func()
        
        thread = threading.Thread(target=load_task)
        thread.start()
        
        progress = start_progress
        stage_start = time.time()
        while thread.is_alive():
            progress = min(progress + 1, end_progress)
            elapsed = time.time() - stage_start
            progress_bar.progress(progress, text=f"⏳ {stage_name}... {progress}% (已用时 {elapsed:.0f}s)")
            time.sleep(0.5)
        
        thread.join()
        return result[0]
    
    def _create_chat_engine(self, index, db_path, status):
        """创建聊天引擎"""
        node_postprocessors = []
        similarity_top_k = 5
        retriever = None
        
        # BM25 混合检索配置
        if st.session_state.get('enable_bm25', False):
            try:
                from llama_index.retrievers.bm25 import BM25Retriever
                from llama_index.core.retrievers import QueryFusionRetriever
                
                status.write("   🔍 构建 BM25 混合检索...")
                nodes = index.docstore.docs.values()
                
                bm25_retriever = BM25Retriever.from_defaults(
                    nodes=list(nodes),
                    similarity_top_k=5
                )
                
                vector_retriever = index.as_retriever(similarity_top_k=5)
                
                retriever = QueryFusionRetriever(
                    retrievers=[vector_retriever, bm25_retriever],
                    similarity_top_k=5,
                    num_queries=1,
                    mode="reciprocal_rerank",
                    use_async=False,
                )
                
                status.write("   ✅ BM25 混合检索构建成功")
            except Exception as e:
                status.write(f"   ⚠️ BM25 构建失败: {e}")
        
        # Re-ranking 配置
        if st.session_state.get('enable_rerank', False):
            try:
                from llama_index.core.postprocessor import SentenceTransformerRerank
                
                rerank_model = st.session_state.get('rerank_model', 'BAAI/bge-reranker-base')
                status.write(f"   🎯 加载 Re-ranking 模型: {rerank_model}...")
                
                reranker = SentenceTransformerRerank(
                    top_n=3,
                    model=rerank_model,
                    keep_retrieval_score=True,
                )
                node_postprocessors.append(reranker)
                similarity_top_k = 10
                
                status.write("   ✅ Re-ranking 模型加载成功")
            except Exception as e:
                status.write(f"   ⚠️ Re-ranking 加载失败: {e}")
        
        # 创建查询引擎
        if retriever:
            return index.as_chat_engine(
                chat_mode="context",
                retriever=retriever,
                memory=ChatMemoryBuffer.from_defaults(token_limit=2000),
                similarity_top_k=3,
                streaming=True,
                timeout=25.0,
                system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。",
                node_postprocessors=node_postprocessors if node_postprocessors else None
            )
        else:
            return index.as_chat_engine(
                chat_mode="context",
                memory=ChatMemoryBuffer.from_defaults(token_limit=2000),
                similarity_top_k=3,
                streaming=True,
                timeout=25.0,
                system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。",
                node_postprocessors=node_postprocessors if node_postprocessors else None
            )
    
    def _handle_dimension_mismatch(self, embed_model, error_msg):
        """处理维度不匹配错误"""
        logger.warning("⚠️ 向量维度不匹配")
        logger.info(f"当前模型: {embed_model}")
        logger.info(f"错误信息: {error_msg}")
        
        st.error("❌ 向量维度不匹配")
        st.warning(f"""
**当前模型:** {embed_model}

**原因:** 知识库是用其他维度的模型创建的，无法直接查询。

**解决方案:**
1. **保留旧数据** - 切换回原模型（bge-small-zh-v1.5）
2. **重建索引** - 用新模型重新嵌入所有文档（耗时较长）
""")
        
        return "维度不匹配错误"
