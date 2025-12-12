#!/usr/bin/env python3
"""
测试OCR日志记录功能
验证文件处理统计和日志输出
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.optimized_ocr_processor import get_ocr_processor
import time

def test_ocr_logging():
    """测试OCR日志记录"""
    print("🧪 测试OCR日志记录功能")
    print("=" * 60)
    
    # 创建日志目录
    os.makedirs('app_logs', exist_ok=True)
    
    # 获取OCR处理器
    processor = get_ocr_processor()
    
    # 模拟处理一些文件
    print("📝 模拟处理文件...")
    
    # 模拟文件路径（不需要真实文件）
    fake_files = [
        'test1.jpg', 'test2.png', 'test3.pdf'
    ]
    
    # 测试初始化日志
    success = processor.initialize()
    print(f"初始化结果: {'成功' if success else '失败'}")
    
    # 显示初始统计
    print("\n📊 初始统计信息:")
    processor.print_statistics()
    
    # 模拟更新统计（不实际处理文件）
    processor.total_files_processed = 15
    processor.total_processing_time = 45.6
    
    print("\n📊 模拟处理后统计信息:")
    processor.print_statistics()
    
    # 测试统计数据获取
    stats = processor.get_statistics()
    print(f"\n📈 统计数据: {stats}")
    
    # 检查日志文件
    log_file = 'app_logs/ocr_processing.log'
    if os.path.exists(log_file):
        print(f"\n📄 日志文件已创建: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"📝 日志行数: {len(lines)}")
            if lines:
                print("📋 最新日志条目:")
                for line in lines[-3:]:  # 显示最后3行
                    print(f"   {line.strip()}")
    else:
        print(f"⚠️ 日志文件未找到: {log_file}")
    
    print("\n" + "=" * 60)
    print("✅ OCR日志记录测试完成！")

if __name__ == "__main__":
    test_ocr_logging()
