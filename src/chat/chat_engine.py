"""
聊天引擎
Stage 7.1 - 问答处理核心逻辑
"""

import time
import re
from typing import Dict, List, Optional, Any
import streamlit as st

from src.logging import LogManager
logger = LogManager()
from src.utils.parallel_executor import ParallelExecutor
from src.utils.parallel_tasks import process_node_worker


class ChatEngine:
    """聊天引擎 - 处理问答流程"""
    
    def __init__(self, query_engine, kb_name: str):
        """
        初始化聊天引擎
        
        Args:
            query_engine: LlamaIndex 查询引擎
            kb_name: 知识库名称
        """
        self.query_engine = query_engine
        self.kb_name = kb_name
        self.executor = ParallelExecutor()
    
    def process_question(
        self, 
        question: str,
        llm_model: str,
        quoted_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户问题
        
        Args:
            question: 用户问题
            llm_model: LLM 模型名称
            quoted_text: 引用的文本（可选）
        
        Returns:
            包含回答、来源、统计信息的字典
        """
        # 构建最终 prompt
        final_prompt = question
        if quoted_text:
            if len(quoted_text) > 2000:
                quoted_text = quoted_text[:2000] + "...(已截断)"
            final_prompt = f"基于以下引用内容：\n> {quoted_text}\n\n我的问题是：{question}"
            logger.info("📌 已应用引用内容")
        
        # 记录日志
        logger.separator("知识库查询")
        logger.start_operation("查询", f"知识库: {self.kb_name}")
        logger.log_user_question(final_prompt, kb_name=self.kb_name)
        
        # 开始计时
        start_time = time.time()
        
        # 显示检索增强功能
        enhancements = []
        if st.session_state.get('enable_bm25', False):
            enhancements.append("BM25混合检索")
        if st.session_state.get('enable_rerank', False):
            enhancements.append("Re-ranking重排序")
        
        if enhancements:
            enhancement_str = " + ".join(enhancements)
            logger.info(f"🎯 检索增强: {enhancement_str}")
            logger.log("查询对话", "检索增强", f"启用功能: {enhancement_str}")
        
        # 检索和生成
        with logger.timer("检索相关文档"):
            logger.log_retrieval_start(kb_name=self.kb_name)
            
            retrieval_start = time.time()
            response = self.query_engine.stream_chat(final_prompt)
            retrieval_time = time.time() - retrieval_start
            
            logger.info(f"🔍 检索耗时: {retrieval_time:.2f}s (GPU加速)")
            
            # 流式输出
            full_text = ""
            token_count = 0
            
            for token in response.response_gen:
                full_text += token
                token_count += 1
                yield {"type": "token", "content": token}
        
        # 提取 token 统计
        prompt_tokens = 0
        completion_tokens = 0
        
        if hasattr(response, 'raw') and response.raw:
            usage = response.raw.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
        
        # 如果没有真实 Usage，则估算
        if completion_tokens == 0:
            total_chars = len(full_text)
            chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', full_text))
            completion_tokens = int((chinese_chars * 1.5) + ((total_chars - chinese_chars) * 0.3))
            token_count = completion_tokens
        else:
            token_count = completion_tokens
        
        # 处理来源节点
        sources = []
        if response.source_nodes:
            logger.log_retrieval_result(len(response.source_nodes), kb_name=self.kb_name)
            logger.data_summary("检索结果", {
                "查询": final_prompt[:50] + "..." if len(final_prompt) > 50 else final_prompt,
                "相关文档": len(response.source_nodes),
                "知识库": self.kb_name
            })
            
            # 提取节点数据
            node_data = []
            for node in response.source_nodes:
                text = ''
                try:
                    if hasattr(node, 'get_text'):
                        text = node.get_text()
                    elif hasattr(node, 'text'):
                        text = node.text
                    elif hasattr(node, 'node') and hasattr(node.node, 'text'):
                        text = node.node.text
                    else:
                        text = str(node)[:150]
                except:
                    text = str(node)[:150]
                
                node_data.append({
                    'metadata': getattr(node, 'metadata', {}),
                    'score': getattr(node, 'score', 0.0),
                    'text': text
                })
            
            # 并行处理节点
            tasks = [(d, self.kb_name) for d in node_data]
            sources = [s for s in self.executor.execute(process_node_worker, tasks, threshold=10) if s]
            
            if len(node_data) >= 10:
                logger.info(f"⚡ 并行处理: {len(sources)} 个节点")
            else:
                logger.info(f"⚡ 串行处理: {len(sources)} 个节点")
        
        # 记录完成日志
        logger.log_answer_complete(
            kb_name=self.kb_name,
            model=llm_model,
            tokens=token_count,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # 计算总耗时
        total_time = time.time() - start_time
        logger.complete_operation(f"查询完成 (耗时 {total_time:.2f}s)")
        
        # 准备统计信息
        tokens_per_sec = token_count / total_time if total_time > 0 else 0
        stats = {
            "time": total_time,
            "tokens": token_count,
            "tokens_per_sec": tokens_per_sec,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }
        
        yield {
            "type": "complete",
            "content": full_text,
            "sources": sources,
            "stats": stats,
            "final_prompt": final_prompt
        }
