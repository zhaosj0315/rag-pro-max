
# 强制OCR配置
import psutil
import multiprocessing as mp

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

print(f"⚡ 激进OCR配置: {AGGRESSIVE_WORKERS} 进程")
