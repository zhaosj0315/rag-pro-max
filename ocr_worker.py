#!/usr/bin/env python3
"""
独立OCR工作进程
"""

import json
import base64
import io
from PIL import Image
import pytesseract
from concurrent.futures import ProcessPoolExecutor
import sys

def ocr_task(task_data):
    """OCR任务处理函数（模块级别）"""
    try:
        # 解码图片
        img_data = base64.b64decode(task_data["image_data"])
        img = Image.open(io.BytesIO(img_data))
        
        # OCR处理
        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(img, lang="chi_sim+eng", config=config)
        
        return {
            "task_id": task_data["task_id"],
            "page_idx": task_data["page_idx"],
            "text": text.strip() if text else ""
        }
    except Exception as e:
        return {
            "task_id": task_data["task_id"],
            "page_idx": task_data["page_idx"],
            "text": ""
        }

if __name__ == "__main__":
    # 从命令行参数获取任务文件和进程数
    task_file = sys.argv[1]
    max_workers = int(sys.argv[2])
    
    # 加载任务数据
    with open(task_file, "r") as f:
        tasks = json.load(f)
    
    # 多进程处理
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(ocr_task, tasks))
    
    # 输出结果
    print(json.dumps(results))
