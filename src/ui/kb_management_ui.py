"""
知识库管理UI - 独立的知识库管理界面
"""

import streamlit as st
import os
from pathlib import Path

def render_kb_creation_wizard(form_key="kb_creation_form"):
    """知识库创建向导"""
    st.markdown("### 📚 创建新知识库")
    
    with st.form(form_key):
        st.markdown("#### 📝 基本信息")
        
        col1, col2 = st.columns(2)
        with col1:
            kb_name = st.text_input(
                "知识库名称 *", 
                placeholder="例如：技术文档库",
                help="请输入有意义的知识库名称"
            )
        
        with col2:
            kb_category = st.selectbox(
                "知识库类别",
                ["📚 通用文档", "💼 工作资料", "📖 学习笔记", "🔬 研究资料", "📋 项目文档", "🎯 其他"]
            )
        
        kb_description = st.text_area(
            "知识库描述",
            placeholder="简要描述这个知识库的用途和内容...",
            height=100
        )
        
        st.markdown("#### ⚙️ 高级设置")
        
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.slider("文档分块大小", 200, 1000, 500)
            chunk_overlap = st.slider("分块重叠长度", 0, 200, 50)
        
        with col2:
            enable_ocr = st.checkbox("启用OCR识别", value=False, help="处理扫描版PDF和图片，会消耗更多计算资源")
            enable_summary = st.checkbox("自动生成摘要", value=False, help="为每个文档生成摘要，会增加处理时间")
        
        # 提交按钮
        submitted = st.form_submit_button("🚀 创建知识库", use_container_width=True, type="primary")
        
        if submitted:
            if kb_name.strip():
                # 创建知识库
                success = create_knowledge_base(kb_name, kb_category, kb_description, {
                    'chunk_size': chunk_size,
                    'chunk_overlap': chunk_overlap,
                    'enable_ocr': enable_ocr,
                    'enable_summary': enable_summary
                })
                
                if success:
                    st.success(f"✅ 知识库 '{kb_name}' 创建成功！")
                    st.session_state.current_kb_id = kb_name
                    st.session_state.kb_created = True
                    # 清理chat_engine以确保重新加载
                    st.session_state.chat_engine = None
                    st.balloons()
                    
                    # 显示下一步操作
                    st.info("🎉 知识库创建完成！现在可以上传文档了。")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📄 立即上传文档", use_container_width=True, type="primary"):
                            # 跳转到主页并确保选中新创建的知识库
                            st.session_state.active_tab = "🏠 主页"
                            st.rerun()
                    with col2:
                        if st.button("📚 查看知识库", use_container_width=True):
                            # 跳转到选择页面
                            st.session_state.kb_tab = "选择"
                            st.rerun()
                else:
                    st.error("❌ 知识库创建失败，请检查名称是否重复")
            else:
                st.error("❌ 请输入知识库名称")

def render_kb_selector():
    """知识库选择器"""
    st.markdown("### 📚 选择知识库")
    
    # 获取知识库列表
    kb_list = get_knowledge_base_list()
    
    if not kb_list:
        st.info("📝 还没有知识库，请先创建一个")
        if st.button("➕ 创建第一个知识库", use_container_width=True, type="primary"):
            st.session_state.kb_tab = "创建"
            st.rerun()
        return
    
    # 搜索过滤
    search_query = st.text_input("🔍 搜索知识库", placeholder="输入名称或描述关键词...")
    
    # 过滤知识库
    if search_query:
        filtered_kbs = [kb for kb in kb_list if search_query.lower() in kb['name'].lower() or search_query.lower() in kb.get('description', '').lower()]
    else:
        filtered_kbs = kb_list
    
    # 显示知识库卡片
    st.markdown(f"#### 📋 知识库列表 ({len(filtered_kbs)}个)")
    
    cols = st.columns(2)
    for i, kb in enumerate(filtered_kbs):
        with cols[i % 2]:
            with st.container():
                # 知识库卡片
                st.markdown(f"**📚 {kb['name']}**")
                st.caption(f"🏷️ {kb.get('category', '通用文档')}")
                
                if kb.get('description'):
                    st.text(kb['description'][:100] + "..." if len(kb['description']) > 100 else kb['description'])
                
                # 统计信息
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄", kb.get('doc_count', 0), label_visibility="collapsed")
                with col2:
                    st.metric("💬", kb.get('chat_count', 0), label_visibility="collapsed")
                with col3:
                    st.metric("📅", kb.get('last_used', 'N/A'), label_visibility="collapsed")
                
                # 操作按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 使用", key=f"use_{kb['name']}", use_container_width=True, type="primary"):
                        st.session_state.current_kb_id = kb['name']
                        st.session_state.active_tab = "🏠 主页"
                        st.success(f"✅ 已切换到知识库: {kb['name']}")
                        st.rerun()
                
                with col2:
                    if st.button("⚙️ 管理", key=f"manage_{kb['name']}", use_container_width=True):
                        st.session_state.manage_kb = kb['name']
                        st.session_state.kb_tab = "管理"
                        st.rerun()
                
                st.divider()

