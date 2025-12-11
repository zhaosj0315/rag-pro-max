#!/usr/bin/env python3
"""
强制启用OCR优化 - 立即生效
"""

import os
import multiprocessing as mp

def force_enable_aggressive_ocr():
    """强制启用激进OCR模式"""
    
    # 设置环境变量强制启用OCR
    os.environ['FORCE_OCR'] = 'true'
    os.environ['SKIP_OCR'] = 'false'
    os.environ['OCR_AGGRESSIVE'] = 'true'
    
    print("🚀 强制启用激进OCR模式")
    print(f"💻 CPU核心数: {mp.cpu_count()}")
    
    # 创建强制OCR配置
    config_content = f"""
# 强制OCR配置
import multiprocessing as mp
import psutil

def get_aggressive_ocr_workers():
    cpu_count = mp.cpu_count()
    # 激进模式：使用最大进程数
    return min(cpu_count, 12)

def force_ocr_all_pdfs():
    # 强制所有PDF都进行OCR处理
    return True

# 导出配置
AGGRESSIVE_WORKERS = get_aggressive_ocr_workers()
FORCE_OCR_ALL = True

print(f"⚡ 激进OCR配置: {{AGGRESSIVE_WORKERS}} 进程")
"""
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/utils/aggressive_ocr_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ 激进OCR配置已创建")

def patch_file_processor():
    """直接修补文件处理器，强制使用高性能OCR"""
    
    patch_code = '''
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
                    all_text[idx-1] = f"--- 第{idx}页 ---\\n{text}"
        
        # 过滤空页
        all_text = [t for t in all_text if t]
        
        if all_text:
            from llama_index.core import Document
            full_text = "\\n\\n".join(all_text)
            docs = [Document(text=full_text, metadata={'file_name': fname, 'file_path': fp})]
            print(f"   ✅ 强制OCR完成: {len(all_text)}/{len(images)} 页")
            return docs, fname, 'success', (len(full_text), len(docs)), 'force_ocr'
        else:
            return None, fname, 'failed', f"OCR未识别到文字（共{len(images)}页）", 'force_ocr'
            
    except Exception as e:
        return None, fname, 'failed', f"强制OCR失败: {str(e)[:50]}", 'force_ocr'

# 导出函数
__all__ = ['force_ocr_processing']
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/utils/force_ocr_patch.py', 'w') as f:
        f.write(patch_code)
    
    print("✅ 强制OCR补丁已创建")

def create_immediate_test():
    """创建立即测试脚本"""
    
    test_code = '''#!/usr/bin/env python3
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time

def cpu_intensive_task(n):
    """CPU密集型任务"""
    total = 0
    for i in range(n * 100000):
        total += i * i
    return total

def test_cpu_utilization():
    """测试CPU利用率"""
    print("🔥 CPU压力测试开始...")
    
    # 使用所有CPU核心
    workers = mp.cpu_count()
    tasks = [1000] * (workers * 2)  # 创建更多任务
    
    print(f"💪 启动 {workers} 进程处理 {len(tasks)} 个任务")
    
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(cpu_intensive_task, tasks))
    
    end_time = time.time()
    
    print(f"✅ 测试完成: {end_time - start_time:.2f}秒")
    print(f"📊 现在检查系统监控，CPU使用率应该接近100%")

if __name__ == "__main__":
    test_cpu_utilization()
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/test_cpu_stress.py', 'w') as f:
        f.write(test_code)
    
    print("✅ CPU压力测试已创建")

def main():
    print("🚀 强制OCR优化启动器")
    print("="*50)
    
    force_enable_aggressive_ocr()
    patch_file_processor()
    create_immediate_test()
    
    print("\n🎯 立即行动:")
    print("1. 运行CPU压力测试验证多核调度:")
    print("   python test_cpu_stress.py")
    print("\n2. 如果CPU能到100%，说明多核调度正常")
    print("3. 如果还是12%，说明系统限制了多进程")
    
    print("\n💡 如果多核调度正常，重启应用即可生效!")

if __name__ == "__main__":
    main()
