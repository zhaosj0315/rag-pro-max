#!/bin/bash
# 快速验证资源保护集成

echo "============================================================"
echo "  资源保护集成验证"
echo "============================================================"
echo ""

# 1. 检查文件修改
echo "1. 检查 apppro.py 修改..."
if grep -q "from src.utils.adaptive_throttling import get_resource_guard" src/apppro.py; then
    echo "  ✅ 导入语句存在"
else
    echo "  ❌ 导入语句缺失"
    exit 1
fi

if grep -q "resource_guard = get_resource_guard()" src/apppro.py; then
    echo "  ✅ 初始化语句存在"
else
    echo "  ❌ 初始化语句缺失"
    exit 1
fi

if grep -q "resource_guard.check_resources" src/apppro.py; then
    echo "  ✅ 资源检查调用存在"
else
    echo "  ❌ 资源检查调用缺失"
    exit 1
fi

if grep -q "resource_guard.throttler.cleanup_memory()" src/apppro.py; then
    echo "  ✅ 内存清理调用存在"
else
    echo "  ❌ 内存清理调用缺失"
    exit 1
fi

echo ""

# 2. 运行测试
echo "2. 运行集成测试..."
python3 tests/test_resource_protection.py
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "  ✅ 验证通过！资源保护已成功集成"
    echo "============================================================"
    echo ""
    echo "下一步："
    echo "  1. 启动应用: ./start.sh"
    echo "  2. 查看日志: tail -f app_logs/log_$(date +%Y%m%d).jsonl"
    echo "  3. 观察资源保护效果"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "  ❌ 验证失败"
    echo "============================================================"
    exit 1
fi
