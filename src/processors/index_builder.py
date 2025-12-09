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
from datetime import datetime

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
                 extract_metadata: bool = True,
                 logger=None):
        self.kb_name = kb_name
        self.persist_dir = persist_dir
        self.embed_model = embed_model
        self.embed_model_name = embed_model_name
        self.extract_metadata = extract_metadata  # 是否提取元数据
        self.logger = logger
        self.metadata_mgr = MetadataManager(persist_dir)
        
        # 初始化并发优化组件
        self.concurrency_mgr = ConcurrencyManager()
        self.batch_optimizer = DynamicBatchOptimizer()
        self.vectorization_wrapper = None  # 延迟初始化
    
    def build(self, source_path: str, force_reindex: bool = False, 
              action_mode: str = "NEW", status_callback=None) -> BuildResult:
        """构建索引"""
        start_time = time.time()
        
        try:
            # 设置嵌入模型
            Settings.embed_model = self.embed_model
            
            # 步骤1: 检查现有索引
            index = self._load_existing_index(force_reindex, action_mode, status_callback)
            
            # 步骤2: 扫描文件
            total_files = self._scan_files(source_path, status_callback)
            
            # 步骤3: 读取文档
            docs, summary = self._read_documents(source_path, total_files, status_callback)
            
            # 步骤4: 构建清单
            file_map = self._build_manifest(source_path, status_callback)
            
            # 步骤5: 解析片段
            valid_docs = self._parse_documents(docs, file_map, source_path, status_callback)
            
            # 步骤6: 构建索引
            index = self._build_index(index, valid_docs, action_mode, status_callback)
            
            # 保存 manifest
            self._save_manifest(file_map)
            
            duration = time.time() - start_time
            return BuildResult(
                success=True,
                index=index,
                file_count=len(file_map),
                doc_count=len(valid_docs),
                duration=duration
            )
            
        except Exception as e:
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
        if callback:
            callback("step", 2, f"扫描文件夹: {os.path.basename(source_path)}")
        
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
        if callback:
            callback("step", 3, f"读取文档内容 (共 {total_files} 个文件)")
        
        docs, process_result = scan_directory_safe(source_path)
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
        if callback:
            callback("step", 4, "构建文件清单")
        
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
        if callback:
            callback("step", 5, f"解析文档片段 (共 {len(docs)} 个)")
        
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
        
        # 生成摘要（后台）
        self._queue_summaries(docs, file_map, callback)
        
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
        """将摘要任务加入队列（异步）"""
        summary_tasks = []
        for d in docs:
            fname = d.metadata.get('file_name')
            if fname and fname in file_map and d.text.strip() and not file_map[fname].get('summary'):
                summary_tasks.append((fname, d.text[:2000]))
        
        if not summary_tasks:
            return
        
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
        # 不等待完成，立即返回
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本"""
        try:
            return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        except:
            return ""
    
    def _build_index(self, index, valid_docs, action_mode, callback):
        """构建向量索引"""
        if callback:
            callback("step", 6, "向量化和索引构建")
        
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
            
            index.storage_context.persist(persist_dir=self.persist_dir)
            
            # 保存知识库信息
            self._save_kb_info()
        
        return index
    
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
