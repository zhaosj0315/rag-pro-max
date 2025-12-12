#!/usr/bin/env python3
"""
OCR日志查看工具
查看OCR处理的详细日志和统计信息
"""

import os
import sys
from datetime import datetime
import argparse

def view_ocr_logs(log_file='app_logs/ocr_processing.log', lines=20):
    """查看OCR日志"""
    print("📋 OCR处理日志查看器")
    print("=" * 60)
    
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        print(f"📄 日志文件: {log_file}")
        print(f"📝 总行数: {len(all_lines)}")
        print(f"📅 文件大小: {os.path.getsize(log_file)} 字节")
        
        if all_lines:
            # 显示最新的日志
            print(f"\n📋 最新 {min(lines, len(all_lines))} 条日志:")
            print("-" * 60)
            
            for line in all_lines[-lines:]:
                line = line.strip()
                if line:
                    # 高亮重要信息
                    if "✅" in line or "成功" in line:
                        print(f"🟢 {line}")
                    elif "❌" in line or "失败" in line or "ERROR" in line:
                        print(f"🔴 {line}")
                    elif "⚠️" in line or "WARNING" in line:
                        print(f"🟡 {line}")
                    elif "📊" in line or "统计" in line:
                        print(f"📊 {line}")
                    else:
                        print(f"   {line}")
            
            # 统计信息
            print("\n" + "=" * 60)
            print("📊 日志统计分析")
            print("=" * 60)
            
            # 统计各类日志数量
            info_count = len([l for l in all_lines if "INFO" in l])
            error_count = len([l for l in all_lines if "ERROR" in l])
            warning_count = len([l for l in all_lines if "WARNING" in l])
            
            print(f"ℹ️  信息日志: {info_count} 条")
            print(f"⚠️  警告日志: {warning_count} 条")
            print(f"❌ 错误日志: {error_count} 条")
            
            # 查找处理统计
            processing_lines = [l for l in all_lines if "处理完成" in l or "累计处理" in l]
            if processing_lines:
                print(f"\n🚀 处理记录: {len(processing_lines)} 条")
                for line in processing_lines[-3:]:  # 显示最近3条
                    print(f"   {line.strip()}")
            
            # 查找初始化记录
            init_lines = [l for l in all_lines if "初始化" in l]
            if init_lines:
                print(f"\n🔧 初始化记录: {len(init_lines)} 条")
        
        else:
            print("📝 日志文件为空")
            
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='OCR日志查看工具')
    parser.add_argument('--file', '-f', default='app_logs/ocr_processing.log', 
                       help='日志文件路径')
    parser.add_argument('--lines', '-n', type=int, default=20, 
                       help='显示最新N行日志')
    parser.add_argument('--all', '-a', action='store_true', 
                       help='显示所有日志')
    
    args = parser.parse_args()
    
    lines = len(open(args.file).readlines()) if args.all and os.path.exists(args.file) else args.lines
    view_ocr_logs(args.file, lines)

if __name__ == "__main__":
    main()
