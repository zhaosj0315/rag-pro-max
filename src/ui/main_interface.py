"""
主界面组件管理器
提取自 apppro.py 的UI逻辑
"""

import streamlit as st
import time
from typing import Optional

from src.logging import LogManager
from src.query.query_handler import QueryHandler
from src.chat import HistoryManager, SuggestionManager
from src.chat_utils_improved import generate_follow_up_questions_safe as generate_follow_up_questions


class MainInterface:
    """主界面管理器"""
    
    def __init__(self):
        self.logger = LogManager()
        self.query_handler = QueryHandler()
    
    def handle_kb_loading(self, active_kb_name: str, output_base: str, 
                         embed_provider: str, embed_model: str, 
                         embed_key: str, embed_url: str) -> bool:
        """处理知识库加载"""
        if active_kb_name and active_kb_name != st.session_state.current_kb_id:
            # 只在没有正在处理的问题时才切换
            if not st.session_state.get('is_processing', False):
                st.session_state.current_kb_id = active_kb_name
                st.session_state.chat_engine = None
                with st.spinner("📜 正在加载对话历史..."):
                    st.session_state.messages = HistoryManager.load(active_kb_name)
                st.session_state.suggestions_history = []
                return True
            else:
                st.warning("⚠️ 正在处理问题，请等待完成后再切换知识库")
                # 恢复之前的选择
                st.session_state.current_nav = f"📂 {st.session_state.current_kb_id}"
                return False
        
        # 加载知识库引擎
        if active_kb_name and st.session_state.chat_engine is None:
            return self.query_handler.load_knowledge_base(
                active_kb_name, output_base, embed_provider, 
                embed_model, embed_key, embed_url
            )
        
        return True
    
    def render_chat_messages(self, messages: list, active_kb_name: str):
        """渲染聊天消息"""
        def click_btn(q):
            """点击追问按钮，将问题加入队列（去重）"""
            if st.session_state.chat_engine:
                # 检查队列中是否已存在相同问题
                if q not in st.session_state.question_queue:
                    st.session_state.question_queue.append(q)
                else:
                    st.toast("⚠️ 该问题已在队列中")
            st.rerun()
        
        for msg_idx, msg in enumerate(messages):
            role = msg["role"]
            avatar = "🤖" if role == "assistant" else "🧑💻"
            
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg["content"])
                
                # 显示来源
                if role == "assistant" and "sources" in msg:
                    self._render_sources(msg["sources"])
                
                # 显示统计信息
                if role == "assistant" and "stats" in msg:
                    self._render_stats(msg["stats"])
                
                # 引用按钮
                if role == "assistant":
                    if st.button("📌 引用此回复", key=f"quote_{msg_idx}", use_container_width=True):
                        st.session_state.quote_content = msg["content"]
                        st.rerun()
                
                # 渲染静态建议
                is_last_message = msg_idx == len(messages) - 1
                if ("suggestions" in msg and msg["suggestions"] and 
                    is_last_message and not st.session_state.suggestions_history):
                    st.write("")
                    for idx, q in enumerate(msg["suggestions"]):
                        if st.button(f"👉 {q}", key=f"sug_{msg_idx}_{idx}", use_container_width=True):
                            click_btn(q)
            
            # 在最后一条 assistant 消息之后显示动态追问推荐
            if (is_last_message and msg["role"] == "assistant" and 
                active_kb_name and st.session_state.chat_engine):
                self._render_dynamic_suggestions(msg, click_btn)
    
    def process_user_input(self, user_input: str, active_kb_name: str,
                          llm_provider: str, llm_model: str, llm_key: str, 
                          llm_url: str, temperature: float = 0.7):
        """处理用户输入"""
        # 检查重复查询（最近3次）
        recent_queries = [m['content'] for m in st.session_state.messages[-6:] if m['role'] == 'user']
        if user_input in recent_queries:
            st.info("💡 您刚才已经问过相同的问题，可以查看上面的回答或尝试换个角度提问")
            st.stop()
        
        self.logger.log("INFO", f"用户提问: {user_input}", stage="查询对话", 
                       details={"kb_name": active_kb_name})
        
        st.session_state.messages.append({"role": "user", "content": user_input})
        if active_kb_name: 
            HistoryManager.save(active_kb_name, st.session_state.messages)
        
        with st.chat_message("user", avatar="🧑💻"): 
            st.markdown(user_input)
        
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            full_text = ""
            sources = []
            stats = {}
            
            try:
                # 处理查询
                for result in self.query_handler.process_question(
                    user_input, llm_provider, llm_model, llm_key, llm_url, temperature
                ):
                    if result['type'] == 'token':
                        full_text += result['content']
                        message_placeholder.markdown(full_text + "▌")
                    elif result['type'] == 'complete':
                        full_text = result['content']
                        sources = result['sources']
                        stats = result['stats']
                        message_placeholder.markdown(full_text)
                        break
                    elif result['type'] == 'error':
                        st.error(f"❌ 查询失败: {result['content']}")
                        return
                
                # 显示来源和统计
                if sources:
                    self._render_sources(sources)
                if stats:
                    self._render_stats(stats)
                
                # 保存消息
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_text, 
                    "sources": sources,
                    "stats": stats
                })
                
                if active_kb_name:
                    HistoryManager.save(active_kb_name, st.session_state.messages)
                
                # 生成推荐问题
                self._generate_suggestions(full_text, active_kb_name)
                
            except Exception as e:
                st.error(f"❌ 处理失败: {str(e)}")
                self.logger.error(f"❌ 用户输入处理失败: {str(e)}")
    
    def _render_sources(self, sources: list):
        """渲染来源信息"""
        if sources:
            with st.expander("📚 参考 3 个片段", expanded=False):
                for i, source in enumerate(sources[:3], 1):
                    st.caption(f"**片段 {i}**: {source.get('file_name', '未知文件')}")
                    st.text(source.get('content', ''))
    
    def _render_stats(self, stats: dict):
        """渲染统计信息"""
        elapsed = stats.get('elapsed_time', 0)
        source_count = stats.get('source_count', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"⏱️ {elapsed:.1f}s")
        with col2:
            st.caption(f"📄 {source_count} 字符")
    
    def _render_dynamic_suggestions(self, msg: dict, click_btn_func):
        """渲染动态推荐问题"""
        import hashlib
        msg_hash = hashlib.md5(msg['content'][:100].encode()).hexdigest()[:8]
        
        st.divider()
        
        @st.fragment
        def suggestions_fragment():
            # 优先显示当前推荐，如果没有则显示历史推荐
            display_suggestions = (
                st.session_state.get('current_suggestions', []) or 
                st.session_state.get('suggestions_history', [])
            )
            
            if display_suggestions:
                st.markdown("##### 🚀 追问推荐")
                for idx, q in enumerate(display_suggestions[:3]):  # 只显示3个
                    if st.button(f"👉 {q}", key=f"dyn_sug_{msg_hash}_{idx}", use_container_width=True):
                        click_btn_func(q)
            
            if st.button("✨ 继续推荐 3 个追问 (无限追问)", key=f"gen_more_{msg_hash}", 
                        type="secondary", use_container_width=True):
                with st.spinner("⏳ 正在生成新问题..."):
                    self._generate_more_suggestions(msg['content'])
        
        suggestions_fragment()
    
    def _generate_suggestions(self, context_text: str, active_kb_name: str):
        """生成初始推荐问题"""
        try:
            existing_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
            existing_questions.extend(st.session_state.question_queue)
            existing_questions.extend(st.session_state.suggestions_history)
            
            initial_sugs = generate_follow_up_questions(
                context_text, 
                num_questions=3,
                existing_questions=existing_questions,
                query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None
            )
            
            if initial_sugs:
                # 累积历史推荐，避免重复
                if not hasattr(st.session_state, 'suggestions_history'):
                    st.session_state.suggestions_history = []
                
                # 过滤掉已存在的推荐
                new_suggestions = []
                for sugg in initial_sugs[:3]:
                    if sugg not in st.session_state.suggestions_history:
                        new_suggestions.append(sugg)
                
                # 添加到历史记录
                st.session_state.suggestions_history.extend(new_suggestions)
                
                # 设置当前显示的推荐（最新的3个）
                st.session_state.current_suggestions = new_suggestions[:3] if new_suggestions else initial_sugs[:3]
                
                # 详细日志记录
                self.logger.info(f"✨ 生成 {len(new_suggestions)} 个新推荐问题")
                if new_suggestions:
                    for i, q in enumerate(new_suggestions[:3], 1):
                        self.logger.info(f"   {i}. {q}")
                else:
                    self.logger.info("⚠️ 未生成新推荐，使用原始推荐")
            else:
                self.logger.info("⚠️ 推荐问题生成失败")
                
        except Exception as e:
            self.logger.error(f"❌ 推荐问题生成异常: {str(e)}")
    
    def _generate_more_suggestions(self, context_text: str):
        """生成更多推荐问题"""
        try:
            # 收集所有历史问题，确保不重复
            all_history_questions = []
            
            # 1. 用户问过的所有问题
            user_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
            all_history_questions.extend(user_questions)
            
            # 2. 所有历史推荐问题
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
                context_text=context_text, 
                num_questions=3,
                existing_questions=all_history_questions,
                query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None
            )
            
            if new_sugs:
                # 累积历史推荐，避免重复
                if not hasattr(st.session_state, 'suggestions_history'):
                    st.session_state.suggestions_history = []
                
                # 过滤掉已存在的推荐
                new_suggestions = []
                for sugg in new_sugs:
                    if sugg not in st.session_state.suggestions_history:
                        new_suggestions.append(sugg)
                
                # 添加到历史记录
                st.session_state.suggestions_history.extend(new_suggestions)
                
                # 设置当前显示的推荐
                st.session_state.current_suggestions = new_suggestions[:3] if new_suggestions else new_sugs[:3]
                
                # 详细日志记录
                self.logger.info(f"🔄 继续生成 {len(new_suggestions)} 个新推荐问题")
                if new_suggestions:
                    for i, q in enumerate(new_suggestions[:3], 1):
                        self.logger.info(f"   {i}. {q}")
                else:
                    self.logger.info("⚠️ 未生成新推荐，可能已达到问题库上限")
                
                st.rerun(scope="fragment")
            else:
                st.warning("未能生成更多追问，请尝试输入新问题。")
                
        except Exception as e:
            self.logger.error(f"❌ 更多推荐问题生成失败: {str(e)}")
            st.error("生成推荐问题时出错，请稍后再试。")
