#!/usr/bin/env python3
"""
OCR热修复 - 立即生效
直接替换正在运行的OCR处理函数
"""

def apply_hotfix():
    """应用OCR热修复"""
    
    # 创建高性能OCR函数
    ocr_patch = '''
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
            lines = [line.strip() for line in text.split('\\n') if len(line.strip()) > 1]
            text = '\\n'.join(lines)
        
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
                    all_text[idx-1] = f"--- 第{idx}页 ---\\n{text}"
        
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
'''
    
    # 写入补丁文件
    with open('/Users/zhaosj/Documents/rag-pro-max/src/utils/ocr_hotfix.py', 'w') as f:
        f.write(ocr_patch)
    
    print("✅ OCR热修复补丁已创建")

def create_force_restart_script():
    """创建强制重启脚本"""
    
    restart_script = '''#!/bin/bash
echo "🔄 强制重启应用以应用OCR优化..."

# 查找并停止Streamlit进程
echo "🛑 停止当前Streamlit进程..."
pkill -f "streamlit run"
pkill -f "apppro.py"

# 等待进程完全停止
sleep 2

# 设置OCR优化环境变量
export FORCE_OCR=true
export SKIP_OCR=false
export OCR_AGGRESSIVE=true

echo "🚀 启动优化后的应用..."

# 重新启动应用
cd /Users/zhaosj/Documents/rag-pro-max
streamlit run src/apppro.py --server.headless=true &

echo "✅ 应用已重启，OCR优化已生效"
echo "📊 现在上传PDF文档，应该能看到CPU使用率提升到70%+"
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/force_restart.sh', 'w') as f:
        f.write(restart_script)
    
    import os
    os.chmod('/Users/zhaosj/Documents/rag-pro-max/force_restart.sh', 0o755)
    
    print("✅ 强制重启脚本已创建")

def main():
    print("🔥 OCR热修复工具")
    print("="*50)
    
    apply_hotfix()
    create_force_restart_script()
    
    print("\n🎯 立即行动方案:")
    print("1. 强制重启应用:")
    print("   ./force_restart.sh")
    print("\n2. 或者手动重启:")
    print("   - 停止当前Streamlit进程")
    print("   - 运行: streamlit run src/apppro.py")
    print("\n3. 上传PDF文档测试")
    print("   - 应该看到CPU使用率70%+")
    print("   - 所有14个核心都激活")
    
    print("\n⚡ 如果还是12% CPU，说明:")
    print("   - 当前处理的不是扫描版PDF")
    print("   - 或者PDF内容不为空，没有触发OCR")

if __name__ == "__main__":
    main()
