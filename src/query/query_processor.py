"""
查询处理器模块
负责处理用户查询、流式响应和结果处理
"""

import os
import re
import time
import streamlit as st
from llama_index.core import Settings

from src.app_logging import LogManager
from src.chat import HistoryManager
from src.chat_utils_improved import generate_follow_up_questions_safe as generate_follow_up_questions
from src.utils.memory import cleanup_memory
from src.utils.model_manager import load_embedding_model
from src.utils.enhanced_cache import smart_cache_manager

logger = LogManager()


def process_node_worker(args):
    """处理单个节点的工作函数"""
    node_data, active_kb_name = args
    
    try:
        metadata = node_data.get('metadata', {})
        score = node_data.get('score', 0.0)
        text = node_data.get('text', '')
        
        # 提取文件名
        file_name = metadata.get('file_name', 'Unknown')
        if not file_name or file_name == 'Unknown':
            file_name = metadata.get('filename', 'Unknown')
        
        # 清理文本
        clean_text = text.replace('\n', ' ').strip()
        if len(clean_text) > 150:
            clean_text = clean_text[:150] + "..."
        
        return {
            'file_name': file_name,
            'score': score,
            'text': clean_text,
            'metadata': metadata
        }
    except Exception as e:
        logger.warning(f"处理节点失败: {e}")
        return None


