#!/bin/bash

echo "============================================================"
echo "  RAG Pro Max 临时文档清理"
echo "  时间: $(date)"
echo "============================================================"

# 创建备份目录
mkdir -p docs/archive/temp_cleanup_$(date +%Y%m%d)
BACKUP_DIR="docs/archive/temp_cleanup_$(date +%Y%m%d)"

echo "📦 备份目录: $BACKUP_DIR"

# 1. 清理临时调试文档
echo ""
echo "🧹 清理临时调试文档..."
TEMP_DOCS=(
    "DEBUG_VERSION_FIX.md"
    "DUPLICATE_FIX_SUMMARY.md" 
    "FINAL_DEBUG_FIX.md"
    "FINAL_SUGGESTION_FIX.md"
    "PROBLEM_LOCATED_FIX.md"
    "RESULT_SCOPE_FIX.md"
    "SIMPLE_FIX.md"
    "SUGGESTION_FIX_STATUS.md"
    "SUGGESTION_FIX.md"
    "SUGGESTION_LOG_FIX.md"
    "SUGGESTION_REPEAT_FIX.md"
    "SUGGESTION_USAGE_GUIDE.md"
)

for doc in "${TEMP_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "  📄 备份并删除: $doc"
        mv "$doc" "$BACKUP_DIR/"
    fi
done

# 2. 清理临时测试文件
echo ""
echo "🧹 清理临时测试文件..."
TEMP_TESTS=(
    "debug_llm_passing.py"
    "demo_smart_naming.py"
    "demo_v1.6.py"
    "quick_test.py"
    "test_duplicate_fix.py"
    "test_llm_fix.py"
    "test_optimizations.py"
    "test_suggestion_fix.py"
    "test_suggestion_logging.py"
)

for test in "${TEMP_TESTS[@]}"; do
    if [ -f "$test" ]; then
        echo "  🧪 备份并删除: $test"
        mv "$test" "$BACKUP_DIR/"
    fi
done

# 3. 清理过期发布文档（保留最新3个版本）
echo ""
echo "🧹 清理过期发布文档..."
OLD_RELEASES=(
    "RELEASE_CHECKLIST_v1.4.4.md"
    "RELEASE_v1.4.2.md"
    "RELEASE_v1.4.3.md"
    "RELEASE_v1.4.4.md"
    "RELEASE_v1.5.0.md"
    "RELEASE_v1.5.1.md"
)

for release in "${OLD_RELEASES[@]}"; do
    if [ -f "$release" ]; then
        echo "  📋 备份并删除: $release"
        mv "$release" "$BACKUP_DIR/"
    fi
done

# 4. 清理重复的快速指南
echo ""
echo "🧹 清理重复文档..."
DUPLICATE_DOCS=(
    "QUICK_INTEGRATION.md"
    "QUICKSTART_V1.6.md"
    "RESOURCE_SCHEDULING_QUICK_REFERENCE.md"
    "V1.5.0_MANUAL_TEST_GUIDE.md"
)

for dup in "${DUPLICATE_DOCS[@]}"; do
    if [ -f "$dup" ]; then
        echo "  📄 备份并删除: $dup"
        mv "$dup" "$BACKUP_DIR/"
    fi
done

echo ""
echo "============================================================"
echo "  清理完成"
echo "============================================================"
echo "✅ 临时文档已清理"
echo "📦 备份位置: $BACKUP_DIR"
echo "🗂️ 保留核心文档:"
echo "   - README.md (主文档)"
echo "   - CHANGELOG.md (更新日志)"
echo "   - RELEASE_v1.7.3.md (最新发布)"
echo "   - TESTING.md (测试文档)"
echo "   - 其他核心功能文档"
