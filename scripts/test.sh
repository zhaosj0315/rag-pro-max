#!/bin/bash
# RAG Pro Max 快捷测试脚本

echo "🚀 开始运行 RAG Pro Max 出厂测试..."
echo ""

python3 tests/factory_test.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 测试通过！可以继续开发或发布。"
else
    echo ""
    echo "❌ 测试失败！请修复问题后再提交代码。"
fi

exit $exit_code
