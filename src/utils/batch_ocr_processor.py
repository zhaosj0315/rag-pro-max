from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
批量OCR处理器
将所有扫描版PDF的OCR任务统一处理，避免重复创建进程池
"""

from typing import List, Dict
import time

class BatchOCRProcessor:
    """批量OCR处理器"""
    
    def __init__(self):
        self.ocr_tasks = []  # 待处理的OCR任务
        self.results = {}    # OCR结果缓存
        
    def add_ocr_task(self, file_path: str, images: List, task_id: str):
        """添加OCR任务到批量队列"""
        for idx, img in enumerate(images):
            self.ocr_tasks.append({
                'task_id': task_id,
                'file_path': file_path,
                'page_idx': idx + 1,
                'image': img
            })
    
    def process_all_ocr_tasks(self) -> Dict:
        """批量处理所有OCR任务 - 带CPU保护"""
        if not self.ocr_tasks:
            return {}
        
        logger.info(f"🚀 批量OCR处理: {len(self.ocr_tasks)} 个页面，来自 {len(set(t['task_id'] for t in self.ocr_tasks))} 个文件")
        
        # 动态调整进程数
        from src.utils.ocr_optimizer import ocr_optimizer
        max_workers, strategy = ocr_optimizer.get_optimal_workers(len(self.ocr_tasks))
        
        logger.info(f"📊 {strategy}，使用 {max_workers} 进程并行处理")
        logger.info(f"🛡️  CPU保护已启用，确保系统稳定运行")
        
        # 启动CPU监控
        ocr_optimizer.start_cpu_monitoring(max_workers)
        
        start_time = time.time()
        temp_file = None  # 初始化临时文件变量
        
        try:
            # 使用独立OCR工作脚本
            import subprocess
            import json
            import tempfile
            import os
            
            # 创建临时文件保存任务数据
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                task_data = []
                for task in self.ocr_tasks:
                    # 将PIL Image转换为可序列化的格式
                    import io
                    import base64
                    img_buffer = io.BytesIO()
                    task['image'].save(img_buffer, format='PNG')
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                    
                    task_data.append({
                        'task_id': task['task_id'],
                        'page_idx': task['page_idx'],
                        'image_data': img_base64
                    })
                
                json.dump(task_data, f)
                temp_file = f.name
            
            # 启动独立OCR工作进程
            cmd = ['python', 'ocr_worker.py', temp_file, str(max_workers)]
            
            # 执行独立进程
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd='/Users/zhaosj/Documents/rag-pro-max')  # 减少超时时间
            
            # 检查紧急停止
            if ocr_optimizer.should_emergency_stop():
                logger.info(f"🛑 检测到紧急停止信号，终止OCR处理")
                return self.results
            
            if result.returncode == 0:
                # 解析结果
                ocr_results = json.loads(result.stdout.strip())
                
                # 整理结果
                for result_item in ocr_results:
                    task_id = result_item['task_id']
                    page_idx = result_item['page_idx']
                    text = result_item['text']
                    
                    if task_id not in self.results:
                        self.results[task_id] = {}
                    
                    self.results[task_id][page_idx] = text
                
                elapsed = time.time() - start_time
                pages_per_sec = len(self.ocr_tasks) / elapsed if elapsed > 0 else 0
                
                logger.info(f"OCR处理速度: {pages_per_sec:.1f}页/秒")
                logger.info(f"🛡️  CPU保护运行正常，系统保持稳定")
                
            else:
                logger.error(result.stderr)
                
        except Exception as e:
            logger.error(e)
        finally:
            # 停止CPU监控
            from src.utils.ocr_optimizer import ocr_optimizer
            ocr_optimizer.stop_cpu_monitoring()
            
            # 清理临时文件
            if temp_file:
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        # 清空任务队列
        self.ocr_tasks = []
        
        return self.results
    
    def get_file_result(self, task_id: str) -> List[str]:
        """获取指定文件的OCR结果"""
        if task_id not in self.results:
            return []
        
        # 按页码排序
        pages = self.results[task_id]
        sorted_pages = sorted(pages.items())
        
        # 组装文本
        all_text = []
        for page_idx, text in sorted_pages:
            if text:
                all_text.append(f"--- 第{page_idx}页 ---\n{text}")
        
        return all_text

# 全局批量OCR处理器
batch_ocr_processor = BatchOCRProcessor()

def _batch_ocr_page(args):
    """批量OCR单页处理（模块级函数）"""
    import pytesseract
    
    page_idx, img = args
    try:
        # 优化OCR配置
        config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz一二三四五六七八九十百千万亿零壹贰叁肆伍陆柒捌玖拾佰仟萬億'
        
        # 多语言识别
        text = pytesseract.image_to_string(img, lang='chi_sim+eng', config=config)
        
        # 清理文本
        if text:
            text = text.strip()
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
            text = '\n'.join(lines)
        
        return page_idx, text if text else ""
    except Exception as e:
        return page_idx, ""
