"""
索引构建器
Stage 4.1 - 提取自 apppro.py
Stage 6 - 使用统一的并行执行器
"""

import os
import json
import shutil
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.core.node_parser import SentenceSplitter

from src.metadata_manager import MetadataManager
from src.file_processor import scan_directory_safe
from src.utils.document_processor import get_file_info
from src.utils.parallel_executor import ParallelExecutor
from src.utils.parallel_tasks import extract_metadata_task
from src.utils.concurrency_manager import ConcurrencyManager
from src.utils.vectorization_wrapper import VectorizationWrapper
from src.utils.dynamic_batch import DynamicBatchOptimizer
from src.app_logging.progress_logger import ProgressLogger


@dataclass
class BuildResult:
    """构建结果"""
    success: bool
    index: Optional[VectorStoreIndex]
    file_count: int
    doc_count: int
    duration: float
    error: Optional[str] = None


class IndexBuilder:
    """索引构建器"""
    
    def __init__(self, kb_name: str, persist_dir: str, 
                 embed_model, embed_model_name: str = "Unknown",
                 use_ocr: bool = False,
                 extract_metadata: bool = True,
                 generate_summary: bool = False,
                 logger=None):
        self.kb_name = kb_name
        self.persist_dir = persist_dir
        self.embed_model = embed_model
        self.embed_model_name = embed_model_name
        self.use_ocr = use_ocr  # OCR选项
        self.extract_metadata = extract_metadata  # 是否提取元数据
        self.generate_summary = generate_summary  # 是否生成摘要
        self.logger = logger
        self.metadata_mgr = MetadataManager(persist_dir)
        
        # 初始化并发优化组件
        self.concurrency_mgr = ConcurrencyManager()
        self.batch_optimizer = DynamicBatchOptimizer()
        self.vectorization_wrapper = None  # 延迟初始化
    
    def build(self, source_path: str, force_reindex: bool = False, 
              action_mode: str = "NEW", status_callback=None) -> BuildResult:
        """构建索引"""
        import streamlit as st
        
        start_time = time.time()
        # 初始化详细进度记录器
        progress = ProgressLogger(total_steps=6, logger=self.logger)
        
        # 前端状态显示
        status_placeholder = st.empty()
        progress_bar = st.progress(0, text="⏳ 准备构建索引...")
        
        try:
            # 设置嵌入模型
            Settings.embed_model = self.embed_model
            
            # 步骤1: 检查现有索引
            progress.start_step(1, "检查现有索引")
            status_placeholder.info("🔍 **检查现有索引**: 正在验证索引状态...")
            progress_bar.progress(0.17, text="🔍 检查现有索引...")
            index = self._load_existing_index(force_reindex, action_mode, status_callback)
            progress.end_step("索引检查完成")
            
            # 步骤2: 扫描文件
            progress.start_step(2, f"扫描文件夹: {os.path.basename(source_path)}")
            status_placeholder.info(f"📁 **扫描文件**: 正在扫描 {os.path.basename(source_path)}...")
            progress_bar.progress(0.33, text="📁 扫描文件...")
            total_files = self._scan_files(source_path, status_callback)
            progress.end_step(f"发现 {total_files} 个文件")
            
            # 步骤3: 读取文档
            progress.start_step(3, f"读取文档内容 (共 {total_files} 个文件)")
            status_placeholder.info(f"📄 **读取文档**: 正在处理 {total_files} 个文件...")
            progress_bar.progress(0.50, text=f"📄 读取文档 (0/{total_files})...")
            docs, summary = self._read_documents(source_path, total_files, status_callback)
            progress.end_step(f"成功读取 {summary['success']} 个文件")
            
            # 步骤4: 构建清单
            progress.start_step(4, "构建文件清单")
            status_placeholder.info("📋 **构建清单**: 正在生成文件索引...")
            progress_bar.progress(0.67, text="📋 构建文件清单...")
            file_map = self._build_manifest(source_path, status_callback)

            # --- 合并清单逻辑 (APPEND 模式) ---
            if action_mode == "APPEND":
                try:
                    from src.config import ManifestManager
                    existing = ManifestManager.load(self.persist_dir)
                    existing_files = existing.get('files', [])
                    
                    # 将现有文件转换为 map 格式
                    existing_map = {}
                    for f in existing_files:
                        if isinstance(f, dict):
                            fname = f.get('name')
                            if fname:
                                existing_map[fname] = f
                    
                    # 记录统计
                    old_count = len(existing_map)
                    new_count = len(file_map)
                    
                    # 合并：保留现有文件，用新文件覆盖同名文件
                    # 注意：file_map 中是新扫描的文件，应优先保留 (覆盖旧的同名文件)
                    # 将不在新 batch 中的旧文件加回来
                    for fname, info in existing_map.items():
                        if fname not in file_map:
                            file_map[fname] = info
                            
                    if status_callback:
                        status_callback("info", f"➕ 追加模式: 原有 {old_count} + 新增 {new_count} = 总计 {len(file_map)} 个文件")
                    if self.logger:
                        self.logger.info(f"清单合并: 原有 {old_count} + 新增 {new_count} -> {len(file_map)}")
                        
                except Exception as e:
                    if self.logger: self.logger.warning(f"合并清单失败: {e}")
            # -------------------------------

            progress.end_step(f"登记 {len(file_map)} 个文件")
            
            # 步骤5: 解析片段
            progress.start_step(5, f"解析文档片段 (共 {len(docs)} 个)")
            valid_docs = self._parse_documents(docs, file_map, source_path, status_callback)
            progress.end_step(f"生成 {len(valid_docs)} 个有效片段")
            
            # 步骤6: 构建索引
            progress.start_step(6, "向量化和索引构建")
            index = self._build_index(index, valid_docs, action_mode, status_callback, file_map)
            progress.end_step("索引构建完成")
            
            # 保存 manifest
            self._save_manifest(file_map)
            
            progress.finish_all(success=True)
            
            duration = time.time() - start_time
            return BuildResult(
                success=True,
                index=index,
                file_count=len(file_map),
                doc_count=len(valid_docs),
                duration=duration
            )
            
        except Exception as e:
            progress.finish_all(success=False)
            duration = time.time() - start_time
            return BuildResult(
                success=False,
                index=None,
                file_count=0,
                doc_count=0,
                duration=duration,
                error=str(e)
            )
    
    def _load_existing_index(self, force_reindex, action_mode, callback):
        """加载现有索引"""
        if callback:
            callback("step", 1, "检查现有索引")
        
        if force_reindex or action_mode == "NEW":
            return None
        
        if not os.path.exists(self.persist_dir):
            return None
        
        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            index = load_index_from_storage(storage_context)
            if callback:
                callback("info", "现有索引加载成功")
            return index
        except Exception as e:
            if "shapes" in str(e) and "not aligned" in str(e):
                if callback:
                    callback("warning", "向量维度不匹配，清理旧索引")
            else:
                if callback:
                    callback("warning", "索引损坏，转为新建模式")
            shutil.rmtree(self.persist_dir, ignore_errors=True)
            return None
    
    def _scan_files(self, source_path, callback) -> int:
        """扫描文件"""
        all_files = []
        for root, _, filenames in os.walk(source_path):
            for f in filenames:
                if not f.startswith('.'):
                    all_files.append(os.path.join(root, f))
        
        total = len(all_files)
        if callback:
            callback("info", f"发现 {total} 个文件")
        
        return total
    
    def _read_documents(self, source_path, total_files, callback):
        """读取文档"""
        docs, process_result = scan_directory_safe(source_path, use_ocr=self.use_ocr)
        summary = process_result.get_summary()
        
        if summary['success'] == 0:
            raise ValueError(f"没有成功读取的文件。{process_result.get_report()}")
        
        total = summary['success'] + summary['failed'] + summary['skipped']
        success_rate = (summary['success'] / total * 100) if total > 0 else 0
        
        if callback:
            callback("info", f"读取完成: {summary['success']}/{total} 个文件 ({success_rate:.1f}%)")
        
        return docs, summary
    
    def _build_manifest(self, source_path, callback) -> Dict:
        """构建文件清单"""
        file_map = {}
        for root, _, filenames in os.walk(source_path):
            for f in filenames:
                if not f.startswith('.'):
                    fp = os.path.join(root, f)
                    info = get_file_info(fp, self.metadata_mgr)
                    info['doc_ids'] = []
                    file_map[f] = info
        
        if callback:
            callback("info", f"清单完成: {len(file_map)} 个文件已登记")
        
        return file_map
    
    def _parse_documents(self, docs, file_map, source_path, callback):
        """解析文档片段"""
        # 映射文档ID
        file_text_samples = {}
        for d in docs:
            fname = d.metadata.get('file_name')
            if fname and fname in file_map:
                file_map[fname]['doc_ids'].append(d.doc_id)
                if fname not in file_text_samples and d.text.strip():
                    file_text_samples[fname] = d.text[:1000]
        
        # 提取元数据（可选）
        if self.extract_metadata:
            self._extract_metadata(file_map, file_text_samples, source_path, callback)
        else:
            if callback:
                callback("info", "⚡ 跳过元数据提取（快速模式）")
        
        # 生成摘要（可选）
        if self.generate_summary:
            self._queue_summaries(docs, file_map, callback)
        else:
            if callback:
                callback("info", "⚡ 跳过摘要生成（快速模式）")
        
        # 过滤有效文档
        valid_docs = [d for d in docs if d.text and d.text.strip()]
        
        if callback:
            callback("info", f"解析完成: {len(valid_docs)} 个有效片段")
        
        return valid_docs
    
    def _extract_metadata(self, file_map, text_samples, source_path, callback):
        """提取元数据"""
        if len(text_samples) == 0:
            return
        
        if callback:
            callback("info", f"提取元数据: {len(text_samples)} 个文件")
        
        # 准备任务
        tasks = []
        for fname, text in text_samples.items():
            if fname in file_map:
                fp = os.path.join(source_path, fname)
                if os.path.exists(fp):
                    doc_ids = file_map[fname]['doc_ids']
                    tasks.append((fp, fname, doc_ids, text, self.persist_dir))
        
        if not tasks:
            return
        
        # 使用并行执行器（自动判断串行/并行）
        executor = ParallelExecutor()
        results = executor.execute(extract_metadata_task, tasks, chunksize=50, threshold=50)
        
        # 更新文件信息
        for fname, meta in results:
            if fname in file_map:
                file_map[fname].update({
                    'file_hash': meta.get('file_hash', ''),
                    'keywords': meta.get('keywords', []),
                    'language': meta.get('language', 'unknown'),
                    'category': meta.get('category', '其他文档')
                })
    
    def _queue_summaries(self, docs, file_map, callback):
        """生成摘要并添加到索引（立即执行）"""
        # 按文件名去重，每个文件只生成一次摘要
        file_texts = {}
        for d in docs:
            fname = d.metadata.get('file_name')
            if fname and fname in file_map and d.text.strip() and not file_map[fname].get('summary'):
                if fname not in file_texts:
                    file_texts[fname] = d.text[:2000]  # 只取第一个片段的前2000字符
        
        summary_tasks = list(file_texts.items())
        
        if not summary_tasks:
            return
        
        if callback:
            callback("info", f"正在生成摘要: {len(summary_tasks)} 个文件")
        
        # 立即生成摘要（并行处理）
        try:
            # 导入摘要生成函数
            from src.common.business import generate_doc_summary
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            def generate_single_summary(fname, text):
                """生成单个文件的摘要"""
                try:
                    summary = generate_doc_summary(text, fname)
                    return fname, summary, None
                except Exception as e:
                    return fname, None, str(e)
            
            # 并行生成摘要
            max_workers = min(4, len(summary_tasks))  # 最多4个线程
            completed_count = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_fname = {
                    executor.submit(generate_single_summary, fname, text): fname 
                    for fname, text in summary_tasks
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_fname):
                    fname, summary, error = future.result()
                    completed_count += 1
                    
                    if callback:
                        callback("progress", completed_count, len(summary_tasks), f"生成摘要: {fname}")
                    
                    if summary:
                        # 保存到 file_map
                        file_map[fname]['summary'] = summary
                        if callback:
                            callback("info", f"✅ 摘要生成成功: {fname}")
                    elif error:
                        if self.logger:
                            self.logger.warning(f"⚠️ 摘要生成失败 {fname}: {error}")
                        if callback:
                            callback("warning", f"摘要生成失败: {fname}")
            
            if callback:
                callback("info", f"摘要生成完成: {len(summary_tasks)} 个文件（并行处理）")
                
        except ImportError:
            # 如果无法导入摘要生成函数，回退到队列模式
            if callback:
                callback("warning", "摘要生成函数不可用，使用队列模式")
            self._queue_summaries_async(summary_tasks, callback)
    
    def _queue_summaries_async(self, summary_tasks, callback):
        """异步队列模式（备用方案）"""
        if callback:
            callback("info", f"摘要生成已加入后台队列 ({len(summary_tasks)} 个文件)")
        
        # 异步写入队列文件
        import threading
        
        def write_queue_async():
            try:
                queue_file = os.path.join(self.persist_dir, "summary_queue.json")
                os.makedirs(self.persist_dir, exist_ok=True)
                
                cleaned_tasks = [(fname, self._clean_text(text)) for fname, text in summary_tasks]
                
                with open(queue_file, 'w', encoding='utf-8', errors='ignore') as f:
                    json.dump({
                        'tasks': cleaned_tasks,
                        'total': len(cleaned_tasks),
                        'completed': 0
                    }, f, ensure_ascii=False)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ 摘要队列写入失败: {e}")
        
        # 启动后台线程
        thread = threading.Thread(target=write_queue_async, daemon=True)
        thread.start()
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本"""
        try:
            return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        except:
            return ""
    
    def _build_index(self, index, valid_docs, action_mode, callback, file_map=None):
        """构建向量索引"""
        if index and action_mode == "APPEND":
            # 追加模式
            if callback:
                callback("info", "追加模式: 插入新文档")
            for d in valid_docs:
                index.insert(d)
        else:
            # 新建模式
            if callback:
                callback("info", "新建模式: 构建向量索引（异步优化）")
            
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir, ignore_errors=True)
            
            # 使用优化的向量化包装器
            try:
                if not self.vectorization_wrapper:
                    self.vectorization_wrapper = VectorizationWrapper(
                        embed_model=self.embed_model,
                        batch_optimizer=self.batch_optimizer
                    )
                
                # 动态批量优化向量化
                index = self.vectorization_wrapper.vectorize_documents(valid_docs, show_progress=True)
                if self.logger:
                    self.logger.info("✅ 优化向量化完成")
            except Exception as e:
                # 降级到同步模式
                if self.logger:
                    self.logger.warning(f"优化向量化失败，降级到标准模式: {e}")
                index = VectorStoreIndex.from_documents(valid_docs, show_progress=True)
        
        # 添加摘要文档到索引
        if self.generate_summary and file_map:
            self._add_summaries_to_index(index, file_map, callback)
            
        index.storage_context.persist(persist_dir=self.persist_dir)
        
        # 保存知识库信息
        self._save_kb_info()
        
        return index
    
    def _add_summaries_to_index(self, index, file_map, callback):
        """将摘要添加到向量索引"""
        summary_docs = []
        
        for fname, file_info in file_map.items():
            if file_info.get('summary'):
                try:
                    from llama_index.core import Document
                    summary_doc = Document(
                        text=f"文档摘要 - {fname}:\n{file_info['summary']}",
                        metadata={
                            "file_name": fname,
                            "file_type": "summary",
                            "source_file": fname
                        }
                    )
                    summary_docs.append(summary_doc)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"摘要文档创建失败 {fname}: {e}")
        
        if summary_docs:
            if callback:
                callback("info", f"添加摘要到索引: {len(summary_docs)} 个")
            
            for doc in summary_docs:
                try:
                    index.insert(doc)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"摘要插入失败: {e}")
            
            if callback:
                callback("info", f"✅ 摘要已添加到索引: {len(summary_docs)} 个")
    
    def _save_kb_info(self):
        """保存知识库信息"""
        try:
            # 使用初始化时传入的原始模型名称
            embed_model_name = self.embed_model_name
            embed_dim = 0
            
            if self.embed_model:
                # 尝试获取维度
                try:
                    test_embedding = self.embed_model._get_text_embedding("test")
                    embed_dim = len(test_embedding)
                except:
                    # 根据模型名称推断维度
                    if "small" in embed_model_name.lower():
                        embed_dim = 512
                    elif "base" in embed_model_name.lower():
                        embed_dim = 768
                    elif "large" in embed_model_name.lower():
                        embed_dim = 1024
                    else:
                        embed_dim = 1024
            
            kb_info = {
                "embedding_model": embed_model_name,
                "embedding_dim": embed_dim,
                "created_at": time.time()
            }
            
            kb_info_file = os.path.join(self.persist_dir, ".kb_info.json")
            with open(kb_info_file, 'w') as f:
                json.dump(kb_info, f, indent=2)
            
            if self.logger:
                self.logger.success(f"✅ 已保存知识库信息: {embed_model_name} ({embed_dim}D)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ 保存知识库信息失败: {e}")


    def _save_manifest(self, file_map):
        """保存 manifest.json"""
        try:
            from src.config import ManifestManager
            
            files_list = list(file_map.values())
            ManifestManager.save(
                self.persist_dir,
                files_list,
                self.embed_model_name
            )
            
            if self.logger:
                self.logger.success(f"✅ 已保存文件清单: {len(files_list)} 个文件")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ 保存文件清单失败: {e}")


# 多进程辅助函数
def _extract_metadata_task(task):
    """元数据提取任务（多进程安全）"""
    fp, fname, doc_ids, text_sample, persist_dir = task
    temp_mgr = MetadataManager(persist_dir)
    return fname, temp_mgr.add_file_metadata(fp, doc_ids, text_sample)
