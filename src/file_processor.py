"文件处理结果追踪"
import os
from pathlib import Path
from typing import Dict, List, Tuple

SUPPORTED_FORMATS = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.csv', '.json', '.pptx', '.ppt'}

class FileProcessResult:
    def __init__(self):
        self.success: List[Dict] = []  # [{'file': name, 'size': bytes, 'docs': count}]
        self.failed: List[Dict] = []   # [{'file': name, 'reason': error_msg}]
        self.skipped: List[Dict] = []  # [{'file': name, 'reason': why}]
    
    def add_success(self, filename: str, size: int, doc_count: int):
        self.success.append({'file': filename, 'size': size, 'docs': doc_count})
    
    def add_failed(self, filename: str, reason: str):
        self.failed.append({'file': filename, 'reason': reason})
    
    def add_skipped(self, filename: str, reason: str):
        self.skipped.append({'file': filename, 'reason': reason})
    
    def get_summary(self) -> Dict:
        return {
            'total': len(self.success) + len(self.failed) + len(self.skipped),
            'success': len(self.success),
            'failed': len(self.failed),
            'skipped': len(self.skipped),
            'total_docs': sum(f['docs'] for f in self.success),
            'total_size': sum(f['size'] for f in self.success),
        }
    
    def get_report(self) -> str:
        """生成详细报告"""
        summary = self.get_summary()
        report = f"\n📊 文件处理报告\n"
        report += f"{ '='*50}\n"
        report += f"✅ 成功: {summary['success']} 个文件 ({summary['total_docs']} 个文档)\n"
        report += f"❌ 失败: {summary['failed']} 个文件\n"
        report += f"⏭️  跳过: {summary['skipped']} 个文件\n"
        report += f"{ '='*50}\n"
        
        if self.failed:
            report += f"\n❌ 失败文件详情:\n"
            for item in self.failed[:10]:  # 只显示前10个
                report += f"  • {item['file']}: {item['reason']}\n"
            if len(self.failed) > 10:
                report += f"  ... 还有 {len(self.failed) - 10} 个失败文件\n"
        
        if self.skipped:
            report += f"\n⏭️  跳过文件详情:\n"
            for item in self.skipped[:10]:
                report += f"  • {item['file']}: {item['reason']}\n"
            if len(self.skipped) > 10:
                report += f"  ... 还有 {len(self.skipped) - 10} 个跳过文件\n"
        
        return report


from typing import List, Tuple
from pathlib import Path
import os

# 支持的文件格式
SUPPORTED_FORMATS = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.xls', '.csv', '.json'}

