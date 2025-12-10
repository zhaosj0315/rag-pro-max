"""
自动摘要模块
负责知识库首次加载时的自动摘要生成
"""

import re
import streamlit as st
from llama_index.core import Settings
from src.logging import LogManager
from src.chat import HistoryManager

logger = LogManager()


class AutoSummaryGenerator:
    """自动摘要生成器"""
    
    @staticmethod
    def should_generate_summary(active_kb_name, chat_engine, messages):
        """判断是否应该生成自动摘要"""
        return (active_kb_name and 
                chat_engine and 
                not messages)
    
    @staticmethod
    def generate_summary(active_kb_name, chat_engine):
        """生成知识库自动摘要"""
        with st.chat_message("assistant", avatar="🤖"):
            summary_placeholder = st.empty()
            
            with st.status("✨ 正在分析文档生成摘要...", expanded=True):
                try:
                    # 使用知识库的模型
                    current_model = getattr(Settings.embed_model, '_model_name', 'Unknown')
                    logger.info(f"💬 摘要生成使用模型: {current_model}")
                    
                    prompt = "请用一段话简要总结此知识库的核心内容。然后，提出3个用户可能最关心的问题，每行一个，不要序号。"
                    full = ""
                    resp = chat_engine.stream_chat(prompt)
                    
                    # 流式输出摘要
                    for t in resp.response_gen:
                        full += t
                        summary_placeholder.markdown(full + "▌")
                    
                    summary_placeholder.markdown(full)
                    
                    # 解析摘要和建议问题
                    summary_lines = full.split('\n')
                    summary = summary_lines[0]
                    suggestions = [
                        re.sub(r'^\d+\.\s*', '', q.strip()) 
                        for q in summary_lines[1:] 
                        if q.strip()
                    ][:3]
                    
                    # 保存到消息历史
                    message = {
                        "role": "assistant", 
                        "content": summary, 
                        "suggestions": suggestions
                    }
                    st.session_state.messages.append(message)
                    HistoryManager.save(active_kb_name, st.session_state.messages)
                    
                    st.rerun()
                    
                except Exception as e:
                    error_msg = str(e)
                    if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                        summary_placeholder.info("⏱️ LLM 响应超时，已跳过自动摘要。您可以直接开始提问。")
                        logger.warning(f"⏱️ 摘要生成超时: {e}")
                    else:
                        summary_placeholder.warning(f"摘要生成受阻: {e}")
                        logger.error(f"❌ 摘要生成失败: {e}")
                    
                    # 添加默认消息
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "👋 知识库已就绪。"
                    })
