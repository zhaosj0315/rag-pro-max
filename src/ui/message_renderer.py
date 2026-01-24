from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
消息渲染模块
负责聊天消息的显示、引用处理和推荐问题渲染
"""

import streamlit as st
import hashlib
from src.ui.display_components import render_message_stats, render_source_references
from src.chat_utils_improved import generate_follow_up_questions_safe as generate_follow_up_questions


class MessageRenderer:
    """消息渲染器"""
    
    @staticmethod
    def render_messages(messages, active_kb_name, chat_engine):
        """渲染所有消息"""
        for msg_idx, msg in enumerate(messages):
            role = msg["role"]
            avatar = "🤖" if role == "assistant" else "🧑💻"
            
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg["content"])
                
                # 显示统计信息
                if "stats" in msg and msg["stats"]:
                    render_message_stats(msg["stats"])
                
                # 渲染引用源
                if "sources" in msg:
                    render_source_references(msg["sources"], expanded=False)
                
                # 引用按钮
                if role == "assistant":
                    if st.button("📌 引用此回复", key=f"quote_{msg_idx}"):
                        st.session_state.quote_content = msg["content"]
                        st.rerun()
                
                # 渲染静态建议（仅用于自动摘要）
                MessageRenderer._render_static_suggestions(msg, msg_idx, messages)
            
            # 在最后一条 assistant 消息之后显示动态追问推荐
            MessageRenderer._render_dynamic_suggestions(msg, msg_idx, messages, active_kb_name, chat_engine)
    
    @staticmethod
    def _render_static_suggestions(msg, msg_idx, messages):
        """渲染静态建议"""
        is_last_message = msg_idx == len(messages) - 1
        if ("suggestions" in msg and msg["suggestions"] and 
            is_last_message and not st.session_state.suggestions_history):
            
            st.write("")
            for idx, q in enumerate(msg["suggestions"]):
                if st.button(f"👉 {q}", key=f"sug_{msg_idx}_{idx}", use_container_width=True):
                    MessageRenderer._click_suggestion(q)
    
    @staticmethod
    def _render_dynamic_suggestions(msg, msg_idx, messages, active_kb_name, chat_engine):
        """渲染动态追问推荐"""
        is_last_message = msg_idx == len(messages) - 1
        if (is_last_message and msg["role"] == "assistant" and 
            active_kb_name and chat_engine):
            
            msg_hash = hashlib.md5(msg['content'][:100].encode()).hexdigest()[:8]
            st.divider()
            
            # @st.fragment [Fix] 移除 Fragment 隔离，使点击事件触发全局 Rerun (Button 默认行为)，利用自然流处理队列
            def suggestions_fragment():
                # 优先显示当前推荐，如果没有则显示历史推荐
                display_suggestions = (
                    st.session_state.get('current_suggestions', []) or 
                    st.session_state.get('suggestions_history', [])
                )
                
                if display_suggestions:
                    st.markdown("###### 🚀 追问推荐")
                    for idx, q in enumerate(display_suggestions[:3]):  # 只显示3个
                        if st.button(f"👉 {q}", key=f"dyn_sug_{msg_hash}_{idx}", use_container_width=True):
                            MessageRenderer._click_suggestion(q)
                
                if st.button("✨ 继续推荐 3 个追问", key=f"gen_more_{msg_hash}", 
                           type="secondary", use_container_width=True):
                    MessageRenderer._generate_more_suggestions(msg, chat_engine)
            
            suggestions_fragment()
    
    @staticmethod
    def _click_suggestion(question):
        """点击建议问题"""
        from src.queue.queue_manager import QueueManager
        queue_manager = QueueManager()
        queue_manager.add_question(question)
        # st.rerun() [Fix] 移除强制重跑，避免白屏闪烁
    
    @staticmethod
    def _generate_more_suggestions(msg, chat_engine):
        """生成更多建议"""
        with st.spinner("⏳ 正在生成新问题..."):
            # 收集所有历史问题，确保不重复
            all_history_questions = []
            
            # 1. 用户问过的所有问题
            user_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
            all_history_questions.extend(user_questions)
            
            # 2. 所有历史推荐问题（包括已点击的）
            if hasattr(st.session_state, 'suggestions_history'):
                all_history_questions.extend(st.session_state.suggestions_history)
            
            # 3. 队列中的问题
            if hasattr(st.session_state, 'question_queue'):
                all_history_questions.extend(st.session_state.question_queue)
            
            # 4. 当前显示的推荐问题
            if hasattr(st.session_state, 'current_suggestions'):
                all_history_questions.extend(st.session_state.current_suggestions)
            
            # 去重
            all_history_questions = list(set(all_history_questions))
            
            new_sugs = generate_follow_up_questions(
                context_text=msg['content'],
                num_questions=3,
                existing_questions=all_history_questions,
                query_engine=chat_engine
            )
            
            if new_sugs:
                # 更新历史记录（累积，不覆盖）
                if not hasattr(st.session_state, 'suggestions_history'):
                    st.session_state.suggestions_history = []
                
                # 过滤重复问题
                new_suggestions = []
                for sugg in new_sugs:
                    if sugg not in st.session_state.suggestions_history:
                        new_suggestions.append(sugg)
                
                st.session_state.suggestions_history.extend(new_suggestions)
                
                # 更新当前显示的推荐
                st.session_state.current_suggestions = new_suggestions[:3] if new_suggestions else new_sugs[:3]
                
                # 详细日志记录
                logger.info(f"🔄 MessageRenderer生成 {len(new_suggestions)} 个新推荐问题")
                if new_suggestions:
                    for i, q in enumerate(new_suggestions[:3], 1):
                        logger.info(f"   {i}. {q}")
                
                st.rerun(scope="fragment")
            else:
                st.warning("未能生成更多追问，请尝试输入新问题。")
    
    @staticmethod
    def render_quote_preview():
        """渲染引用内容预览"""
        if st.session_state.get("quote_content"):
            quote_text = st.session_state.quote_content
            display_text = quote_text[:60].replace('\n', ' ') + "..." if len(quote_text) > 60 else quote_text
            
            with st.container():
                st.info(f"📌 **已引用**: {display_text}")
                col1, col2 = st.columns([8, 2])
                col1.caption("基于此内容提问...")
                if col2.button("取消引用", key="cancel_quote", use_container_width=True):
                    st.session_state.quote_content = None
                    st.rerun()