# 将文件加载函数移到模块级别（用于多进程）
def _load_single_file(file_info):
    """单个文件加载函数（优化：直接读取文件内容，避免 SimpleDirectoryReader 开销）"""
    # 屏蔽子进程中的警告和日志
    import warnings
    import logging
    warnings.filterwarnings('ignore')
    logging.getLogger('streamlit').setLevel(logging.ERROR)
    logging.getLogger('pypdf').setLevel(logging.ERROR)
    logging.getLogger('pdfminer').setLevel(logging.ERROR)
    
    fp, fname, ext = file_info
    try:
        size = os.path.getsize(fp)
        
        # 检查格式支持
        if ext not in SUPPORTED_FORMATS:
            return None, fname, 'skipped', f"不支持的格式: {ext}", 'skip'
        
        # 检查文件大小
        if size > 100 * 1024 * 1024:  # 100MB
            return None, fname, 'skipped', "文件过大 (>100MB)", 'skip'
        
        # 优化：直接读取文件内容，减少 SimpleDirectoryReader 开销
        from llama_index.core import Document
        
        # 根据文件类型快速读取
        if ext in ['.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.css', '.yaml', '.yml', '.sh', '.sql', 
                   '.log', '.ini', '.conf', '.cfg', '.csv', '.tsv', '.properties', '.env', '.rst', '.toml']:
            # 文本文件：直接读取（快速模式）
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            docs = [Document(text=text, metadata={'file_name': fname, 'file_path': fp})]
            read_mode = 'fast'
        
        elif ext in ['.xlsx', '.xls']:
            # Excel文件：快速读取（只读文本内容，不解析格式）
            try:
                import openpyxl
                wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
                text_parts = []
                for sheet in wb.worksheets[:5]:  # 只读前5个sheet
                    for row in sheet.iter_rows(max_row=1000, values_only=True):  # 每个sheet最多1000行
                        row_text = ' '.join([str(cell) for cell in row if cell is not None])
                        if row_text.strip():
                            text_parts.append(row_text)
                wb.close()
                text = '\n'.join(text_parts)
                docs = [Document(text=text, metadata={'file_name': fname, 'file_path': fp})]
                read_mode = 'fast'
            except:
                # 失败则用慢速模式
                from llama_index.core import SimpleDirectoryReader
                docs = SimpleDirectoryReader(input_files=[fp]).load_data()
                read_mode = 'slow'
        elif ext in ['.pptx', '.ppt']:
            # PowerPoint文件：读取所有文本内容
            try:
                from pptx import Presentation
                prs = Presentation(fp)
                text_parts = []
                for slide_idx, slide in enumerate(prs.slides):
                    text_parts.append(f"--- 幻灯片 {slide_idx + 1} ---")
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            text_parts.append(shape.text)
                text = '\n'.join(text_parts)
                docs = [Document(text=text, metadata={'file_name': fname, 'file_path': fp})]
                read_mode = 'fast'
            except Exception as e:
                return None, fname, 'failed', f"PPTX解析失败: {str(e)[:50]}", 'slow'
        else:
            # 其他格式：使用 SimpleDirectoryReader（慢速模式）
            from llama_index.core import SimpleDirectoryReader
            docs = SimpleDirectoryReader(input_files=[fp]).load_data()
            read_mode = 'slow'

            # 如果是PDF且内容为空，尝试 OCR（扫描版PDF）
            needs_ocr = False
            if ext == '.pdf' and docs:
                if not docs[0].text or len(docs[0].text.strip()) == 0:
                    needs_ocr = True
            
            if needs_ocr:
                try:
                    from pdf2image import convert_from_path
                    import pytesseract
                    import multiprocessing as mp
                    from concurrent.futures import ProcessPoolExecutor
                    
                    # 限制最多处理50页（多进程可以处理更多）
                    max_pages = 50
                    print(f"   🔍 检测到扫描版PDF，启动多进程OCR识别（最多{max_pages}页）...")
                    
                    images = convert_from_path(fp, first_page=1, last_page=max_pages, dpi=200)
                    print(f"   📄 共 {len(images)} 页，使用 {mp.cpu_count()} 进程并行OCR...")
                    
                    # 多进程OCR函数
                    def ocr_page(args):
                        idx, img = args
                        try:
                            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                            return idx, text.strip() if text else ""
                        except:
                            return idx, ""
                    
                    # 并行处理
                    all_text = [""] * len(images)
                    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
                        results = executor.map(ocr_page, enumerate(images, 1))
                        for idx, text in results:
                            if text:
                                all_text[idx-1] = f"--- 第{idx}页 ---\n{text}"
                    
                    # 过滤空页
                    all_text = [t for t in all_text if t]
                    
                    if all_text:
                        full_text = "\n\n".join(all_text)
                        docs = [Document(text=full_text, metadata={'file_name': fname, 'file_path': fp})]
                        read_mode = 'ocr'
                        print(f"   ✅ OCR完成: 识别了 {len(all_text)}/{len(images)} 页")
                    else:
                        return None, fname, 'failed', f"OCR未识别到文字（共{len(images)}页）", 'ocr'
                
                except Exception as e:
                    return None, fname, 'failed', f"OCR失败: {str(e)[:50]}", 'ocr'
        
        if docs:
            # 过滤掉空文档
            docs = [d for d in docs if d.text and d.text.strip()]
            if docs:
                return docs, fname, 'success', (size, len(docs)), read_mode
            else:
                return None, fname, 'failed', "文件内容为空（所有文档都是空的）", read_mode
        else:
            return None, fname, 'failed', "文件内容为空", read_mode
    
    except Exception as e:
        error_msg = str(e)
        # 简化常见错误信息
        if "trailer cannot be read" in error_msg or "invalid literal" in error_msg:
            error_msg = "PDF文件损坏"
        elif "not a zip file" in error_msg.lower():
            error_msg = "DOCX文件损坏"
        elif "RetryError" in error_msg or "AttributeError" in error_msg:
            error_msg = "文件解析失败"
        elif "Unsupported" in error_msg:
            error_msg = "不支持的文件格式"
        return None, fname, 'failed', error_msg[:100]


# 批量处理函数（模块级别，用于多进程）
def _process_batch(batch_files):
    """批量处理文件（在独立进程中运行）"""
    batch_results = []
    for file_info in batch_files:
        result = _load_single_file(file_info)
        batch_results.append(result)
    return batch_results


