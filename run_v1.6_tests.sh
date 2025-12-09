#!/bin/bash

echo "=========================================="
echo "🧪 RAG Pro Max v1.6 测试套件"
echo "=========================================="
echo ""

# 1. 单元测试
echo "1️⃣ 运行单元测试..."
python tests/test_query_rewriter.py
if [ $? -ne 0 ]; then
    echo "❌ 单元测试失败"
    exit 1
fi
echo ""

# 2. 可行性测试
echo "2️⃣ 运行可行性测试..."
python tests/test_v1.6_feasibility.py
if [ $? -ne 0 ]; then
    echo "❌ 可行性测试失败"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 所有测试通过！"
echo "=========================================="
echo ""
echo "测试覆盖:"
echo "  ✅ 查询改写功能"
echo "  ✅ 文档预览功能"
echo "  ✅ 智能命名功能"
echo "  ✅ 性能测试"
echo ""
echo "v1.6 已通过完整验证，可以发布！"