class QueryProcessor:
    """查询处理器"""
    
    def __init__(self):
        self.executor = ParallelExecutor()
    
    @smart_cache_manager.cached_query
    def process_query(self, query, chat_engine, active_kb_name, embed_provider, embed_model, embed_key, embed_url):
        """处理查询并返回结果"""
        try:
            logger.separator("知识库查询")
            logger.start_operation("查询", f"知识库: {active_kb_name}")
            logger.log("INFO", f"用户提问: {query}", stage="查询对话", details={"kb_name": active_kb_name})
            
            # 开始计时
            start_time = time.time()
            
            # 显示启用的检索增强功能
            enhancements = []
            if st.session_state.get('enable_bm25', False):
                enhancements.append("BM25混合检索")
            if st.session_state.get('enable_rerank', False):
                enhancements.append("Re-ranking重排序")
            
            if enhancements:
                enhancement_str = " + ".join(enhancements)
                logger.info(f"🎯 检索增强: {enhancement_str}")
            
            with logger.timer("检索相关文档"):
                logger.log("INFO", "开始检索相关文档", stage="查询对话", details={"kb_name": active_kb_name})
                
                # 确保 embedding 模型已设置
                embed = load_embedding_model(embed_provider, embed_model, embed_key, embed_url)
                if embed:
                    Settings.embed_model = embed
                
                # GPU加速检索 - 添加超时控制
                retrieval_start = time.time()
                
                try:
                    # 设置较短的超时时间
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("检索超时")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)  # 30秒超时
                    
                    response = chat_engine.stream_chat(query)
                    signal.alarm(0)  # 取消超时
                    
                except TimeoutError:
                    logger.error("⏰ 检索超时 (30s)，请尝试简化查询")
                    yield {"type": "error", "content": "检索超时，请尝试简化查询或稍后重试"}
                    return
                except Exception as e:
                    signal.alarm(0)  # 确保取消超时
                    raise e
                retrieval_time = time.time() - retrieval_start
                
                logger.info(f"🔍 检索耗时: {retrieval_time:.2f}s (GPU加速)")
                
                # 流式输出处理
                full_text = ""
                for token in response.response_gen:
                    full_text += token
                    yield {"type": "token", "content": token, "full_text": full_text}
                
                # 处理完成
                yield {"type": "complete", "content": full_text, "response": response, "start_time": start_time}
                
        except Exception as e:
            logger.error(f"查询处理失败: {e}")
            yield {"type": "error", "content": str(e)}
    
    def process_response_complete(self, full_text, response, start_time, active_kb_name, llm_model):
        """处理响应完成后的逻辑"""
        try:
            # 提取 token 统计
            prompt_tokens = 0
            completion_tokens = 0
            
            if hasattr(response, 'raw') and response.raw:
                usage = response.raw.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
            
            # 如果没有真实 Usage，则进行估算
            if completion_tokens == 0:
                total_chars = len(full_text)
                chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', full_text))
                completion_tokens = int((chinese_chars * 1.5) + ((total_chars - chinese_chars) * 0.3))
            
            # 处理源节点
            srcs = []
            if response.source_nodes:
                logger.log("INFO", f"检索完成，找到 {len(response.source_nodes)} 个相关文档", 
                          stage="查询对话", details={"kb_name": active_kb_name})
                
                # 提取节点数据
                node_data = []
                for node in response.source_nodes:
                    text = self._extract_node_text(node)
                    node_data.append({
                        'metadata': getattr(node, 'metadata', {}),
                        'score': getattr(node, 'score', 0.0),
                        'text': text
                    })
                
                # 并行处理节点（优化阈值）
                tasks = [(d, active_kb_name) for d in node_data]
                # 降低并行阈值：2个节点就并行，充分利用多核
                parallel_threshold = 2
                srcs = [s for s in self.executor.execute(process_node_worker, tasks, threshold=parallel_threshold) if s]
                
                if len(node_data) >= parallel_threshold:
                    logger.info(f"⚡ 并行处理: {len(srcs)} 个节点 (阈值: {parallel_threshold})")
                else:
                    logger.info(f"⚡ 单节点处理: {len(srcs)} 个节点")
            
            # 计算统计信息
            total_time = time.time() - start_time
            tokens_per_sec = completion_tokens / total_time if total_time > 0 else 0
            
            stats = {
                "time": total_time,
                "tokens": completion_tokens,
                "tokens_per_sec": tokens_per_sec,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
            
            logger.log("SUCCESS", "回答生成完成", stage="查询对话", 
                      details={"kb_name": active_kb_name, "model": llm_model, 
                              "tokens": completion_tokens, "prompt_tokens": prompt_tokens, 
                              "completion_tokens": completion_tokens})
            logger.complete_operation(f"查询完成 (耗时 {total_time:.2f}s)")
            
            return {
                "sources": srcs,
                "stats": stats,
                "full_text": full_text
            }
            
        except Exception as e:
            logger.error(f"响应处理失败: {e}")
            return {"sources": [], "stats": {}, "full_text": full_text}
    
    def generate_suggestions(self, full_text, existing_questions, chat_engine):
        """生成追问建议"""
        try:
            # 尝试从chat_engine获取LLM
            llm_model = None
            if chat_engine and hasattr(chat_engine, '_llm'):
                llm_model = chat_engine._llm
            elif chat_engine and hasattr(chat_engine, 'llm'):
                llm_model = chat_engine.llm
            
            initial_sugs = generate_follow_up_questions(
                full_text,
                num_questions=3,
                existing_questions=existing_questions,
                query_engine=chat_engine if chat_engine else None,
                llm_model=llm_model
            )
            
            if initial_sugs:
                logger.info(f"✨ 生成 {len(initial_sugs)} 个新推荐问题")
                # 详细记录每个推荐问题
                for i, q in enumerate(initial_sugs[:3], 1):
                    logger.info(f"   {i}. {q}")
                return initial_sugs[:3]
            else:
                logger.info("⚠️ 推荐问题生成失败")
                return []
                
        except Exception as e:
            logger.error(f"推荐问题生成失败: {e}")
            return []
    
    def save_message_and_cleanup(self, active_kb_name, messages):
        """保存消息并清理内存"""
        try:
            if active_kb_name:
                HistoryManager.save(active_kb_name, messages)
            cleanup_memory()
            logger.info("🧹 对话完成，内存已清理")
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
    
    def _extract_node_text(self, node):
        """提取节点文本"""
        try:
            if hasattr(node, 'get_text'):
                return node.get_text()
            elif hasattr(node, 'text'):
                return node.text
            elif hasattr(node, 'node') and hasattr(node.node, 'text'):
                return node.node.text
            else:
                return str(node)[:150]
        except:
            return str(node)[:150]
    
    def check_duplicate_query(self, query, messages):
        """检查重复查询 - 使用智能相似度检测"""
        from src.chat_utils_improved import _is_similar_question
        
        # 获取最近的用户问题
        recent_queries = [m['content'] for m in messages[-6:] if m['role'] == 'user']
        
        # 使用智能相似度检测，降低阈值以捕获更多相似问题
        for recent_query in recent_queries:
            if _is_similar_question(query, recent_query, threshold=0.6):  # 降低阈值
                return True
        
        return False
    
    def prepare_quoted_query(self, query, quote_content):
        """准备包含引用的查询"""
        if quote_content:
            # 限制引用长度
            if len(quote_content) > 2000:
                quote_content = quote_content[:2000] + "...(已截断)"
            
            return f"基于以下引用内容：\n> {quote_content}\n\n我的问题是：{query}"
        return query
