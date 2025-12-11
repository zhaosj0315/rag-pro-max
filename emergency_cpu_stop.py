#!/usr/bin/env python3
"""
紧急CPU保护 - 立即停止所有OCR进程
"""

import os
import signal
import psutil
import subprocess

def emergency_stop_ocr():
    """紧急停止所有OCR相关进程"""
    print("🚨 紧急CPU保护启动...")
    
    stopped_processes = 0
    
    # 查找并终止OCR相关进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            
            # 检查是否是OCR相关进程
            if any(keyword in cmdline.lower() for keyword in [
                'ocr_worker', 'tesseract', 'pdf2image', 'batch_ocr'
            ]):
                print(f"🛑 终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.terminate()
                stopped_processes += 1
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if stopped_processes > 0:
        print(f"✅ 已终止 {stopped_processes} 个OCR进程")
        
        # 等待进程终止
        import time
        time.sleep(2)
        
        # 检查CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f"📊 当前CPU使用率: {cpu_usage:.1f}%")
        
        if cpu_usage < 80:
            print("✅ CPU使用率已降低，系统安全")
        else:
            print("⚠️  CPU使用率仍然较高，建议重启应用")
    else:
        print("ℹ️  未发现活跃的OCR进程")

if __name__ == "__main__":
    emergency_stop_ocr()
