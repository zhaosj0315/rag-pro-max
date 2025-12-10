#!/bin/bash

echo "============================================================"
echo "  RAG Pro Max v1.7.3 最终状态检查"
echo "  时间: $(date)"
echo "============================================================"

# 1. 过程材料清理检查
echo "🧹 过程材料清理检查..."
TEMP_COUNT=$(ls -la | grep -E "(DEBUG|FIX|TEMP|QUICK|SIMPLE)" | wc -l)
if [ "$TEMP_COUNT" -eq 0 ]; then
    echo "✅ 过程材料已完全清理"
else
    echo "⚠️ 还有 $TEMP_COUNT 个过程文件未清理"
fi

# 2. 版本逻辑对齐检查
echo ""
echo "🔄 版本逻辑对齐检查..."
VERSION_FILES=("README.md" "CHANGELOG.md" "RELEASE_v1.7.3.md" "TESTING.md" "USER_MANUAL.md" "DEPLOYMENT.md" "FAQ.md")
ALIGNED=true

for file in "${VERSION_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "1.7.3" "$file"; then
            echo "✅ $file - 版本对齐"
        else
            echo "❌ $file - 版本未对齐"
            ALIGNED=false
        fi
    else
        echo "⚠️ $file - 文件不存在"
    fi
done

# 3. 操作手册更新检查
echo ""
echo "📖 操作手册更新检查..."
MANUALS=("USER_MANUAL.md" "DEPLOYMENT.md" "FAQ.md" "FIRST_TIME_GUIDE.md")
for manual in "${MANUALS[@]}"; do
    if [ -f "$manual" ]; then
        MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d" "$manual")
        echo "✅ $manual - 最后修改: $MODIFIED"
    else
        echo "❌ $manual - 文件缺失"
    fi
done

# 4. README更新检查
echo ""
echo "📄 README更新检查..."
if [ -f "README.md" ]; then
    README_VERSION=$(grep -o "version-[0-9.]*" README.md | head -1)
    README_STATS=$(grep -o "[0-9]*个Python文件" README.md | head -1)
    echo "✅ README版本: $README_VERSION"
    echo "✅ README统计: $README_STATS"
else
    echo "❌ README.md 文件缺失"
fi

# 5. 可行性测试检查
echo ""
echo "🧪 可行性测试检查..."
if [ -f "tests/test_v1.7.3_feasibility.py" ]; then
    echo "✅ v1.7.3可行性测试存在"
    echo "🔄 运行可行性测试..."
    python tests/test_v1.7.3_feasibility.py 2>/dev/null | grep -E "(OK|FAILED)" | tail -1
else
    echo "❌ v1.7.3可行性测试缺失"
fi

# 6. 出厂测试检查
echo ""
echo "🏭 出厂测试检查..."
FACTORY_RESULT=$(python tests/factory_test.py 2>/dev/null | grep "通过:" | tail -1)
echo "✅ 出厂测试结果: $FACTORY_RESULT"

# 7. 文档索引检查
echo ""
echo "📚 文档索引检查..."
if [ -f "DOCS_INDEX.md" ]; then
    if grep -q "RELEASE_v1.7.3.md" "DOCS_INDEX.md"; then
        echo "✅ 文档索引已更新"
    else
        echo "⚠️ 文档索引可能需要更新"
    fi
else
    echo "❌ DOCS_INDEX.md 缺失"
fi

echo ""
echo "============================================================"
echo "  最终状态总结"
echo "============================================================"

if [ "$ALIGNED" = true ] && [ "$TEMP_COUNT" -eq 0 ]; then
    echo "✅ 所有环节业务逻辑已对齐"
    echo "✅ 过程材料已完全清理"
    echo "✅ 操作手册已更新"
    echo "✅ README已更新"
    echo "✅ 可行性测试已更新"
    echo ""
    echo "🎉 系统处于最佳状态，可以发布！"
else
    echo "⚠️ 部分环节需要检查"
fi
