import streamlit as st
import os
import time
import shutil
from datetime import datetime
from src.app_logging import LogManager
from src.common.utils import save_uploaded_files
from src.utils.file_system_utils import reveal_in_file_manager

logger = LogManager()

def sync_to_staging(target_dir, source, is_file=True, source_label="Unknown"):
    """
    同步文件或目录到暂存区
    """
    count = 0
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        if is_file:
            # 单文件模式
            fname = os.path.basename(source)
            dest = os.path.join(target_dir, fname)
            shutil.copy2(source, dest)
            count = 1
        else:
            # 目录/批量模式
            if os.path.isdir(source):
                # 如果是目录，递归拷贝所有文件
                for root, dirs, files in os.walk(source):
                    for file in files:
                        # 过滤隐藏文件
                        if file.startswith('.'): continue
                        
                        src_file = os.path.join(root, file)
                        # 扁平化存储，防止目录结构导致索引问题
                        # 如果有重名，添加时间戳前缀
                        dest_file = os.path.join(target_dir, file)
                        if os.path.exists(dest_file):
                            dest_file = os.path.join(target_dir, f"{int(time.time())}_{file}")
                        
                        shutil.copy2(src_file, dest_file)
                        
                        # 写入元数据
                        with open(dest_file + ".meta", "w", encoding="utf-8") as meta_f:
                            meta_f.write(f"Source: {source_label}\n")
                            meta_f.write(f"OriginalPath: {src_file}\n")
                            meta_f.write(f"SyncTime: {datetime.now().isoformat()}\n")
                        count += 1
        return count
    except Exception as e:
        st.error(f"同步失败: {e}")
        logger.error(f"Sync failed: {e}")
        return 0

def handle_ingestion_success(source_name, count, details=""):
    st.toast(f"✅ [{source_name}] 已成功摄入 {count} 个文件")
    logger.info(f"Ingestion Success [{source_name}]: {count} files. {details}")