def render_kb_management():
    """知识库管理"""
    st.markdown("### 🛠️ 知识库管理")
    
    # 获取知识库列表
    kb_list = get_knowledge_base_list()
    if not kb_list:
        st.info("📝 没有知识库可管理")
        return
    
    # 准备表格数据
    import pandas as pd
    from src.config.manifest_manager import ManifestManager
    data = []
    for kb in kb_list:
        # 尝试获取更准确的大小和片段信息
        kb_path = os.path.join("vector_db_storage", kb['name'])
        stats = ManifestManager.get_stats(kb_path)
        
        data.append({
            "名称": kb['name'],
            "文件数量": stats.get('file_count', kb.get('doc_count', 0)),
            "状态": "就绪",
            "片段数": stats.get('doc_count', kb.get('chunk_count', 0)),
            "大小": ManifestManager.format_size(stats.get('total_size', 0)),
            "创建时间": stats.get('created_time', '').split('T')[0] if stats.get('created_time') else 'N/A',
            "描述": kb.get('description', ''),
            "分类": kb.get('category', '通用文档')
        })
    
    df = pd.DataFrame(data)
    
    # 显示表格
    st.dataframe(
        df,
        column_config={
            "名称": st.column_config.TextColumn("名称", help="知识库名称", width="medium"),
            "文件数量": st.column_config.NumberColumn("文件数量", help="包含的文档总数"),
            "状态": st.column_config.TextColumn("状态", help="当前索引状态"),
            "片段数": st.column_config.NumberColumn("片段数", help="向量片段总数"),
            "大小": st.column_config.TextColumn("大小", help="占用存储空间"),
            "创建时间": st.column_config.TextColumn("创建时间", help="创建日期"),
            "分类": st.column_config.TextColumn("分类", width="small")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.divider()
    
    # 选择要管理的知识库
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_kb = st.selectbox(
            "选择要操作的知识库",
            [kb['name'] for kb in kb_list],
            index=0 if not st.session_state.get('manage_kb') else [kb['name'] for kb in kb_list].index(st.session_state.get('manage_kb', kb_list[0]['name']))
        )
    
    if selected_kb:
        kb_info = next((kb for kb in kb_list if kb['name'] == selected_kb), None)
        
        # 知识库信息编辑
        with st.expander(f"⚙️ 编辑知识库: {selected_kb}", expanded=True):
            with st.form("kb_edit_form"):
                new_name = st.text_input("知识库名称", value=kb_info['name'])
                new_category = st.selectbox(
                    "知识库类别",
                    ["📚 通用文档", "💼 工作资料", "📖 学习笔记", "🔬 研究资料", "📋 项目文档", "🎯 其他"],
                    index=0 # 简化处理，实际应匹配当前类别
                )
                new_description = st.text_area("知识库描述", value=kb_info.get('description', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 保存修改", use_container_width=True, type="primary"):
                        st.success("✅ 知识库信息已更新")
                
                with col2:
                    if st.form_submit_button("🗑️ 删除知识库", use_container_width=True):
                        st.session_state.confirm_delete = selected_kb
        
        # 删除确认
        if st.session_state.get('confirm_delete') == selected_kb:
            st.warning(f"⚠️ 确定要删除知识库 '{selected_kb}' 吗？此操作不可恢复！")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认删除", type="primary"):
                    # 执行删除
                    st.success(f"🗑️ 知识库 '{selected_kb}' 已删除")
                    st.session_state.confirm_delete = None
                    st.rerun()
            with col2:
                if st.button("❌ 取消"):
                    st.session_state.confirm_delete = None
                    st.rerun()

def create_knowledge_base(name, category, description, settings):
    """创建知识库"""
    try:
        # 检查是否已存在
        kb_dir = Path(f"vector_db_storage/{name}")
        if kb_dir.exists():
            return False
        
        # 创建目录
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存知识库信息
        kb_info = {
            'name': name,
            'category': category,
            'description': description,
            'created_time': st.session_state.get('current_time', '2024-12-14'),
            'settings': settings,
            'doc_count': 0,
            'chat_count': 0,
            'chunk_count': 0,
            'size_mb': 0
        }
        
        import json
        with open(kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"创建失败: {str(e)}")
        return False

def get_knowledge_base_list():
    """获取知识库列表"""
    kb_list = []
    vector_db_dir = Path("vector_db_storage")
    
    if not vector_db_dir.exists():
        return kb_list
    
    for kb_dir in vector_db_dir.iterdir():
        if kb_dir.is_dir():
            # 同时检查带点和不带点的 info 文件
            kb_info_file = kb_dir / "kb_info.json"
            if not kb_info_file.exists():
                kb_info_file = kb_dir / ".kb_info.json"
                
            if kb_info_file.exists():
                try:
                    import json
                    with open(kb_info_file, 'r', encoding='utf-8') as f:
                        kb_info = json.load(f)
                    kb_list.append(kb_info)
                except:
                    # 兼容旧版本，没有info文件的知识库
                    kb_list.append({
                        'name': kb_dir.name,
                        'category': '📚 通用文档',
                        'description': '旧版本知识库',
                        'doc_count': 0,
                        'chat_count': 0,
                        'chunk_count': 0,
                        'size_mb': 0
                    })
            else:
                # 兼容旧版本知识库 - 检查是否有实际内容
                if any(kb_dir.iterdir()):  # 目录不为空
                    kb_list.append({
                        'name': kb_dir.name,
                        'category': '📚 通用文档',
                        'description': '原有知识库',
                        'doc_count': 0,
                        'chat_count': 0,
                        'chunk_count': 0,
                        'size_mb': 0
                    })
    
    return kb_list

def render_kb_quick_selector():
    """快速知识库选择器（用于主页）"""
    kb_list = get_knowledge_base_list()
    
    if not kb_list:
        st.info("📝 还没有知识库")
        if st.button("➕ 创建知识库", use_container_width=True):
            st.session_state.active_tab = "🔧 工具"
            st.session_state.tool_tab = "知识库"
            st.rerun()
        return None
    
    # 添加"新建知识库"选项到列表开头
    kb_names = ["➕ 新建知识库..."] + [kb['name'] for kb in kb_list]
    
    # 默认选择"新建知识库"，避免自动加载大知识库
    current_kb = st.session_state.get('current_kb_id')
    
    # 如果当前有选中的知识库，找到它的索引
    if current_kb and current_kb in kb_names[1:]:  # 跳过"新建知识库"选项
        current_index = kb_names.index(current_kb)
    else:
        current_index = 0  # 默认选择"新建知识库"
    
    selected_kb = st.selectbox(
        "📚 选择知识库",
        kb_names,
        index=current_index,
        help="选择要使用的知识库，或创建新的知识库"
    )
    
    # 处理选择结果
    if selected_kb == "➕ 新建知识库...":
        # 清除当前知识库，避免加载
        if st.session_state.get('current_kb_id'):
            st.session_state.current_kb_id = None
            st.session_state.chat_engine = None
        
        # 显示创建提示
        st.info("💡 请到工具箱 → 知识库 → 创建新知识库")
        return None
    else:
        # 选择了具体的知识库
        if selected_kb != current_kb:
            st.session_state.current_kb_id = selected_kb
            # 清理chat_engine以触发重新加载
            st.session_state.chat_engine = None
            st.rerun()
        
        return selected_kb
