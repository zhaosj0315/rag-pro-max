"""
RAG Pro Max - RAG 核心引擎
提取自 apppro.py，负责知识库的创建、加载和查询
"""

import os
import time
import shutil
from typing import List, Dict, Optional, Tuple
from llama_index.core import (
    VectorStoreIndex, 
    StorageContext, 
    load_index_from_storage,
    Settings,
    PromptTemplate
)
from llama_index.core.schema import Document


class RAGEngine:
    """RAG 核心引擎"""
    
    def __init__(
        self, 
        kb_name: str,
        persist_dir: str,
        embed_model,
        llm_model,
        logger=None
    ):
        """
        初始化 RAG 引擎
        
        Args:
            kb_name: 知识库名称
            persist_dir: 持久化目录
            embed_model: 嵌入模型
            llm_model: LLM 模型
            logger: 日志记录器
        """
        self.kb_name = kb_name
        self.persist_dir = persist_dir
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.logger = logger
        self.index = None
        
        # 设置全局模型
        if embed_model:
            Settings.embed_model = embed_model
        if llm_model:
            Settings.llm = llm_model
    
    def load_existing_index(self) -> bool:
        """
        加载已有索引
        
        Returns:
            bool: 是否成功加载
        """
        if not os.path.exists(self.persist_dir):
            return False
        
        try:
            if self.logger:
                self.logger.info(f"📂 加载现有索引: {self.kb_name}")
            
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            self.index = load_index_from_storage(storage_context)
            
            if self.logger:
                self.logger.success("✅ 索引加载成功")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if self.logger:
                if "shapes" in error_msg and "not aligned" in error_msg:
                    self.logger.warning("⚠️  向量维度不匹配，需要重建索引")
                else:
                    self.logger.warning(f"⚠️  索引加载失败: {error_msg}")
            
            # 清理损坏的索引
            shutil.rmtree(self.persist_dir, ignore_errors=True)
            self.index = None
            return False
    
    def create_index(
        self, 
        documents: List[Document],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """
        创建向量索引
        
        Args:
            documents: 文档列表
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            show_progress: 是否显示进度
            
        Returns:
            VectorStoreIndex: 创建的索引
        """
        if self.logger:
            self.logger.info(f"🔨 创建向量索引: {len(documents)} 个文档")
        
        start_time = time.time()
        
        # 创建索引
        if self.index:
            # 追加到现有索引
            if self.logger:
                self.logger.info("📝 追加文档到现有索引")
            for doc in documents:
                self.index.insert(doc)
        else:
            # 创建新索引
            if self.logger:
                self.logger.info("🆕 创建新索引")
            self.index = VectorStoreIndex.from_documents(
                documents,
                show_progress=show_progress
            )
        
        # 持久化
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        
        elapsed = time.time() - start_time
        if self.logger:
            self.logger.success(f"✅ 索引创建完成 (耗时 {elapsed:.1f}s)")
        
        return self.index
    
    def get_query_engine(
        self,
        similarity_top_k: int = 5,
        streaming: bool = True
    ):
        """
        获取查询引擎
        
        Args:
            similarity_top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            查询引擎对象
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
        
        # 定义中文问答模板 (优化 Gemini/DeepSeek 等模型的指令遵循)
        qa_prompt_tmpl_str = (
            "以下是已知信息：\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "请完全根据上述上下文信息回答用户的问题。不要使用外部知识。\n"
            "如果上下文中包含相关信息，请详细回答。\n"
            "如果上下文中没有相关信息，请回答“知识库中未找到相关内容”。\n"
            "问题：{query_str}\n"
            "回答："
        )
        qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
        
        return self.index.as_query_engine(
            similarity_top_k=similarity_top_k,
            streaming=streaming,
            text_qa_template=qa_prompt_tmpl
        )

    def get_chat_engine(
        self,
        chat_mode: str = "context",
        similarity_top_k: int = 5,
        streaming: bool = True
    ):
        """
        获取聊天引擎
        
        Args:
            chat_mode: 聊天模式 ("context", "condense_question", "simple")
            similarity_top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            聊天引擎对象
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
            
        from llama_index.core.memory import ChatMemoryBuffer
        
        return self.index.as_chat_engine(
            chat_mode=chat_mode,
            memory=ChatMemoryBuffer.from_defaults(token_limit=2000),
            similarity_top_k=similarity_top_k,
            streaming=streaming,
            system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。"
        )
    
    def query(
        self, 
        question: str,
        top_k: int = 5,
        streaming: bool = True
    ):
        """
        查询知识库
        
        Args:
            question: 查询问题
            top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            查询响应
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
        
        if self.logger:
            self.logger.info(f"🔍 查询: {question[:50]}...")
        
        query_engine = self.get_query_engine(
            similarity_top_k=top_k,
            streaming=streaming
        )
        
        start_time = time.time()
        response = query_engine.query(question)
        elapsed = time.time() - start_time
        
        if self.logger:
            self.logger.success(f"✅ 查询完成 (耗时 {elapsed:.1f}s)")
        
        return response
    
    def get_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.index:
            return {
                "status": "未加载",
                "documents": 0,
                "nodes": 0
            }
        
        try:
            docstore = self.index.docstore
            nodes = list(docstore.docs.values())
            
            return {
                "status": "已加载",
                "documents": len(set(n.ref_doc_id for n in nodes if hasattr(n, 'ref_doc_id'))),
                "nodes": len(nodes),
                "persist_dir": self.persist_dir
            }
        except:
            return {
                "status": "已加载",
                "persist_dir": self.persist_dir
            }
    
    def delete(self):
        """删除知识库"""
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
            if self.logger:
                self.logger.success(f"✅ 知识库已删除: {self.kb_name}")
        
        self.index = None
    
    def __repr__(self):
        stats = self.get_stats()
        return f"RAGEngine(kb_name='{self.kb_name}', status='{stats['status']}')"


def create_rag_engine(kb_name: str, logger=None) -> Optional['RAGEngine']:
    """
    创建 RAGEngine 实例的工厂函数
    
    Args:
        kb_name: 知识库名称（可能带前缀）
        logger: 日志记录器
        
    Returns:
        RAGEngine 实例，如果创建失败则返回 None
    """
    try:
        from src.core.app_config import load_config, output_base
        from src.utils.model_manager import load_embedding_model, load_llm_model
        
        # 加载配置
        config = load_config()
        
        # 解析知识库路径 - 支持用户权限控制
        try:
            # 根据知识库名称格式确定路径
            if kb_name.startswith('[历史] '):
                # 历史知识库在根目录
                actual_kb_name = kb_name[5:]  # 移除 "[历史] " 前缀
                persist_dir = os.path.join("vector_db_storage", actual_kb_name)
            elif kb_name.startswith('[') and '] ' in kb_name:
                # 格式: [username] kb_name
                kb_owner = kb_name.split('] ')[0][1:]
                actual_kb_name = kb_name.split('] ')[1]
                persist_dir = os.path.join("vector_db_storage", kb_owner, actual_kb_name)
            else:
                # 普通格式，使用用户上下文
                try:
                    from src.auth.user_context import UserContext
                    persist_dir = UserContext.get_user_kb_path(kb_name)
                except:
                    persist_dir = os.path.join(output_base, kb_name)
        except:
            # 向后兼容
            persist_dir = os.path.join(output_base, kb_name)
        
        # 确保配置值有效 (防止空字符串导致模型加载失败)
        llm_provider = config.get('llm_provider') or "Ollama"
        llm_model_name = config.get('llm_model') or "gpt-oss:20b"
        
        # 加载 Embedding 模型
        embed_model = load_embedding_model(
            provider=config.get('embed_provider'),
            model_name=config.get('embed_model'),
            api_key=config.get('embed_key'),
            api_url=config.get('embed_url')
        )
        
        # 加载 LLM 模型
        llm_model = load_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            api_key=config.get('llm_key'),
            api_url=config.get('llm_url'),
            temperature=config.get('temperature', 0.7)
        )
        
        # 创建引擎实例
        engine = RAGEngine(
            kb_name=kb_name,
            persist_dir=persist_dir,
            embed_model=embed_model,
            llm_model=llm_model,
            logger=logger
        )
        
        # 加载已有索引
        if engine.load_existing_index():
            return engine
        else:
            if logger:
                logger.error(f"❌ 无法加载知识库索引: {kb_name} (路径: {persist_dir})")
            return None
            
    except Exception as e:
        if logger:
            logger.error(f"❌ 创建 RAG 引擎失败: {str(e)} (知识库: {kb_name})")
        else:
            print(f"❌ 创建 RAG 引擎失败: {str(e)} (知识库: {kb_name})")
        return None