def render_staging_area(target_dir, key_prefix="omni"):
    """
    渲染暂存区状态栏 (显示文件数、打开文件夹、刷新、清空)
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    files_in_staging = os.listdir(target_dir)
    staging_count = len([f for f in files_in_staging if not f.startswith('.') and not f.endswith('.meta')])
    
    stat_col1, stat_col_icon, stat_col_open, stat_col_refresh, stat_col2 = st.columns([2.8, 0.4, 0.4, 0.4, 0.4])
    
    with stat_col1:
        stats_placeholder = st.empty()
        stats_placeholder.markdown(
            f"""<div style='display: flex; align-items: center; gap: 8px;'>
                <span style='font-weight: 600; color: #1f77b4;'>📦 待处理暂存区:</span>
                <span style='background: #e1f5fe; color: #01579b; padding: 2px 10px; border-radius: 12px; font-weight: bold; font-family: monospace;'>{staging_count}</span>
                <span style='color: #666; font-size: 0.85rem;'>个文件已就绪</span>
            </div>""", unsafe_allow_html=True
        )
    
    with stat_col_icon:
        with st.popover("📂", help="查看暂存区详情"):
            if files_in_staging:
                # 深度分类与追踪展现
                grouped_files = {} # {source_label: [file_info, ...]}
                
                for f in sorted(files_in_staging):
                    if f.startswith('.') or f.endswith('.meta'): continue
                    fpath = os.path.join(target_dir, f)
                    
                    # 提取元数据
                    source_label = "外部导入"
                    sync_time = "未知时间"
                    meta_path = fpath + ".meta"
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as meta_f:
                                for line in meta_f:
                                    if line.startswith("Source:"):
                                        source_label = line.split(":", 1)[1].strip()
                                    elif line.startswith("SyncTime:"):
                                        sync_time = line.split(":", 1)[1].strip()[11:16]
                        except: pass
                    else:
                        # 降级推断
                        if f.startswith('[DB]'): source_label = "数据库快照"
                        elif f.startswith('[SQL]'): source_label = "自定义SQL"
                        elif f.startswith('Web_'): source_label = "网页抓取"
                        elif f.startswith('Search_'): source_label = "智能搜索"
                        elif f.startswith('Pasted_'): source_label = "文本粘贴"
                    
                    if source_label not in grouped_files:
                        grouped_files[source_label] = []
                    
                    size_kb = os.path.getsize(fpath)/1024 if os.path.exists(fpath) else 0
                    grouped_files[source_label].append({
                        "name": f,
                        "size": f"{size_kb:.1f}k",
                        "time": sync_time
                    })

                # 构建全量内容 HTML
                full_html = f"""
                <div style='max-height: 450px; overflow-y: auto; overflow-x: hidden; padding-right: 5px;'>
                    <h4 style='margin-bottom: 5px;'>📦 暂存区资产清单</h4>
                    <div style='font-size: 0.8rem; color: #666; margin-bottom: 10px;'>📍 物理路径: <code>{target_dir}</code></div>
                    <div style='border-top: 1px solid #eee; padding-top: 5px;'>
                """
                
                for label, files in grouped_files.items():
                    icon = "📄"
                    if "数据库" in label or "SQL" in label: icon = "🗄️"
                    elif "网页" in label: icon = "🌐"
                    elif "搜索" in label: icon = "🔍"
                    elif "粘贴" in label: icon = "📝"
                    elif "上传" in label: icon = "📤"
                    elif "目录" in label: icon = "📁"
                    
                    full_html += f"<div style='font-weight: bold; margin-top: 12px; margin-bottom: 4px; font-size: 0.85rem; color: #1f77b4;'>{icon} {label} ({len(files)})</div>"
                    
                    for item in files:
                        full_html += (
                            f"<div style='font-size: 0.75rem; margin-left: 10px; border-left: 2px solid #f0f2f6; "
                            f"padding-left: 8px; color: #555; word-break: break-all; "
                            f"line-height: 1.6; margin-bottom: 2px;'>"
                            f"▫️ {item['name']} <span style='color: #bbb;'>({item['size']} | {item['time']})</span>"
                            f"</div>"
                        )
                full_html += "</div></div>"
                st.markdown(full_html, unsafe_allow_html=True)
            else:
                st.markdown("#### 📦 暂存区资产清单")
                st.info("暂存区为空")

    with stat_col_open:
        if st.button("📍", help="在 Finder 中显示暂存区", key=f"{key_prefix}_open_btn"):
            if reveal_in_file_manager(target_dir):
                st.toast("📂 已在 Finder 中打开")
            else:
                st.error("无法打开 Finder")

    with stat_col_refresh:
        if st.button("🔄", help="强制同步并刷新暂存区", key=f"{key_prefix}_refresh_btn"):
            # 1. 重置上传哈希 (需要调用者配合，或者这里约定 key)
            hash_key = f"{key_prefix}_last_upload_hash"
            if hash_key in st.session_state:
                st.session_state[hash_key] = None
            
            # 2. 重新扫描路径 (尝试读取 session state 中的路径输入)
            path_input_key = f"{key_prefix}_path_input"
            m_path = st.session_state.get(path_input_key)
            if m_path and os.path.exists(m_path):
                from .unified_ingestion import sync_to_staging as local_sync
                sync_to_staging(target_dir, m_path, is_file=False, source_label="同步刷新")
            
            st.toast("✅ 暂存区同步刷新成功")

    with stat_col2:
        if st.button("🧹", help="清空暂存区", use_container_width=True, key=f"{key_prefix}_clean_btn"):
            try:
                shutil.rmtree(target_dir)
                os.makedirs(target_dir, exist_ok=True)
                # 清除相关 session state
                hash_key = f"{key_prefix}_last_upload_hash"
                if hash_key in st.session_state:
                    st.session_state[hash_key] = None
                
                # 特别处理：如果是主创建流程，清除 uploaded_path
                if key_prefix == "create" or key_prefix == "omni":
                    st.session_state.uploaded_path = None
                
                st.toast("🗑️ 暂存区已清空")
            except Exception as e:
                st.error(f"清空失败: {e}")

def render_omni_ingestion_tabs(target_dir, key_prefix="omni", can_upload=True, on_success=None):
    """
    渲染五大源全能摄入面板 (可复用组件)
    """
    # 确保目标目录存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    # 内部辅助成功处理
    def _handle_local_success(source_name, count):
        handle_ingestion_success(source_name, count)
        if on_success:
            on_success(source_name, count)

    # --- 五大源标准 Tabs ---
    tabs = st.tabs(["📂 上传文件", "📁 扫描路径", "📝 文本粘贴", "🌐 网页摄入", "🗄️ 数据库快照"])
    
    # Tab 1: 文件上传
    with tabs[0]:
        uploaded_files = st.file_uploader(
            "拖入文件", 
            accept_multiple_files=True, 
            key=f"{key_prefix}_uploader",
            label_visibility="collapsed",
            type=['pdf', 'docx', 'txt', 'md', 'xlsx', 'csv', 'pptx', 'jpg', 'png', 'jpeg'],
            disabled=not can_upload
        )
        if uploaded_files:
            import hashlib
            upload_hash = hashlib.md5("".join([f"{f.name}_{f.size}" for f in uploaded_files]).encode()).hexdigest()
            
            last_hash_key = f"{key_prefix}_last_upload_hash"
            
            if st.session_state.get(last_hash_key) != upload_hash:
                with st.spinner("⚡ 同步中..."):
                    batch_dir = save_uploaded_files(uploaded_files, "temp_uploads")
                    if batch_dir:
                        count = sync_to_staging(target_dir, batch_dir, is_file=False, source_label="文件上传")
                        if count > 0:
                            st.session_state[last_hash_key] = upload_hash
                            _handle_local_success("文件上传", count)
            else:
                st.caption("✨ 当前批次文件已在暂存区")
    
    # Tab 2: 本地路径
    with tabs[1]:
        path_c1, path_c2 = st.columns([5, 1])
        manual_path = path_c1.text_input("本地路径", placeholder="粘贴本地目录地址...", key=f"{key_prefix}_path_input", label_visibility="collapsed")
        if path_c2.button("📥 镜像", use_container_width=True, key=f"{key_prefix}_path_btn"):
            if os.path.exists(manual_path):
                count = sync_to_staging(target_dir, manual_path, is_file=False, source_label="目录镜像")
                if count > 0:
                    _handle_local_success("目录镜像", count)
            else: st.error("路径不存在")
    
    # Tab 3: 文本粘贴
    with tabs[2]:
        paste_key = f"{key_prefix}_paste_input"
        
        content = st.text_area("粘贴文本内容", height=150, placeholder="在此输入或粘贴文本...", label_visibility="collapsed", key=paste_key)
        
        if st.button("📥 保存文本", use_container_width=True, key=f"{key_prefix}_paste_btn"):
            if content.strip():
                safe_name = f"Pasted_{int(time.time())}.txt"
                fpath = os.path.join(target_dir, safe_name)
                try:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    with open(fpath + ".meta", "w", encoding="utf-8") as meta_f:
                        meta_f.write(f"Source: 文本粘贴\nSyncTime: {datetime.now().isoformat()}\n")
                    _handle_local_success("文本粘贴", 1)
                except Exception as e:
                    st.error(f"保存失败: {e}")

    # Tab 4: 网页摄入
    with tabs[3]:
        # 复用原有的网页摄入逻辑
        try:
            from src.config.unified_sites import get_industry_list
            industries = get_industry_list()
            with st.expander("⚙️ 行业上下文 (影响搜索结果)", expanded=False):
                sel_ind = st.selectbox("行业领域", industries, key=f"{key_prefix}_wf_industry", label_visibility="collapsed")
        except:
            sel_ind = "🔧 技术开发"

        c_input, c_btn = st.columns([7, 1])
        with c_input:
            user_input = st.text_input("网址或关键词", placeholder="输入 URL (https://...)", label_visibility="collapsed", key=f"{key_prefix}_wf_input")
        with c_btn:
            st.button("🧠", help="AI 智能分析", key=f"{key_prefix}_wf_smart_analyze", use_container_width=True)

        # 智能识别
        crawl_url = None
        search_keyword = None
        if user_input:
            if user_input.strip().lower().startswith(('http://', 'https://')):
                crawl_url = user_input.strip()
                st.caption(f"🔗 已识别为网址")
            else:
                search_keyword = user_input.strip()
                st.caption(f"🔍 已识别为搜索关键词")

        # 参数行
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        with c_p1:
            wf_crawl_depth = st.number_input("递归深度", 1, 10, 2, key=f"{key_prefix}_wf_depth")
        with c_p2:
            wf_max_pages = st.number_input("最大页数", 1, 1000, 5, key=f"{key_prefix}_wf_pages")
        with c_p3:
            wf_parser_type = st.selectbox("解析器", ["default", "article", "documentation"], key=f"{key_prefix}_wf_parser")
        with c_p4:
            wf_quality_threshold = st.number_input("质量阈值", 0.0, 100.0, 45.0, 5.0, key=f"{key_prefix}_wf_quality")

        with st.expander("🚫 排除链接", expanded=False):
            wf_exclude_text = st.text_area("每行一个", height=68, placeholder="*/admin/*", key=f"{key_prefix}_wf_exclude")
            wf_exclude_patterns = [line.strip() for line in wf_exclude_text.split('\n') if line.strip()] if wf_exclude_text else []

        if st.button("📥 抓取并投递", use_container_width=True, type="primary", key=f"{key_prefix}_wf_run", disabled=not user_input):
            status_container = st.status("🕷️ 正在执行网页摄入...", expanded=True)
            
            def web_log(msg, *args):
                status_container.write(msg)
            
            try:
                saved_files = []
                if crawl_url:
                    from src.processors.enhanced_web_crawler import run_async_crawl
                    saved_files = run_async_crawl(
                        start_url=crawl_url, 
                        max_depth=wf_crawl_depth, 
                        max_pages=wf_max_pages,
                        parser_type=wf_parser_type, 
                        output_dir=target_dir, 
                        exclude_patterns=wf_exclude_patterns,
                        status_callback=web_log
                    )
                else:
                    # 智能搜索逻辑 (简化版引用)
                    from src.processors.concurrent_crawler import ConcurrentCrawler
                    from urllib.parse import quote
                    import requests
                    from bs4 import BeautifulSoup
                    
                    q = quote(search_keyword)
                    search_urls = [f"https://www.bing.com/search?q={q}", f"https://html.duckduckgo.com/html/?q={q}"]
                    
                    def discovery_links_violently_local(urls):
                        found_links = []
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        for u in urls:
                            try:
                                resp = requests.get(u, headers=headers, timeout=10)
                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.content, 'html.parser')
                                    for a in soup.find_all('a', href=True):
                                        href = a['href']
                                        if href.startswith('http'): found_links.append(href)
                            except: pass
                        return list(set(found_links))
                    
                    initial_docs = discovery_links_violently_local(search_urls)
                    if initial_docs:
                         crawler = ConcurrentCrawler(max_workers=3, use_processes=False)
                         crawl_results = crawler.crawl_with_depth(
                            initial_docs, 
                            max_depth=wf_crawl_depth, 
                            max_pages_per_level=wf_max_pages, 
                            progress_callback=web_log
                        )
                         for res in crawl_results:
                             if res.get('success'):
                                 fname = f"Search_{int(time.time())}_{hash(res['url'])}.md"
                                 with open(os.path.join(target_dir, fname), 'w') as f:
                                     f.write(res.get('content', ''))
                                 saved_files.append(fname)

                if saved_files:
                    status_container.update(label=f"🎉 成功摄入 {len(saved_files)} 个页面", state="complete", expanded=False)
                    _handle_local_success("网页摄入", len(saved_files))
                else:
                    status_container.update(label="❌ 未获取到有效内容", state="error")
            except Exception as e:
                status_container.update(label=f"❌ 失败: {e}", state="error")

    # Tab 5: 数据库快照
    with tabs[4]:
        from src.processors.database_exporter import DatabaseExporter
        from src.auth.connection_manager import ConnectionManager
        
        conn_mgr = ConnectionManager()
        curr_user = st.session_state.get('user', 'guest_user')
        curr_role = st.session_state.get('role', 'guest')
        
        saved_conns = conn_mgr.load_connections() if curr_role == 'admin' else conn_mgr.get_connections_for_user(curr_user)
        
        if not saved_conns:
            st.info("ℹ️ 暂无可用连接，请在 [👤 我的 -> 🔌 数据连接] 中配置")
        else:
            c_conn, c_db = st.columns([1, 1])
            with c_conn:
                selected_alias = st.selectbox("1. 数据源", list(saved_conns.keys()), key=f"{key_prefix}_db_alias")
                conn_conf = saved_conns[selected_alias]
            
            with c_db:
                dbs = conn_mgr.get_database_list(selected_alias)
                default_db = conn_conf.get('database')
                db_idx = dbs.index(default_db) if default_db in dbs else 0
                selected_db = st.selectbox("2. 数据库", dbs, index=db_idx, key=f"{key_prefix}_db_name")

            if selected_db:
                st.divider()
                snap_mode = st.radio("快照模式", ["📋 数据表选择", "📝 自定义 SQL"], horizontal=True, label_visibility="collapsed", key=f"{key_prefix}_db_mode")
                
                exporter = DatabaseExporter(target_dir)
                
                if snap_mode == "📋 数据表选择":
                    tables = conn_mgr.get_table_list(selected_alias, db_override=selected_db)
                    if not tables:
                        st.warning("📭 该库为空")
                    else:
                        sel_tables = st.multiselect("选择数据表", tables, key=f"{key_prefix}_db_tables")
                        if st.button("📥 导出并投递", type="primary", use_container_width=True, disabled=not sel_tables, key=f"{key_prefix}_db_export_btn"):
                            status = st.status("📸 正在导出...", expanded=True)
                            try:
                                for t in sel_tables:
                                    status.write(f"导出: {t}...")
                                    exporter.export(selected_alias, selected_db, table_name=t)
                                status.update(label="✅ 完成", state="complete", expanded=False)
                                _handle_local_success("数据库快照", len(sel_tables))
                            except Exception as e:
                                status.update(label="❌ 失败", state="error")
                                st.error(str(e))
                
                elif snap_mode == "📝 自定义 SQL":
                    sql_input = st.text_area("SQL 语句", height=150, key=f"{key_prefix}_db_sql")
                    filename_hint = st.text_input("文件名标识", key=f"{key_prefix}_db_hint")
                    
                    if st.button("📥 执行并投递", type="primary", key=f"{key_prefix}_db_sql_btn"):
                        if not sql_input.strip():
                            st.error("请输入 SQL")
                        else:
                            try:
                                final_name = None
                                if filename_hint.strip():
                                    final_name = f"[SQL]{filename_hint}_{int(time.time())}.csv"
                                exporter.export(selected_alias, selected_db, sql_query=sql_input, output_filename=final_name)
                                _handle_local_success("自定义SQL", 1)
                            except Exception as e:
                                st.error(str(e))

@st.fragment
def _render_advanced_options_content(key_prefix, allow_reindex, allow_data_analysis, can_rebuild):
    """
    高级选项内部内容渲染 (Fragment 隔离，防止全量 Rerun 卡顿)
    """
    # Select All Logic with Callback
    def toggle_all():
        val = st.session_state.get(f"{key_prefix}_select_all", False)
        st.session_state[f"{key_prefix}_use_ocr"] = val
        st.session_state[f"{key_prefix}_extract_metadata"] = val
        st.session_state[f"{key_prefix}_generate_summary"] = val
        if allow_data_analysis:
            st.session_state[f"{key_prefix}_enable_data_analysis"] = val
        if allow_reindex and can_rebuild:
            st.session_state[f"{key_prefix}_force_reindex"] = val

    # 预计算状态，避免使用 st.empty 造成闪烁
    # 注意：此时 session_state 已经被 callback 更新（如果有触发）
    # 或者如果没有触发 callback，也是最新的
    
    # 辅助获取当前值的函数 (默认 False)
    def get_val(suffix):
        return st.session_state.get(f"{key_prefix}_{suffix}", False)

    options_labels = []
    if allow_reindex and can_rebuild and get_val("force_reindex"): options_labels.append("重建")
    if get_val("use_ocr"): options_labels.append("OCR")
    if allow_data_analysis and get_val("enable_data_analysis"): options_labels.append("分析")
    if get_val("extract_metadata"): options_labels.append("元数据")
    if get_val("generate_summary"): options_labels.append("摘要")
    
    status_text = f"🔧 启用: {'|'.join(options_labels)}" if options_labels else "⚡ 快速模式：已关闭高级选项"

    # 布局优化：全选 + 状态提示在一行
    h_col1, h_col2 = st.columns([1.5, 2.5])
    with h_col1:
        # Checkbox 状态会自动同步 session_state
        select_all = st.checkbox("✅ 一键全选", value=False, key=f"{key_prefix}_select_all", on_change=toggle_all, help="开启/关闭所有高级选项")
    with h_col2:
        # 直接渲染文本，无占位符，无延迟
        st.caption(status_text)
    
    # 布局调整：两行 (3 + 2)
    # Row 1: OCR, Metadata, Summary
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    
    with r1_c1:
        use_ocr = st.checkbox("🔍 OCR文字识别", value=False, key=f"{key_prefix}_use_ocr", help="识别图片或PDF中的文字")
    with r1_c2:
        extract_metadata = st.checkbox("📊 元数据提取", value=False, key=f"{key_prefix}_extract_metadata", help="自动提取文件分类、关键词")
    with r1_c3:
        generate_summary = st.checkbox("📝 自动摘要生成", value=False, key=f"{key_prefix}_generate_summary", help="为每份文件生成AI摘要")

    # Row 2: Data Analysis, Reindex (Empty 3rd col)
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    
    with r2_c1:
        enable_data_analysis = False
        if allow_data_analysis:
            enable_data_analysis = st.checkbox("💎 智能数据分析", value=False, key=f"{key_prefix}_enable_data_analysis", help="自动识别真数据，构建物理库，启用SQL决策")
        else:
            st.caption("ℹ️ 追加模式暂不支持数据分析")
    
    with r2_c2:
        force_reindex = False
        if allow_reindex:
            if can_rebuild:
                force_reindex = st.checkbox("🔄 强制重建索引", value=False, key=f"{key_prefix}_force_reindex", help="物理删除旧索引，触发全量重建（慎用）")
            else:
                st.checkbox("🔄 强制重建索引 (🔒)", value=False, disabled=True, help="无重建索引权限")
        else:
            st.caption("ℹ️ 追加模式下不可重建索引")

    return {
        "use_ocr": use_ocr,
        "extract_metadata": extract_metadata,
        "force_reindex": force_reindex,
        "enable_data_analysis": enable_data_analysis,
        "generate_summary": generate_summary
    }

def render_advanced_options(key_prefix="kb_adv", expanded=False, allow_reindex=True, allow_data_analysis=True):
    """
    渲染统一的高级选项面板 (五大核心选项)
    """
    with st.expander("🔧 高级选项", expanded=expanded):
        # 权限检查
        from src.auth.permission_manager import permission_manager
        current_user = st.session_state.get('user', 'guest_user')
        can_rebuild = permission_manager.has_permission(current_user, "kb_rebuild_index")

        # 委托给 Fragment 处理内部逻辑
        return _render_advanced_options_content(key_prefix, allow_reindex, allow_data_analysis, can_rebuild)