def scan_directory_safe(input_dir: str) -> Tuple[List, 'FileProcessResult']:
    """
    安全扫描目录，返回成功加载的文档和处理结果（多线程并行）
    
    Args:
        input_dir: 输入目录路径
    
    Returns:
        (documents, result) - 文档列表和处理结果
    """
    from llama_index.core import SimpleDirectoryReader
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import multiprocessing as mp
    
    result = FileProcessResult()
    all_docs = []
    
    # 第一步：并行扫描所有文件（优化：多线程加速）
    print(f"📁 [第 2 步] 并行扫描目录: {input_dir}")
    file_list = []
    
    # 获取所有子目录
    subdirs = [input_dir]
    try:
        subdirs.extend([os.path.join(input_dir, d) for d in os.listdir(input_dir) 
                       if os.path.isdir(os.path.join(input_dir, d)) and not d.startswith('.')])
    except:
        pass
    
    # 并行扫描函数
    def scan_dir(directory):
        local_files = []
        try:
            for root, _, filenames in os.walk(directory):
                for f in filenames:
                    if not f.startswith('.'):
                        fp = os.path.join(root, f)
                        ext = Path(f).suffix.lower()
                        local_files.append((fp, f, ext))
        except Exception as e:
            print(f"   扫描失败 {directory}: {e}")
        return local_files
    
    # 多线程并行扫描（极限配置：250 线程，冲刺 80% 资源）
    if len(subdirs) > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        scan_workers = min(250, len(subdirs))  # 250 线程
        print(f"⚡ [第 2 步] 极限模式：{scan_workers} 线程并行扫描 {len(subdirs)} 个目录（冲刺 80% 资源）")
        
        with ThreadPoolExecutor(max_workers=scan_workers) as executor:
            futures = [executor.submit(scan_dir, d) for d in subdirs]
            for future in as_completed(futures):
                file_list.extend(future.result())
    else:
        # 单目录直接扫描
        file_list = scan_dir(input_dir)
    
    print(f"✅ [第 2 步] 扫描完成: 发现 {len(file_list)} 个文件")
    
    # 第二步：多线程并行处理（动态调度，保持资源 < 80%）
    import psutil
    import time as time_module
    from queue import Queue
    from threading import Semaphore
    
    # 初始线程数（极限配置：250 线程，冲刺 80%）
    # 动态计算最优配置
    fast_formats = {'.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.css', '.yaml', '.yml', '.sh', '.sql',
                   '.log', '.ini', '.conf', '.cfg', '.csv', '.tsv', '.properties', '.env', '.rst', '.toml',
                   '.xlsx', '.xls'}  # Excel也加入快速读取
    fast_count = sum(1 for _, _, ext in file_list if ext in fast_formats)
    fast_ratio = fast_count / len(file_list) if len(file_list) > 0 else 0
    
    # 根据文件类型优化配置
    if fast_ratio > 0.5:
        # 文本文件多：高并发，大批量
        max_workers = min(500, mp.cpu_count() * 50, len(file_list))
        batch_size = 75  # 平衡批量
        mode_name = "高并发"
    elif fast_ratio > 0.3:
        # 混合文件：平衡模式
        max_workers = min(300, mp.cpu_count() * 30, len(file_list))
        batch_size = 40
        mode_name = "平衡"
    else:
        # PDF/DOCX多：保守模式
        max_workers = min(250, mp.cpu_count() * 25, len(file_list))
        batch_size = 25
        mode_name = "重文件优化"
    
    max_workers = int(max_workers)
    
    if max_workers > 1 and len(file_list) > 10:
        # batch_size已在上面动态计算，这里不再重复定义
        
        print(f"🚀 [第 3 步] {mode_name}模式: {max_workers} 进程 | 文本占比: {fast_ratio*100:.1f}%")
        print(f"📦 [第 3 步] 批量大小: {batch_size} 个/批 | 多进程突破GIL")
        
        # 使用多进程（突破GIL限制）
        import multiprocessing as mp
        import time as time_module
        
        # 设置启动方法为fork（macOS默认，避免重新导入）
        try:
             mp.set_start_method('fork', force=True)
        except RuntimeError:
             pass
        
        # 限制进程数
        actual_workers = min(max_workers, int(mp.cpu_count() * 1.2))
        print(f"💻 [第 3 步] 使用 {actual_workers} 个进程（CPU: {mp.cpu_count()}核，目标<80%）")
        
        # 统计快速/慢速读取
        fast_count = 0
        slow_count = 0
        
        # 将文件列表分批
        batches = [file_list[i:i + batch_size] for i in range(0, len(file_list), batch_size)]
        print(f"📊 [第 3 步] 总计 {len(file_list)} 个文件，分成 {len(batches)} 批")
        
        start_time = time_module.time()
        completed = 0
        
        # 使用进程池
        with mp.Pool(processes=actual_workers) as pool:
            # 使用imap_unordered获取结果
            for batch_results in pool.imap_unordered(_process_batch, batches, chunksize=1):
                try:
                    for file_result in batch_results:
                        docs, fname, status, info, read_mode = file_result if len(file_result) == 5 else (*file_result, 'unknown')
                        completed += 1
                        
                        # 统计读取模式
                        if read_mode == 'fast':
                            fast_count += 1
                        elif read_mode == 'slow':
                            slow_count += 1
                        
                        if status == 'success':
                            all_docs.extend(docs)
                            size, doc_count = info
                            result.add_success(fname, size, doc_count)
                        elif status == 'skipped':
                            result.add_skipped(fname, info)
                        else:  # failed
                            result.add_failed(fname, info)
                    
                    # 显示进度和统计（每200个文件）
                    if completed % 200 == 0:
                        elapsed = time_module.time() - start_time
                        speed = completed / elapsed if elapsed > 0 else 0
                        remaining = len(file_list) - completed
                        eta_seconds = remaining / speed if speed > 0 else 0
                        eta_minutes = eta_seconds / 60
                        
                        progress_pct = completed / len(file_list) * 100
                        print(f"📊 [第 3 步] {completed}/{len(file_list)} ({progress_pct:.1f}%) | 进程: {actual_workers}")
                        print(f"   ⚡ 快速: {fast_count} | 🐌 慢速: {slow_count} | 速度: {speed:.1f} 文件/秒 | ⏱️  预计剩余: {eta_minutes:.1f} 分钟")
                    
                    # 每处理50个文件打印简单进度
                    if completed % 50 == 0:
                        print(f"   已读取: {completed}/{len(file_list)}")
                
                except Exception as e:
                    print(f"   批次处理失败: {e}")
        
        
        # 最终统计
        print(f"\n✅ [第 3 步] 文件读取完成:")
        print(f"   ⚡ 快速读取 (直接): {fast_count} 个文件")
        print(f"   🐌 慢速读取 (解析): {slow_count} 个文件")
        if fast_count + slow_count > 0:
            print(f"   📈 快速占比: {fast_count/(fast_count+slow_count)*100:.1f}%")
    
    else:
        # 单核模式（文件少时）
        for fp, fname, ext in file_list:
            try:
                size = os.path.getsize(fp)
                
                if ext not in SUPPORTED_FORMATS:
                    result.add_skipped(fname, f"不支持的格式: {ext}")
                    continue
                
                if size > 100 * 1024 * 1024:
                    result.add_skipped(fname, "文件过大 (>100MB)")
                    continue
                
                docs = SimpleDirectoryReader(input_files=[fp]).load_data()
                if docs:
                    all_docs.extend(docs)
                    result.add_success(fname, size, len(docs))
                else:
                    result.add_failed(fname, "文件内容为空")
            
            except Exception as e:
                result.add_failed(fname, str(e)[:100])
    
    return all_docs, result

