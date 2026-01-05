"""
文档管理器模块
负责文档列表显示、搜索、筛选和管理
"""

import os
import json
import time
import streamlit as st
from llama_index.core import StorageContext, load_index_from_storage

from src.app_logging import LogManager
from src.config import ManifestManager
from src.metadata_manager import MetadataManager

logger = LogManager()


class DocumentManager:
    """文档管理器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.manifest = ManifestManager.load(db_path)
    
    def get_kb_statistics(self):
        """获取知识库统计信息"""
        files = self.manifest.get('files', [])
        file_cnt = len(files)
        
        # 计算统计信息
        total_sz = 0
        total_chunks = 0
        file_types = {}
        oldest_date = None
        newest_date = None
        
        for f in files:
            try:
                if 'KB' in f['size']:
                    total_sz += float(f['size'].replace(' KB', ''))
                elif 'MB' in f['size']:
                    total_sz += float(f['size'].replace(' MB', '')) * 1024
            except:
                pass
            
            total_chunks += len(f.get('doc_ids', []))
            ftype = f.get('type', 'Unknown')
            file_types[ftype] = file_types.get(ftype, 0) + 1
            
            file_date = f.get('added_at', '')
            if file_date:
                if oldest_date is None or file_date < oldest_date:
                    oldest_date = file_date
                if newest_date is None or file_date > newest_date:
                    newest_date = file_date
        
        # 计算向量库实际存储大小
        db_size = 0
        if os.path.exists(self.db_path):
            try:
                for root, dirs, files_walk in os.walk(self.db_path):
                    db_size += sum(os.path.getsize(os.path.join(root, f)) for f in files_walk)
            except Exception:
                pass

        return {
            'file_cnt': file_cnt,
            'total_sz': total_sz,
            'total_chunks': total_chunks,
            'file_types': file_types,
            'oldest_date': oldest_date,
            'newest_date': newest_date,
            'size': db_size
        }
    
    def render_statistics_overview(self, kb_name, stats):
        """渲染统计概览"""
        # 知识库名称和修改按钮在一行
        name_col, edit_col = st.columns([4, 1])
        with name_col:
            st.markdown(f"### 💬 {kb_name}")
        
        # 返回编辑按钮列，用于放置修改按钮
        return edit_col
    
    def render_detailed_statistics(self, stats):
        """渲染详细统计信息"""
        file_cnt = stats['file_cnt']
        total_sz = stats['total_sz']
        total_chunks = stats['total_chunks']
        file_types = stats['file_types']
        oldest_date = stats['oldest_date']
        newest_date = stats['newest_date']
        
        # 计算存储大小
        db_size = 0
        if os.path.exists(self.db_path):
            for root, dirs, files in os.walk(self.db_path):
                db_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        db_size_mb = db_size / (1024 * 1024)
        
        # 计算成功率和压缩比
        files_with_chunks = len([f for f in self.manifest['files'] if len(f.get('doc_ids', [])) > 0])
        success_rate = (files_with_chunks / file_cnt * 100) if file_cnt > 0 else 0
        
        total_sz_bytes = total_sz * 1024
        compression_ratio = (total_sz_bytes / db_size) if db_size > 0 else 0
        storage_efficiency = f"{compression_ratio:.1f}x" if compression_ratio > 1 else "1.0x" if compression_ratio > 0 else "N/A"
        
        # 时间范围
        last_upd = self.manifest.get('last_updated', 'N/A')[:10]
        time_range = f"{oldest_date[:10]} ~ {newest_date[:10]}" if oldest_date and newest_date else last_upd
        
        # 统计摘要
        st.markdown(f"**📊 统计** · {file_cnt} 文件 · {total_chunks} 片段 · 📁 原始 {f'{total_sz/1024:.1f}MB' if total_sz > 1024 else f'{int(total_sz)}KB'} · 💾 向量库 {db_size_mb:.1f}MB ({storage_efficiency}) · 📅 {time_range}")
        
        # 核心指标 - 优化为单行布局 (6列)
        metric_cols = st.columns(6)
        
        avg_chunks = total_chunks / file_cnt if file_cnt > 0 else 0
        avg_size = (total_sz / file_cnt) if file_cnt > 0 else 0
        
        with metric_cols[0]:
            st.metric("📈 平均片段", f"{avg_chunks:.1f}")
        with metric_cols[1]:
            st.metric("📊 平均大小", f"{avg_size/1024:.1f}KB" if avg_size > 1024 else f"{int(avg_size)}KB")
        
        # 健康度
        health_icon = "🟢" if success_rate >= 90 else "🟡" if success_rate >= 70 else "🔴"
        with metric_cols[2]:
            st.metric("💚 健康度", f"{health_icon} {success_rate:.0f}%")
        
        # 质量分析
        low_quality = len([f for f in self.manifest['files'] if len(f.get('doc_ids', [])) < 2])
        large_files = len([f for f in self.manifest['files'] if 'MB' in f['size']])
        empty_docs = len([f for f in self.manifest['files'] if len(f.get('doc_ids', [])) == 0])
        
        quality_status = "✅ 优秀" if low_quality == 0 and large_files == 0 and empty_docs == 0 else f"⚠️ {empty_docs}空 {low_quality}低质"
        with metric_cols[3]:
            st.metric("🔍 质量", quality_status)
        
        type_count = len(file_types)
        with metric_cols[4]:
            st.metric("📂 类型", f"{type_count} 种")
        
        kb_model = self.manifest.get('embed_model', 'Unknown')
        with metric_cols[5]:
            st.metric("🔤 模型", kb_model.split('/')[-1][:12] if '/' in kb_model else kb_model[:12])
        
        return {
            'success_rate': success_rate,
            'low_quality': low_quality,
            'empty_docs': empty_docs
        }
    
    def render_distribution_analysis(self, stats):
        """渲染分布分析"""
        file_types = stats['file_types']
        file_cnt = stats['file_cnt']
        
        # 四列布局：类型分布 + 大小分布 + 片段分布 + 数据洞察
        type_col, size_col, chunk_col, insight_col = st.columns([2, 2, 2, 2])
        
        with type_col:
            st.markdown("**📂 类型分布**")
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            for i, (ftype, count) in enumerate(sorted_types[:5]):
                pct = (count / file_cnt * 100) if file_cnt > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                st.caption(f"{ftype}: {count} ({pct:.0f}%) {bar[:10]}")
            if len(sorted_types) > 5:
                other_count = sum(c for _, c in sorted_types[5:])
                other_pct = (other_count / file_cnt * 100) if file_cnt > 0 else 0
                st.caption(f"其他: {other_count} ({other_pct:.0f}%)")
        
        with size_col:
            st.markdown("**📊 大小分布**")
            size_ranges = {"<100KB": 0, "100KB-1MB": 0, "1MB-10MB": 0, ">10MB": 0}
            for f in self.manifest['files']:
                size_bytes = f.get('size_bytes', 0)
                if size_bytes < 100 * 1024:
                    size_ranges["<100KB"] += 1
                elif size_bytes < 1024 * 1024:
                    size_ranges["100KB-1MB"] += 1
                elif size_bytes < 10 * 1024 * 1024:
                    size_ranges["1MB-10MB"] += 1
                else:
                    size_ranges[">10MB"] += 1
            
            for range_name, count in size_ranges.items():
                if count > 0:
                    pct = (count / file_cnt * 100) if file_cnt > 0 else 0
                    st.caption(f"{range_name}: {count} ({pct:.0f}%)")
        
        with chunk_col:
            st.markdown("**📦 片段分布**")
            chunk_ranges = {"0片段": 0, "1-5片段": 0, "6-20片段": 0, ">20片段": 0}
            for f in self.manifest['files']:
                chunk_count = len(f.get('doc_ids', []))
                if chunk_count == 0:
                    chunk_ranges["0片段"] += 1
                elif chunk_count <= 5:
                    chunk_ranges["1-5片段"] += 1
                elif chunk_count <= 20:
                    chunk_ranges["6-20片段"] += 1
                else:
                    chunk_ranges[">20片段"] += 1
            
            for range_name, count in chunk_ranges.items():
                if count > 0:
                    pct = (count / file_cnt * 100) if file_cnt > 0 else 0
                    icon = "⚠️" if range_name == "0片段" else "✅" if range_name == ">20片段" else ""
                    st.caption(f"{icon}{range_name}: {count} ({pct:.0f}%)")
        
        with insight_col:
            st.markdown("**💡 数据洞察**")
            if self.manifest['files']:
                # 热门文件
                hot_files = [(f['name'], f.get('hit_count', 0)) for f in self.manifest['files'] if f.get('hit_count', 0) > 0]
                if hot_files:
                    hot_files.sort(key=lambda x: x[1], reverse=True)
                    top_file = hot_files[0]
                    st.caption(f"🔥 最热: {top_file[0][:12]}... ({top_file[1]}次)")
                
                # 最多片段
                chunks_list = [(f['name'], len(f.get('doc_ids', []))) for f in self.manifest['files']]
                most_chunks = max(chunks_list, key=lambda x: x[1]) if chunks_list else None
                if most_chunks and most_chunks[1] > 0:
                    st.caption(f"🔢 最多片段: {most_chunks[0][:12]}... ({most_chunks[1]})")
                
                # 主要类型
                if file_types:
                    main_type = max(file_types.items(), key=lambda x: x[1])
                    st.caption(f"📂 主要类型: {main_type[0]} ({main_type[1]}个)")
    
    def filter_and_sort_files(self, search_term, filter_type, filter_category, filter_heat, filter_quality, sort_by):
        """筛选和排序文件"""
        filtered_files = self.manifest['files']
        
        # 搜索
        if search_term:
            filtered_files = [f for f in filtered_files if search_term.lower() in f['name'].lower()]
        
        # 类型筛选
        if filter_type != "全部":
            filtered_files = [f for f in filtered_files if f.get('type') == filter_type]
        
        # 分类筛选
        if filter_category != "全部":
            filtered_files = [f for f in filtered_files if f.get('category') == filter_category]
        
        # 热度筛选
        if filter_heat == "高频":
            filtered_files = [f for f in filtered_files if f.get('hit_count', 0) > 10]
        elif filter_heat == "中频":
            filtered_files = [f for f in filtered_files if 3 < f.get('hit_count', 0) <= 10]
        elif filter_heat == "低频":
            filtered_files = [f for f in filtered_files if 0 < f.get('hit_count', 0) <= 3]
        elif filter_heat == "未用":
            filtered_files = [f for f in filtered_files if f.get('hit_count', 0) == 0]
        
        # 质量筛选
        if filter_quality == "优秀":
            filtered_files = [f for f in filtered_files if len(f.get('doc_ids', [])) >= 10]
        elif filter_quality == "正常":
            filtered_files = [f for f in filtered_files if 2 <= len(f.get('doc_ids', [])) < 10]
        elif filter_quality == "低质":
            filtered_files = [f for f in filtered_files if 0 < len(f.get('doc_ids', [])) < 2]
        elif filter_quality == "空":
            filtered_files = [f for f in filtered_files if len(f.get('doc_ids', [])) == 0]
        
        # 排序
        if sort_by == "时间↓":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('added_at', ''), reverse=True)
        elif sort_by == "时间↑":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('added_at', ''))
        elif sort_by == "大小↓":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('size_bytes', 0), reverse=True)
        elif sort_by == "大小↑":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('size_bytes', 0))
        elif sort_by == "名称":
            filtered_files = sorted(filtered_files, key=lambda x: x['name'].lower())
        elif sort_by == "热度↓":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('hit_count', 0), reverse=True)
        elif sort_by == "片段↓":
            filtered_files = sorted(filtered_files, key=lambda x: len(x.get('doc_ids', [])), reverse=True)
        
        return filtered_files
    
    @st.fragment
    def render_file_list(self, filtered_files, start_idx, end_idx, page_size):
        """渲染文件列表 (局部刷新模式)"""
        # 表头 - 与 _render_file_row 保持一致 [0.4, 0.8, 2.3, 0.8, 0.6, 0.8, 0.6, 1.2, 1.0]
        cols = st.columns([0.4, 0.8, 2.3, 0.8, 0.6, 0.8, 0.6, 1.2, 1.0])
        
        # 1. 全选复选框
        current_page_files = [f['name'] for f in filtered_files[start_idx:end_idx]]
        
        selected_for_summary = st.session_state.get('selected_for_summary', set())
        
        if current_page_files:
            all_selected = all(fname in selected_for_summary for fname in current_page_files)
            
            def toggle_select_all():
                if st.session_state.get(f"select_all_page_{st.session_state.file_page}"):
                    st.session_state.selected_for_summary.update(current_page_files)
                else:
                    st.session_state.selected_for_summary.difference_update(current_page_files)
            
            cols[0].checkbox(
                "全选",
                value=all_selected,
                key=f"select_all_page_{st.session_state.file_page}",
                label_visibility="collapsed",
                on_change=toggle_select_all
            )
        else:
            cols[0].markdown("**✨**")
            
        # 2. 批量操作按钮 (紧跟在全选框后面)
        selected_count = len(selected_for_summary)
        if selected_count > 0:
            btn_col = cols[1]
            b1, b2 = btn_col.columns(2)
            if b1.button("✨", key="batch_sum_btn", help=f"为选中的 {selected_count} 个文件生成摘要"):
                st.session_state.trigger_batch_summary = True
            if b2.button("🗑️", key="batch_del_btn", help=f"批量删除选中的 {selected_count} 个文件"):
                st.session_state.trigger_batch_delete = True
        else:
            cols[1].markdown("**ID**")
            
        cols[2].markdown("**文件名**")
        cols[3].markdown("**类型**")
        cols[4].markdown("**片段**")
        cols[5].markdown("**大小**")
        cols[6].markdown("**质量**")
        cols[7].markdown("**时间**")
        cols[8].markdown("**操作**")
        st.divider()
        
        # 渲染文件行
        for i in range(start_idx, end_idx):
            f = filtered_files[i]
            orig_idx = self.manifest['files'].index(f)
            
            self._render_file_row(f, orig_idx, i)
    
    def _render_file_row(self, f, orig_idx, display_idx):
        """渲染单个文件行"""
        # 调整列比例，与表头对齐 [0.4, 0.8, 2.3, 0.8, 0.6, 0.8, 0.6, 1.2, 1.0]
        cols = st.columns([0.4, 0.8, 2.3, 0.8, 0.6, 0.8, 0.6, 1.2, 1.0])
        
        # 复选框 (始终显示)
        if True:
            if 'selected_for_summary' not in st.session_state:
                st.session_state.selected_for_summary = set()
            
            is_checked = f['name'] in st.session_state.selected_for_summary
            checked = cols[0].checkbox("选择", value=is_checked, 
                                     key=f"sum_{f['name']}_{st.session_state.file_page}", 
                                     label_visibility="collapsed")
            
            if checked:
                st.session_state.selected_for_summary.add(f['name'])
            else:
                st.session_state.selected_for_summary.discard(f['name'])
            
        # ID列
        cols[1].caption(f"#{orig_idx+1}")
        
        # 文件信息
        cols[2].caption(f'{f["icon"]} {f["name"]}')
        cols[3].caption(f['type'])
        
        chunk_count = len(f.get('doc_ids', []))
        cols[4].caption(str(chunk_count))
        cols[5].caption(f['size'])
        
        # 质量指示器
        if chunk_count == 0:
            quality_icon = "❌"
        elif chunk_count < 2:
            quality_icon = "⚠️"
        elif chunk_count < 10:
            quality_icon = "✅"
        else:
            quality_icon = "🎉"
        cols[6].caption(quality_icon)
        
        cols[7].caption(f['added_at'])
        
        # 操作列 (预览 + 删除)
        btn_col = cols[8]
        btn_col1, btn_col2 = btn_col.columns(2)
        
        with btn_col1:
            # 查找文件真实路径
            file_name = f['name']
            kb_name = os.path.basename(self.db_path)
            
            # 1. 整理可能的路径候选 (按优先级)
            candidates = []
            
            # A. Manifest 记录的原始路径 (最准确)
            raw_path = f.get('file_path')
            if raw_path: candidates.append(raw_path)
            
            # B. 各种上传目录模糊匹配
            import glob
            patterns = [
                os.path.join("temp_uploads", kb_name, file_name),
                os.path.join("temp_uploads", "batch_*", file_name),
                os.path.join("temp_uploads", "Search_*", file_name),
                os.path.join("temp_uploads", "Web_*", file_name),
                os.path.join("vector_db_storage", kb_name, file_name),
                # 递归查找知识库目录下的文件
                os.path.join("vector_db_storage", kb_name, "**", file_name)
            ]
            
            for pattern in patterns:
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    candidates.extend(matches)
            
            # C. 针对“手动输入文件夹路径”的情况，尝试在父目录中查找
            if raw_path:
                parent_dir = os.path.dirname(raw_path)
                if parent_dir and os.path.exists(parent_dir):
                    candidates.append(os.path.join(parent_dir, file_name))
            
            # 2. 验证并转换为绝对路径
            final_path = None
            for p in candidates:
                abs_p = os.path.abspath(p)
                if os.path.exists(abs_p):
                    final_path = abs_p
                    break
            
            if btn_col1.button("👁️", key=f"prev_{orig_idx}_{display_idx}", help="macOS 原生预览"):
                if final_path:
                    from src.utils.app_utils import open_file_native
                    open_file_native(final_path)
                    st.toast(f"🚀 正在调用系统预览: {file_name}")
                else:
                    st.error(f"找不到文件: {file_name}")
                    # 在控制台输出更详细的调试信息
                    logger.debug(candidates)
                    
        with btn_col2:
            if btn_col2.button("🗑️", key=f"del_{orig_idx}_{display_idx}", help="删除"):
                self._delete_file(f)
        
        # 文件摘要展开
        if f.get('summary'):
            with st.expander(f"📖 {f['summary'][:50]}...", expanded=False):
                st.markdown(f.get('summary'))
        
        # 文件详情展开
        with st.expander(f"📊 详情 - {f['name']}", expanded=False):
            self._render_file_details(f)
    
    def _render_file_details(self, f):
        """渲染文件详情"""
        chunk_count = len(f.get('doc_ids', []))
        
        # 基础信息
        detail_cols = st.columns(4)
        detail_cols[0].metric("📦 片段", chunk_count)
        detail_cols[1].metric("💾 大小", f['size'])
        detail_cols[2].metric("📅 时间", f['added_at'][:10])
        detail_cols[3].metric("🏷️ 类型", f['type'])
        
        # 质量评估
        if chunk_count == 0:
            quality_info = "❌ 解析失败"
        elif chunk_count < 2:
            quality_info = "⚠️ 低质（内容过少）"
        elif chunk_count < 10:
            quality_info = "✅ 正常"
        else:
            quality_info = "🎉 优秀（内容丰富）"
        
        estimated_chars = chunk_count * 500
        st.caption(f"**质量**: {quality_info} · **字符**: ~{estimated_chars:,} · **向量**: {chunk_count}")
        
        # 元数据信息
        if f.get('hit_count', 0) > 0 or f.get('keywords') or f.get('category'):
            st.divider()
            self._render_file_metadata(f)
        
        # 文档ID
        if f.get('doc_ids'):
            if len(f['doc_ids']) <= 3:
                st.caption(f"**片段ID**: `{', '.join(f['doc_ids'])}`")
            else:
                st.caption(f"**片段ID**: `{f['doc_ids'][0]}` ... (共{len(f['doc_ids'])}个)")
                with st.expander("查看全部ID", expanded=False):
                    st.code('\n'.join(f['doc_ids']), language=None)
        else:
            st.warning("⚠️ 未生成片段 · 可能原因：文件为空/格式不支持/已损坏/加密")
    
    def _render_file_metadata(self, f):
        """渲染文件元数据"""
        meta_cols = st.columns(4)
        
        # 检索统计
        hit_count = f.get('hit_count', 0)
        avg_score = f.get('avg_score', 0.0)
        heat = "🔥" if hit_count > 10 else "📊" if hit_count > 3 else "📦" if hit_count > 0 else "❄️"
        
        meta_cols[0].metric("🔥 命中", f"{hit_count} 次")
        meta_cols[1].metric("⭐ 得分", f"{avg_score:.2f}")
        meta_cols[2].metric("🌡️ 热度", heat)
        
        # 最后访问
        last_accessed = f.get('last_accessed')
        if last_accessed:
            meta_cols[3].metric("🕐 访问", last_accessed[:10])
        else:
            meta_cols[3].metric("🕐 访问", "从未")
        
        # 分类和语言
        category = f.get('category', '其他')
        language = f.get('language', 'unknown')
        lang_map = {"zh": "🇨🇳", "en": "🇬🇧", "zh-en": "🌐", "unknown": "❓"}
        lang_icon = lang_map.get(language, "❓")
        
        st.caption(f"**📂 分类**: {category} · **🌍 语言**: {lang_icon} {language}")
        
        # 关键词
        keywords = f.get('keywords', [])
        if keywords:
            st.caption(f"**🏷️ 关键词**: {' · '.join(keywords[:5])}")
    
    def _delete_file(self, f):
        """删除文件"""
        with st.status(f"正在删除 {f['name']}...", expanded=True) as status:
            try:
                ctx = StorageContext.from_defaults(persist_dir=self.db_path)
                idx = load_index_from_storage(ctx)
                for did in f.get('doc_ids', []):
                    idx.delete_ref_doc(did, delete_from_docstore=True)
                idx.storage_context.persist(persist_dir=self.db_path)
                
                # 从 manifest 中移除
                self.manifest['files'] = [file for file in self.manifest['files'] if file['name'] != f['name']]
                with open(ManifestManager.get_path(self.db_path), 'w', encoding='utf-8') as mf:
                    json.dump(self.manifest, mf, indent=4, ensure_ascii=False)
                
                status.update(label="✅ 已删除", state="complete")
                st.session_state.chat_engine = None
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(str(e))
