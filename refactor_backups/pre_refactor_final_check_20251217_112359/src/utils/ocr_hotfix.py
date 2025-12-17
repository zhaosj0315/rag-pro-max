
# OCR高性能补丁 - 立即替换
def _ocr_page_optimized(args):
    """优化的OCR页面处理"""
    import pytesseract
    import time
    
    idx, img = args
    try:
        # 高性能OCR配置
        config = '--oem 3 --psm 6'
        
        # 多语言识别
        text = pytesseract.image_to_string(img, lang='chi_sim+eng', config=config)
        
        # 快速文本清理
        if text:
            text = text.strip()
            # 移除过短的行
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
            text = '\n'.join(lines)
        
        return idx, text if text else ""
    except Exception as e:
        return idx, ""

# 高性能批量OCR处理
def process_pdf_with_max_performance(file_path):
    """使用最大性能处理PDF"""
    try:
        from pdf2image import convert_from_path
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing as mp
        
        print(f"🚀 高性能OCR处理: {file_path}")
        
        # 转换PDF为图片
        images = convert_from_path(file_path, dpi=200)
        
        # 使用最大进程数
        max_workers = min(mp.cpu_count(), len(images))
        print(f"💪 激进模式: {len(images)}页，{max_workers}进程，目标CPU 90%+")
        
        # 强制并行OCR
        all_text = [""] * len(images)
        
        import time
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(_ocr_page_optimized, enumerate(images, 1))
            for idx, text in results:
                if text:
                    all_text[idx-1] = f"--- 第{idx}页 ---\n{text}"
        
        end_time = time.time()
        duration = end_time - start_time
        pages_per_sec = len(images) / duration if duration > 0 else 0
        
        print(f"✅ 高性能OCR完成: {duration:.1f}秒, {pages_per_sec:.1f}页/秒")
        
        # 过滤空页
        all_text = [t for t in all_text if t]
        
        return all_text
        
    except Exception as e:
        print(f"❌ 高性能OCR失败: {e}")
        return []