# ==========================================
# 多进程处理函数 (从 apppro.py 移动至此)
# ==========================================

def _parse_single_doc(doc_text):
    """单个文档解析（多进程安全）- 返回字典而非对象"""
    import warnings
    warnings.filterwarnings('ignore')
    
    # 文本分割 + 基础处理（优化：增大 chunk_size 减少节点数）
    chunk_size = 1024  # 从 512 增加到 1024
    chunk_overlap = 100  # 相应增加 overlap
    chunks = []
    
    # 预处理：清理和标准化文本
    doc_text = doc_text.strip()
    lines = doc_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            line = ' '.join(line.split())
            cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    
    # 分块处理
    for i in range(0, len(cleaned_text), chunk_size - chunk_overlap):
        chunk = cleaned_text[i:i + chunk_size]
        if chunk.strip():
            word_count = len(chunk.split())
            char_count = len(chunk)
            
            chunks.append({
                'text': chunk,
                'start_idx': i,
                'word_count': word_count,
                'char_count': char_count
            })
    
    return chunks

def _parse_batch_docs(doc_texts_batch):
    """批量处理文档（减少进程间通信）"""
    all_chunks = []
    for doc_text in doc_texts_batch:
        chunks = _parse_single_doc(doc_text)
        all_chunks.extend(chunks)
    return all_chunks


# ==========================================
# 向量化处理函数 (多进程)
# ==========================================

def _generate_embeddings_worker(task):
    """
    生成 embeddings 的工作进程
    task: (model_name, texts_batch, device)
    """
    import os
    # 屏蔽日志
    import logging
    logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
    
    model_name, texts, device = task
    
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        
        # 优化：使用本地缓存，避免重复下载
        embed_model = HuggingFaceEmbedding(
            model_name=model_name,
            cache_folder="./hf_cache",
            device=device,
            embed_batch_size=256  # 内部批处理
        )
        
        # 获取 embeddings
        embeddings = []
        for text in texts:
            embeddings.append(embed_model.get_text_embedding(text))
            
        return embeddings
    except Exception as e:
        return [None] * len(texts)  # 返回空以标记失败
