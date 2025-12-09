#!/bin/bash

echo "=========================================="
echo "  RAG Pro Max v1.4.4 版本验证"
echo "=========================================="
echo ""

# 1. 检查版本号
echo "1. 检查版本号..."
if grep -q "version-1.4.4" README.md; then
    echo "   ✅ README.md 版本号正确"
else
    echo "   ❌ README.md 版本号错误"
    exit 1
fi

# 2. 检查发布说明
echo "2. 检查发布说明..."
if [ -f "RELEASE_v1.4.4.md" ]; then
    echo "   ✅ RELEASE_v1.4.4.md 存在"
else
    echo "   ❌ RELEASE_v1.4.4.md 不存在"
    exit 1
fi

# 3. 运行可行性测试
echo "3. 运行可行性测试..."
python3 tests/test_v1.4.4_feasibility.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 可行性测试通过"
else
    echo "   ❌ 可行性测试失败"
    exit 1
fi

# 4. 运行出厂测试
echo "4. 运行出厂测试..."
python3 tests/factory_test.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 出厂测试通过"
else
    echo "   ❌ 出厂测试失败"
    exit 1
fi

# 5. 检查语法
echo "5. 检查语法..."
python3 -m py_compile src/apppro.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ apppro.py 语法正确"
else
    echo "   ❌ apppro.py 语法错误"
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ v1.4.4 验证通过！可以发布。"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. git add ."
echo "  2. git commit -m 'Release v1.4.4'"
echo "  3. git tag v1.4.4"
echo "  4. git push origin main --tags"
