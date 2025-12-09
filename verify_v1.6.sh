#!/bin/bash

echo "=========================================="
echo "🔍 RAG Pro Max v1.6 启动验证"
echo "=========================================="
echo ""

# 1. 检查Python语法
echo "1️⃣ 检查Python语法..."
python -m py_compile src/apppro.py
if [ $? -eq 0 ]; then
    echo "   ✅ 语法检查通过"
else
    echo "   ❌ 语法错误"
    exit 1
fi
echo ""

# 2. 运行单元测试
echo "2️⃣ 运行单元测试..."
python tests/test_query_rewriter.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 单元测试通过"
else
    echo "   ❌ 单元测试失败"
    exit 1
fi
echo ""

# 3. 检查新增模块
echo "3️⃣ 检查新增模块..."
modules=(
    "src/query/query_rewriter.py"
    "src/kb/document_viewer.py"
    "src/ui/document_preview.py"
)

for module in "${modules[@]}"; do
    if [ -f "$module" ]; then
        echo "   ✅ $module"
    else
        echo "   ❌ $module 不存在"
        exit 1
    fi
done
echo ""

# 4. 检查文档
echo "4️⃣ 检查文档..."
docs=(
    "docs/V1.6_FEATURES.md"
    "docs/V1.6_IMPLEMENTATION.md"
    "V1.6_COMPLETION_REPORT.md"
    "QUICKSTART_V1.6.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✅ $doc"
    else
        echo "   ❌ $doc 不存在"
        exit 1
    fi
done
echo ""

# 5. 清理缓存
echo "5️⃣ 清理Python缓存..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "   ✅ 缓存已清理"
echo ""

echo "=========================================="
echo "✅ v1.6 验证完成！可以启动应用"
echo "=========================================="
echo ""
echo "启动命令："
echo "  streamlit run src/apppro.py"
echo ""
