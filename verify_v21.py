#!/usr/bin/env python3
"""
RAG Pro Max v2.1 功能验证脚本
快速验证v2.1新功能是否可用
"""

import sys
import os
import importlib.util

def test_import(module_name, description):
    """测试模块导入"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"✅ {description}: 可用")
            return True
        else:
            print(f"❌ {description}: 模块未找到")
            return False
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试基础功能...")
    
    # 测试文件监控
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        print("✅ 文件监控: watchdog 可用")
    except ImportError as e:
        print(f"❌ 文件监控: {e}")
    
    # 测试OCR
    try:
        import cv2
        import pytesseract
        from PIL import Image
        print("✅ OCR处理: opencv + pytesseract + PIL 可用")
    except ImportError as e:
        print(f"❌ OCR处理: {e}")
    
    # 测试表格解析
    try:
        import pandas as pd
        import openpyxl
        print("✅ 表格解析: pandas + openpyxl 可用")
        
        # 测试camelot（可选）
        try:
            import camelot
            print("✅ PDF表格解析: camelot 可用")
        except ImportError:
            print("⚠️  PDF表格解析: camelot 不可用（功能受限）")
            
        # 测试tabula（可选）
        try:
            import tabula
            print("✅ PDF表格解析: tabula 可用")
        except ImportError:
            print("⚠️  PDF表格解析: tabula 不可用（功能受限）")
            
    except ImportError as e:
        print(f"❌ 表格解析: {e}")
    
    # 测试多模态向量化
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ 文本向量化: sentence-transformers 可用")
    except ImportError as e:
        print(f"❌ 文本向量化: {e}")
    
    try:
        from transformers import CLIPProcessor, CLIPModel
        print("✅ 图片向量化: transformers CLIP 可用")
    except ImportError as e:
        print(f"❌ 图片向量化: {e}")

def test_system_dependencies():
    """测试系统依赖"""
    print("\n🔍 测试系统依赖...")
    
    # 测试Tesseract
    try:
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract OCR: {version}")
        else:
            print("❌ Tesseract OCR: 未正确安装")
    except Exception as e:
        print(f"❌ Tesseract OCR: {e}")
    
    # 测试中文语言包
    try:
        result = subprocess.run(['tesseract', '--list-langs'], 
                              capture_output=True, text=True, timeout=5)
        if 'chi_sim' in result.stdout:
            print("✅ 中文语言包: 已安装")
        else:
            print("⚠️  中文语言包: 未安装")
    except Exception as e:
        print(f"⚠️  中文语言包: 无法检测 ({e})")

def create_test_files():
    """创建测试文件"""
    print("\n📁 创建测试文件...")
    
    # 创建测试CSV
    try:
        import pandas as pd
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['New York', 'London', 'Tokyo']
        })
        
        os.makedirs('temp_uploads', exist_ok=True)
        test_csv = 'temp_uploads/test_table.csv'
        test_data.to_csv(test_csv, index=False)
        print(f"✅ 测试表格文件: {test_csv}")
        
        return test_csv
    except Exception as e:
        print(f"❌ 创建测试文件失败: {e}")
        return None

def test_table_parsing(test_csv):
    """测试表格解析功能"""
    if not test_csv or not os.path.exists(test_csv):
        print("⚠️  跳过表格解析测试（无测试文件）")
        return
    
    print("\n📊 测试表格解析...")
    
    try:
        import pandas as pd
        
        # 基础CSV读取
        df = pd.read_csv(test_csv)
        print(f"✅ CSV解析: {df.shape[0]}行 {df.shape[1]}列")
        
        # 数据类型推断
        dtypes = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_numeric(df[col])
                    dtypes[col] = 'numeric'
                except:
                    dtypes[col] = 'text'
            else:
                dtypes[col] = 'numeric'
        
        print(f"✅ 数据类型推断: {dtypes}")
        
    except Exception as e:
        print(f"❌ 表格解析测试失败: {e}")

def test_text_vectorization():
    """测试文本向量化"""
    print("\n🎯 测试文本向量化...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 使用轻量级模型
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # 测试向量化
        text = "这是一个测试文本"
        vector = model.encode(text)
        
        print(f"✅ 文本向量化: 维度 {len(vector)}")
        
    except Exception as e:
        print(f"❌ 文本向量化测试失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("  RAG Pro Max v2.1 功能验证")
    print("=" * 60)
    
    # 基础功能测试
    test_basic_functionality()
    
    # 系统依赖测试
    test_system_dependencies()
    
    # 创建测试文件
    test_csv = create_test_files()
    
    # 表格解析测试
    test_table_parsing(test_csv)
    
    # 文本向量化测试
    test_text_vectorization()
    
    print("\n" + "=" * 60)
    print("  验证完成")
    print("=" * 60)
    print("\n🚀 v2.1 新功能:")
    print("  📁 实时文件监控 - 自动检测文件变化")
    print("  🔍 批量OCR优化 - 并行处理图片文件")
    print("  📊 表格智能解析 - 自动识别表格结构")
    print("  🎯 多模态向量化 - 跨模态内容检索")
    print("\n启动应用: ./start.sh")

if __name__ == '__main__':
    main()
