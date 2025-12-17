#!/bin/bash

# RAG Pro Max v2.1 安装脚本
# 安装新功能依赖并验证

set -e

echo "============================================================"
echo "  RAG Pro Max v2.1 功能安装"
echo "============================================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要 >= 3.8，当前: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p src/monitoring
mkdir -p src/processors
mkdir -p temp_uploads

# 安装v2.1依赖
echo "📦 安装v2.1新功能依赖..."

# 基础依赖
pip3 install watchdog>=3.0.0
pip3 install opencv-python>=4.8.0
pip3 install pytesseract>=0.3.10
pip3 install Pillow>=10.0.0

# 表格处理依赖
echo "📊 安装表格处理依赖..."
pip3 install tabula-py>=2.8.0
pip3 install openpyxl>=3.1.0

# 尝试安装camelot-py（可能失败）
echo "🐪 尝试安装camelot-py..."
pip3 install camelot-py>=0.10.1 || echo "⚠️  camelot-py安装失败，PDF表格解析功能受限"

# 多模态依赖（修复版）
echo "🎯 安装多模态依赖..."
pip3 install transformers>=4.35.0
pip3 install sentence-transformers>=2.2.0

# 图像处理增强
pip3 install scikit-image>=0.21.0
pip3 install matplotlib>=3.7.0

echo "✅ 依赖安装完成"

# 检查系统依赖
echo "🔍 检查系统依赖..."

# 检查Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR未安装"
    echo "macOS安装: brew install tesseract tesseract-lang"
    echo "Ubuntu安装: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim"
else
    echo "✅ Tesseract OCR已安装"
fi

# 检查中文语言包
if tesseract --list-langs 2>/dev/null | grep -q "chi_sim"; then
    echo "✅ 中文语言包已安装"
else
    echo "⚠️  中文语言包未安装"
    echo "请安装: brew install tesseract-lang (macOS)"
fi

# 运行v2.1功能测试
echo "🧪 运行v2.1功能验证..."
if python3 verify_v21.py; then
    echo "✅ v2.1功能验证通过"
else
    echo "⚠️  部分v2.1功能可能不可用"
fi

echo ""
echo "============================================================"
echo "  v2.1 安装完成"
echo "============================================================"
echo ""
echo "🚀 新功能:"
echo "  📁 实时文件监控 - 自动检测文件变化"
echo "  🔍 批量OCR优化 - 并行处理图片文件"
echo "  📊 表格智能解析 - 自动识别表格结构"
echo "  🎯 多模态向量化 - 跨模态内容检索"
echo ""
echo "启动应用: ./start.sh"
echo "查看文档: docs/V2.1_FEATURES.md"
echo ""
