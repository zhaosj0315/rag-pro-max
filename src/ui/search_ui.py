"""
搜索UI组件
"""

import streamlit as st
from src.utils.search_engine import search_engine

def render_search_interface():
    """渲染搜索界面"""
    st.markdown("###### 🔍 智能搜索")
    
    # 搜索输入框
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_query = st.text_input(
            "搜索内容", 
            placeholder="输入关键词搜索文档内容...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_clicked = st.button("🔍 搜索", use_container_width=True, type="primary")
    
    # 搜索建议
    if search_query and len(search_query) > 1:
        suggestions = search_engine.get_search_suggestions(search_query)
        if suggestions:
            st.markdown("💡 **搜索建议:**")
            for suggestion in suggestions:
                if st.button(f"📝 {suggestion}", key=f"suggest_{suggestion}"):
                    st.session_state.search_query = suggestion
                    st.rerun()
    
    # 高级过滤器
    with st.expander("🎛️ 高级过滤", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 文件类型过滤
            file_types = st.multiselect(
                "📄 文件类型",
                ["PDF", "DOCX", "TXT", "MD", "XLSX", "PPTX"],
                help="选择要搜索的文件类型"
            )
            
            # 日期范围
            date_range = st.date_input(
                "📅 日期范围",
                value=(),
                help="选择文档的日期范围"
            )
        
        with col2:
            # 标签过滤
            available_tags = search_engine.get_all_tags()
            selected_tags = st.multiselect(
                "🏷️ 标签",
                available_tags,
                help="按标签过滤文档"
            )
            
            # 排序方式
            sort_by = st.selectbox(
                "📊 排序方式",
                ["relevance", "date", "size", "name"],
                format_func=lambda x: {
                    "relevance": "🎯 相关性",
                    "date": "📅 日期",
                    "size": "📏 大小", 
                    "name": "📝 名称"
                }[x]
            )
    
    # 执行搜索
    if search_clicked or search_query:
        # 获取当前知识库中的真实文档
        kb_name = st.session_state.get('kb_selected')
        if not kb_name:
            st.warning("请先选择知识库")
            return
            
        kb_path = os.path.join("vector_db_storage", kb_name)
        from src.config.manifest_manager import ManifestManager
        manifest = ManifestManager.load(kb_path)
        real_files = manifest.get('files', [])
        
        # 转换为搜索引擎需要的格式
        documents = []
        for i, f in enumerate(real_files):
            documents.append({
                'id': f.get('id', str(i)),
                'filename': f.get('filename', 'Unknown'),
                'title': f.get('title', f.get('filename', 'Unknown')),
                'content': f.get('summary', '') or f.get('filename', ''),
                'file_type': f.get('type', 'Unknown'),
                'size': f.get('size_bytes', 0),
                'date': f.get('added_at', ''),
                'tags': f.get('tags', [])
            })
        
        # 应用搜索和过滤
        results = documents
        
        if search_query:
            results = search_engine.full_text_search(search_query, results)
        
        if file_types:
            results = search_engine.filter_by_file_type(results, file_types)
        
        if selected_tags:
            results = search_engine.filter_by_tags(results, selected_tags)
        
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            results = search_engine.filter_by_date_range(
                results, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
        
        results = search_engine.sort_results(results, sort_by)
        
        # 显示搜索结果
        st.markdown(f"#### 📋 搜索结果 ({len(results)} 个)")
        
        if results:
            for i, doc in enumerate(results):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**📄 {doc['filename']}**")
                        if 'matches' in doc and doc['matches']:
                            for match in doc['matches'][:1]:  # 只显示第一个匹配
                                st.markdown(f"💬 {match['snippet']}")
                        else:
                            # 显示内容摘要
                            content_preview = doc['content'][:100] + "..." if len(doc['content']) > 100 else doc['content']
                            st.markdown(f"💬 {content_preview}")
                    
                    with col2:
                        st.markdown(f"📅 {doc['date']}")
                        st.markdown(f"📏 {doc['size']/1024:.0f}KB")
                    
                    with col3:
                        if 'search_score' in doc:
                            st.markdown(f"🎯 相关性: {doc['search_score']}")
                        
                        # 标签显示
                        if doc.get('tags'):
                            tags_str = " ".join([f"`{tag}`" for tag in doc['tags'][:3]])
                            st.markdown(f"🏷️ {tags_str}")
                    
                    st.divider()
        else:
            st.info("🔍 没有找到匹配的文档，请尝试其他关键词")

def render_tag_management():
    """渲染标签管理界面"""
    st.markdown("##### 🏷️ 标签管理")
    
    # 添加新标签
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_tag = st.text_input("新标签", placeholder="输入标签名称...", label_visibility="collapsed")
    
    with col2:
        if st.button("➕ 添加", use_container_width=True):
            if new_tag.strip():
                search_engine.add_tag_to_document("", new_tag.strip())
                st.success(f"✅ 已添加标签: {new_tag}")
                st.rerun()
    
    # 显示现有标签
    all_tags = search_engine.get_all_tags()
    if all_tags:
        st.markdown("###### 📋 现有标签")
        
        # 分列显示标签
        cols = st.columns(3)
        for i, tag in enumerate(all_tags):
            with cols[i % 3]:
                st.markdown(f"🏷️ `{tag}`")
    else:
        st.info("📝 还没有标签，请添加一些标签来组织文档")

def render_search_analytics():
    """渲染搜索分析界面"""
    st.markdown("##### 📊 搜索分析")
    
    # 搜索历史
    search_history = search_engine.search_history
    if search_history:
        st.markdown("###### 🕒 最近搜索")
        for i, query in enumerate(reversed(search_history[-5:])):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🔍 {query}")
            with col2:
                if st.button("🔄", key=f"repeat_{i}", help="重复搜索"):
                    st.session_state.search_query = query
                    st.rerun()
    else:
        st.info("📝 还没有搜索记录")
    
    # 搜索统计
    st.markdown("###### 📈 搜索统计")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔍 总搜索次数", len(search_history))
    
    with col2:
        unique_queries = len(set(search_history)) if search_history else 0
        st.metric("💡 不同查询", unique_queries)
    
    with col3:
        avg_query_length = sum(len(q) for q in search_history) / len(search_history) if search_history else 0
        st.metric("📏 平均查询长度", f"{avg_query_length:.1f}字符")
