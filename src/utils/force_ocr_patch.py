
# 强制OCR处理补丁
def force_ocr_processing(fp, fname):
    """强制OCR处理，无论PDF是否为空"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing as mp
        
        print(f"   🚀 强制OCR处理: {fname}")
        
        # 转换PDF为图片
        images = convert_from_path(fp, dpi=200)
        
        # 使用最大进程数
        max_workers = min(mp.cpu_count(), len(images), 12)
        print(f"   💪 激进模式: {len(images)}页，{max_workers}进程")
        
        # 强制并行OCR
        all_text = [""] * len(images)
        
        def ocr_page_aggressive(args):
            idx, img = args
            try:
                import pytesseract
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                return idx, text.strip() if text else ""
            except:
                return idx, ""
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(ocr_page_aggressive, enumerate(images, 1))
            for idx, text in results:
                if text:
                    all_text[idx-1] = f"--- 第{idx}页 ---\n{text}"
        
        # 过滤空页
        all_text = [t for t in all_text if t]
        
        if all_text:
            from llama_index.core import Document
            full_text = "\n\n".join(all_text)
            docs = [Document(text=full_text, metadata={'file_name': fname, 'file_path': fp})]
            print(f"   ✅ 强制OCR完成: {len(all_text)}/{len(images)} 页")
            return docs, fname, 'success', (len(full_text), len(docs)), 'force_ocr'
        else:
            return None, fname, 'failed', f"OCR未识别到文字（共{len(images)}页）", 'force_ocr'
            
    except Exception as e:
        return None, fname, 'failed', f"强制OCR失败: {str(e)[:50]}", 'force_ocr'

# 导出函数
__all__ = ['force_ocr_processing']
