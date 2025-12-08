#!/bin/bash
# RAG Pro Max 安全启动脚本
# 启动前自动运行出厂测试，防止运行有问题的代码

echo "🔍 启动前检测..."
echo ""

# 运行出厂测试
python3 tests/factory_test.py

# 检查测试结果
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 出厂测试失败！应用未启动"
    echo "💡 请修复问题后再启动"
    exit 1
fi

echo ""
echo "✅ 测试通过！正在启动应用..."
echo ""

# 启动应用（设置 PYTHONPATH 以支持绝对导入）
export PYTHONPATH="${PWD}:${PYTHONPATH}"
streamlit run src/apppro.py
