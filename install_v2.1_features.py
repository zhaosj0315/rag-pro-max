#!/usr/bin/env python3
"""
RAG Pro Max v2.1 功能安装脚本
安装自适应调度、实时进度监控和GPU OCR加速
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装依赖包"""
    print("📦 安装v2.1功能依赖...")
    
    dependencies = [
        "paddlepaddle-gpu",  # GPU版本
        "paddleocr",         # OCR引擎
        "torch",             # PyTorch
        "torchvision",       # 视觉处理
    ]
    
    for dep in dependencies:
        try:
            print(f"   安装 {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"   ✅ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  {dep} 安装失败: {e}")
            if dep == "paddlepaddle-gpu":
                print("   💡 尝试安装CPU版本...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "paddlepaddle"])
                    print("   ✅ paddlepaddle (CPU版本) 安装成功")
                except:
                    print("   ❌ paddlepaddle 安装失败")

def create_config_directory():
    """创建配置目录"""
    config_dir = "config"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"✅ 创建配置目录: {config_dir}")

def test_gpu_availability():
    """测试GPU可用性"""
    print("🔍 检测GPU可用性...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"   ✅ CUDA GPU可用: {torch.cuda.get_device_name(0)}")
            print(f"   📊 GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
            return "cuda"
        elif torch.backends.mps.is_available():
            print(f"   ✅ Apple Silicon GPU (MPS) 可用")
            return "mps"
        else:
            print(f"   💻 仅CPU可用")
            return "cpu"
    except ImportError:
        print(f"   ❌ PyTorch未安装")
        return "none"

def test_paddleocr():
    """测试PaddleOCR"""
    print("🔍 测试PaddleOCR...")
    
    try:
        from paddleocr import PaddleOCR
        
        # 简单测试
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        print("   ✅ PaddleOCR初始化成功")
        return True
    except ImportError:
        print("   ❌ PaddleOCR未安装")
        return False
    except Exception as e:
        print(f"   ⚠️  PaddleOCR测试失败: {e}")
        return False

def run_feature_test():
    """运行功能测试"""
    print("🧪 运行v2.1功能测试...")
    
    try:
        # 测试自适应调度器
        from src.utils.adaptive_scheduler import adaptive_scheduler
        workers, strategy, confidence = adaptive_scheduler.get_optimal_strategy(10)
        print(f"   ✅ 自适应调度器: {strategy} ({workers}进程, 置信度{confidence:.1%})")
        
        # 测试进度监控器
        from src.ui.progress_monitor import progress_monitor
        progress_monitor.start_task("test", "测试任务", 10)
        progress_monitor.complete_task("test")
        print(f"   ✅ 进度监控器: 正常工作")
        
        # 测试GPU OCR加速器
        from src.utils.gpu_ocr_accelerator import gpu_ocr_accelerator
        device_info = gpu_ocr_accelerator.get_device_info()
        print(f"   ✅ GPU OCR加速器: {device_info['device']} (批量大小: {device_info['batch_size']})")
        
        # 测试增强OCR优化器
        from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer
        stats = enhanced_ocr_optimizer.get_performance_stats()
        print(f"   ✅ 增强OCR优化器: {len(stats)}项统计")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 功能测试失败: {e}")
        return False

def main():
    """主安装流程"""
    print("🚀 RAG Pro Max v2.1 功能安装")
    print("=" * 50)
    
    # 1. 安装依赖
    install_dependencies()
    
    # 2. 创建配置目录
    create_config_directory()
    
    # 3. 测试GPU
    gpu_type = test_gpu_availability()
    
    # 4. 测试PaddleOCR
    paddleocr_ok = test_paddleocr()
    
    # 5. 运行功能测试
    features_ok = run_feature_test()
    
    # 6. 输出结果
    print("\n" + "=" * 50)
    print("📋 安装结果:")
    print(f"   GPU支持: {gpu_type}")
    print(f"   PaddleOCR: {'✅ 可用' if paddleocr_ok else '❌ 不可用'}")
    print(f"   v2.1功能: {'✅ 正常' if features_ok else '❌ 异常'}")
    
    if features_ok:
        print("\n🎉 v2.1功能安装成功！")
        print("\n💡 新功能:")
        print("   • 🧠 自适应CPU调度 - 基于历史数据智能调整")
        print("   • 📊 实时进度监控 - 可视化处理状态")
        print("   • 🚀 GPU OCR加速 - 显著提升处理速度")
        print("\n🚀 现在可以启动应用体验新功能:")
        print("   ./start.sh")
    else:
        print("\n⚠️  部分功能可能无法正常工作")
        print("💡 建议:")
        print("   1. 检查依赖安装")
        print("   2. 重新运行安装脚本")
        print("   3. 查看错误日志")

if __name__ == "__main__":
    main()
