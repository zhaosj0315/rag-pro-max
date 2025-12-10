#!/usr/bin/env python3
"""
RAG Pro Max v2.1 功能演示
展示新功能的基本用法
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path

def demo_file_watcher():
    """演示文件监控功能"""
    print("=" * 50)
    print("📁 文件监控功能演示")
    print("=" * 50)
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class DemoHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    print(f"🔄 文件已修改: {event.src_path}")
            
            def on_created(self, event):
                if not event.is_directory:
                    print(f"✨ 文件已创建: {event.src_path}")
        
        # 创建监控器
        observer = Observer()
        handler = DemoHandler()
        
        # 监控当前目录
        watch_path = "./temp_uploads"
        os.makedirs(watch_path, exist_ok=True)
        
        observer.schedule(handler, watch_path, recursive=False)
        observer.start()
        
        print(f"🔍 开始监控目录: {watch_path}")
        print("📝 创建测试文件...")
        
        # 创建测试文件
        test_file = os.path.join(watch_path, "demo_file.txt")
        with open(test_file, "w") as f:
            f.write("这是一个测试文件")
        
        time.sleep(1)
        
        # 修改文件
        with open(test_file, "a") as f:
            f.write("\n添加新内容")
        
        time.sleep(1)
        
        observer.stop()
        observer.join()
        
        print("✅ 文件监控演示完成")
        
    except Exception as e:
        print(f"❌ 文件监控演示失败: {e}")

def demo_table_parsing():
    """演示表格解析功能"""
    print("\n" + "=" * 50)
    print("📊 表格解析功能演示")
    print("=" * 50)
    
    try:
        # 创建示例表格
        data = {
            '产品名称': ['iPhone 15', 'MacBook Pro', 'iPad Air', 'Apple Watch'],
            '价格': [5999, 14999, 4599, 2999],
            '库存': [150, 80, 200, 300],
            '类别': ['手机', '笔记本', '平板', '手表'],
            '评分': [4.8, 4.9, 4.7, 4.6]
        }
        
        df = pd.DataFrame(data)
        
        print("📋 原始表格数据:")
        print(df.to_string(index=False))
        
        # 结构分析
        print(f"\n📏 表格结构:")
        print(f"  行数: {len(df)}")
        print(f"  列数: {len(df.columns)}")
        print(f"  列名: {list(df.columns)}")
        
        # 数据类型分析
        print(f"\n🔍 数据类型分析:")
        for col in df.columns:
            dtype = 'numeric' if pd.api.types.is_numeric_dtype(df[col]) else 'text'
            unique_ratio = len(df[col].unique()) / len(df)
            if unique_ratio < 0.5 and dtype == 'text':
                dtype = 'categorical'
            print(f"  {col}: {dtype}")
        
        # 统计信息
        print(f"\n📈 数值列统计:")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            stats = df[col].describe()
            print(f"  {col}: 均值={stats['mean']:.1f}, 范围=[{stats['min']:.0f}, {stats['max']:.0f}]")
        
        # 保存为CSV
        csv_path = "temp_uploads/demo_table.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n💾 表格已保存: {csv_path}")
        
        print("✅ 表格解析演示完成")
        
    except Exception as e:
        print(f"❌ 表格解析演示失败: {e}")

def demo_text_vectorization():
    """演示文本向量化功能"""
    print("\n" + "=" * 50)
    print("🎯 文本向量化功能演示")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 加载模型
        print("🔄 加载文本向量化模型...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # 测试文本
        texts = [
            "苹果公司发布了新款iPhone",
            "Apple released a new iPhone model",
            "今天天气很好，适合出门",
            "The weather is nice today",
            "人工智能技术发展迅速"
        ]
        
        print("\n📝 测试文本:")
        for i, text in enumerate(texts, 1):
            print(f"  {i}. {text}")
        
        # 向量化
        print("\n🔄 正在向量化...")
        vectors = model.encode(texts)
        
        print(f"✅ 向量化完成:")
        print(f"  向量维度: {vectors.shape[1]}")
        print(f"  文本数量: {vectors.shape[0]}")
        
        # 计算相似度
        print(f"\n🔍 相似度分析:")
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarity_matrix = cosine_similarity(vectors)
        
        # 找出最相似的文本对
        max_sim = 0
        max_pair = (0, 0)
        for i in range(len(texts)):
            for j in range(i+1, len(texts)):
                sim = similarity_matrix[i][j]
                if sim > max_sim:
                    max_sim = sim
                    max_pair = (i, j)
        
        print(f"  最相似的文本对:")
        print(f"    文本1: {texts[max_pair[0]]}")
        print(f"    文本2: {texts[max_pair[1]]}")
        print(f"    相似度: {max_sim:.3f}")
        
        print("✅ 文本向量化演示完成")
        
    except Exception as e:
        print(f"❌ 文本向量化演示失败: {e}")

def demo_ocr_preprocessing():
    """演示OCR预处理功能"""
    print("\n" + "=" * 50)
    print("🔍 OCR预处理功能演示")
    print("=" * 50)
    
    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageEnhance, ImageFilter
        
        # 创建模拟图片（带噪声的文字）
        print("🖼️  创建模拟图片...")
        
        # 创建白色背景
        img = np.ones((200, 400, 3), dtype=np.uint8) * 255
        
        # 添加文字（模拟）
        cv2.putText(img, "Hello World", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        # 添加噪声
        noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
        noisy_img = cv2.add(img, noise)
        
        print("🔧 图片预处理步骤:")
        
        # 1. 转灰度
        gray = cv2.cvtColor(noisy_img, cv2.COLOR_BGR2GRAY)
        print("  ✅ 转换为灰度图")
        
        # 2. 去噪
        denoised = cv2.GaussianBlur(gray, (3, 3), 0)
        print("  ✅ 高斯模糊去噪")
        
        # 3. 二值化
        _, binary = cv2.threshold(denoised, 0, 255, 
                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("  ✅ 自适应二值化")
        
        # 4. 形态学操作
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        print("  ✅ 形态学处理")
        
        # 保存处理结果
        os.makedirs("temp_uploads", exist_ok=True)
        cv2.imwrite("temp_uploads/demo_original.png", noisy_img)
        cv2.imwrite("temp_uploads/demo_processed.png", processed)
        
        print(f"\n💾 图片已保存:")
        print(f"  原图: temp_uploads/demo_original.png")
        print(f"  处理后: temp_uploads/demo_processed.png")
        
        print("✅ OCR预处理演示完成")
        
    except Exception as e:
        print(f"❌ OCR预处理演示失败: {e}")

def main():
    """主函数"""
    print("🚀 RAG Pro Max v2.1 功能演示")
    print("展示四大新功能的基本用法\n")
    
    # 创建临时目录
    os.makedirs("temp_uploads", exist_ok=True)
    
    # 演示各功能
    demo_file_watcher()
    demo_table_parsing()
    demo_text_vectorization()
    demo_ocr_preprocessing()
    
    print("\n" + "=" * 60)
    print("🎉 所有功能演示完成！")
    print("=" * 60)
    print("\n📁 生成的演示文件:")
    
    demo_files = [
        "temp_uploads/demo_file.txt",
        "temp_uploads/demo_table.csv", 
        "temp_uploads/demo_original.png",
        "temp_uploads/demo_processed.png"
    ]
    
    for file_path in demo_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  📄 {file_path} ({size} bytes)")
    
    print(f"\n🚀 启动完整应用: ./start.sh")
    print(f"📚 查看详细文档: docs/V2.1_FEATURES.md")

if __name__ == '__main__':
    main()
