#!/bin/bash

echo "🚀 开始打包 RAG Pro Max..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python 版本: $python_version"

# 安装 PyInstaller
echo "📦 安装 PyInstaller..."
pip install pyinstaller

# 清理旧文件
echo "🧹 清理旧文件..."
rm -rf build dist

# 打包
echo "⚙️  开始打包..."
pyinstaller RAG_Pro_Max.spec --clean --noconfirm

# 检查结果
if [ -f "dist/RAG_Pro_Max.app/Contents/MacOS/RAG_Pro_Max" ]; then
    echo ""
    echo "✅ 打包成功！应用位于 dist/RAG_Pro_Max.app"
    echo ""
    
    # 验证依赖
    echo "🔍 验证打包的依赖..."
    ./dist/RAG_Pro_Max.app/Contents/MacOS/RAG_Pro_Max -c "import sys; sys.path.insert(0, '.'); exec(open('verify_package.py').read())" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 所有依赖验证通过！"
    else
        echo ""
        echo "⚠️  依赖验证失败，但应用已打包"
    fi
    
    echo ""
    echo "📝 测试方法："
    echo "  1. 直接运行（查看详细日志）："
    echo "     ./dist/RAG_Pro_Max.app/Contents/MacOS/RAG_Pro_Max"
    echo ""
    echo "  2. 双击打开："
    echo "     open dist/RAG_Pro_Max.app"
    echo ""
    echo "  3. 查看启动日志："
    echo "     cat dist/RAG_Pro_Max.app/Contents/MacOS/launch_*.log"
    echo ""
else
    echo "❌ 打包失败"
    echo ""
    echo "请检查错误信息，常见问题："
    echo "  1. 缺少依赖包：pip install -r requirements.txt"
    echo "  2. PyInstaller 版本问题：pip install --upgrade pyinstaller"
    echo "  3. 查看详细错误：pyinstaller RAG_Pro_Max.spec --clean --noconfirm --log-level DEBUG"
    exit 1
fi
