#!/bin/bash

# 文档同步检查脚本
# 检查代码和文档是否保持一致

echo "📋 RAG Pro Max 文档同步检查"
echo "================================"

# 检查版本一致性
echo "🔍 检查版本信息..."

# 从README获取版本
README_VERSION=$(grep -o 'version-[0-9]\+\.[0-9]\+\.[0-9]\+' README.md | head -1 | cut -d'-' -f2)
echo "📖 README版本: $README_VERSION"

# 从API获取版本
API_VERSION=$(grep 'version=' src/api/fastapi_server.py | grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' | tr -d '"')
echo "🔌 API版本: $API_VERSION"

# 检查版本是否一致
if [ "$README_VERSION" = "$API_VERSION" ]; then
    echo "✅ 版本信息一致: $README_VERSION"
else
    echo "❌ 版本信息不一致!"
    echo "   README: $README_VERSION"
    echo "   API: $API_VERSION"
fi

echo ""

# 检查文件统计
echo "🔍 检查文件统计..."

# 实际Python文件数
ACTUAL_PY_FILES=$(find src -name "*.py" | wc -l | tr -d ' ')
echo "📁 实际Python文件: $ACTUAL_PY_FILES"

# README中的统计
README_PY_FILES=$(grep "总文件数" README.md | grep -o '[0-9]\+个Python文件' | grep -o '[0-9]\+')
echo "📖 README记录: $README_PY_FILES"

if [ "$ACTUAL_PY_FILES" = "$README_PY_FILES" ]; then
    echo "✅ Python文件统计一致"
else
    echo "⚠️  Python文件统计需要更新"
    echo "   实际: $ACTUAL_PY_FILES"
    echo "   文档: $README_PY_FILES"
fi

echo ""

# 检查测试文件
echo "🔍 检查测试文件..."

ACTUAL_TEST_FILES=$(find tests -name "*.py" | wc -l | tr -d ' ')
echo "🧪 实际测试文件: $ACTUAL_TEST_FILES"

README_TEST_FILES=$(grep "测试覆盖" README.md | grep -o '[0-9]\+个测试文件' | grep -o '[0-9]\+')
echo "📖 README记录: $README_TEST_FILES"

if [ "$ACTUAL_TEST_FILES" = "$README_TEST_FILES" ]; then
    echo "✅ 测试文件统计一致"
else
    echo "⚠️  测试文件统计需要更新"
    echo "   实际: $ACTUAL_TEST_FILES"
    echo "   文档: $README_TEST_FILES"
fi

echo ""

# 检查v2.0功能模块
echo "🔍 检查v2.0功能模块..."

V2_MODULES=(
    "src/kb/incremental_updater.py"
    "src/processors/multimodal_processor.py"
    "src/core/v2_integration.py"
    "tests/test_v2_features.py"
    "docs/V2.0_FEATURES.md"
)

MISSING_MODULES=0
for module in "${V2_MODULES[@]}"; do
    if [ -f "$module" ]; then
        echo "✅ $module"
    else
        echo "❌ $module (缺失)"
        MISSING_MODULES=$((MISSING_MODULES + 1))
    fi
done

if [ $MISSING_MODULES -eq 0 ]; then
    echo "✅ 所有v2.0模块存在"
else
    echo "⚠️  缺失 $MISSING_MODULES 个v2.0模块"
fi

echo ""

# 检查启动脚本
echo "🔍 检查启动脚本..."

if grep -q "v2.0" scripts/start.sh; then
    echo "✅ start.sh 包含v2.0支持"
else
    echo "⚠️  start.sh 可能需要更新v2.0支持"
fi

echo ""

# 总结
echo "📋 检查总结"
echo "================================"

ISSUES=0

if [ "$README_VERSION" != "$API_VERSION" ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ "$ACTUAL_PY_FILES" != "$README_PY_FILES" ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ "$ACTUAL_TEST_FILES" != "$README_TEST_FILES" ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ $MISSING_MODULES -gt 0 ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "🎉 所有文档和代码保持同步！"
    echo "✅ 版本: $README_VERSION"
    echo "✅ Python文件: $ACTUAL_PY_FILES"
    echo "✅ 测试文件: $ACTUAL_TEST_FILES"
    echo "✅ v2.0模块: 完整"
else
    echo "⚠️  发现 $ISSUES 个同步问题，建议修复"
fi

echo ""
echo "💡 提示: 修改代码后记得更新相关文档"
