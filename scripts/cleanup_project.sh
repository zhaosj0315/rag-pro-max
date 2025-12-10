#!/bin/bash

# RAG Pro Max 项目清理脚本
# 移除过程文档、临时文件、旧版本文件等

echo "🧹 RAG Pro Max 项目清理"
echo "================================"

# 需要清理的文件和目录
CLEANUP_ITEMS=(
    # 过程文档 - 开发过程记录，用户不需要
    "RELEASE_v1.7.2.md"
    "RELEASE_v1.7.2_FINAL.md" 
    "RELEASE_v1.7.3.md"
    "RESOURCE_SCHEDULING_SUMMARY.md"
    "RESOURCE_SCHEDULING_VERIFICATION.md"
    "APPPRO_UPDATE_GUIDE.md"
    "V1.7_INTEGRITY_CHECK.md"
    "V1.5.0_REVIEW_CHECKLIST.md"
    "DEPLOYMENT_VERIFICATION.md"
    
    # 旧版本发布脚本
    "release_v1.7.sh"
    "release_v1.6.sh"
    
    # 验证脚本 - 开发过程用，用户不需要
    "verify_planb.sh"
    "verify_v1.6.sh"
    "verify_integration.sh"
    "verify_v1.7.3.sh"
    "verify_v1.4.4.sh"
    "run_v1.6_tests.sh"
    
    # 临时和过程脚本
    "standard_update_process.sh"
    "restart_app.sh"
    "check_before_push.sh"
    "final_status_check.sh"
    "manage_api.sh"
    "cleanup_temp_docs.sh"
    "cleanup_kb.sh"
    "cleanup.sh"
    
    # 错误的requirements文件
    "=10.0.0"
    "=0.3.10"
    "=3.1.0"
    "=0.21.0"
    "=4.8.0"
    "=2.2.0"
    "=2.8.0"
    "=4.35.0"
    "=3.7.0"
    "=2.0.0"
    "=3.0.0"
    "requirements_v21.txt"
    "requirements_v21_fixed.txt"
    
    # 开发规则文档
    "DEV_RULES.md"
    
    # 过程文档目录下的开发记录
    "docs/archive"
    "docs/refactor"
    "docs/PLAN2_COMPLETED.md"
    "docs/V1.5_REFACTOR_PLAN.md"
    "docs/BUG_RESPONSE_DISPLAY.md"
    "docs/SUGGESTION_DEDUP.md"
    "docs/STAGE17_FINAL_OPTIMIZATION.md"
    "docs/V1.6_FEASIBILITY.md"
    "docs/STAGE14_REFACTOR_SUMMARY.md"
    "docs/V1.7_FEASIBILITY.md"
    "docs/V1.5_EXECUTION_SUMMARY.md"
    "docs/STAGE15_REFACTOR_SUMMARY.md"
    "docs/STAGE16_REFACTOR_SUMMARY.md"
    "docs/QUEUE_OPTIMIZATION.md"
    "docs/V1.6_IMPLEMENTATION.md"
    "docs/RESOURCE_PROTECTION_INTEGRATION.md"
    "docs/VERSION_v1.4.4_SUMMARY.md"
    "docs/AUTO_PARALLEL_GUIDE.md"
    "docs/PARALLEL_COMPARISON.md"
    "docs/CODE_QUALITY_REPORT.md"
    "docs/PROJECT_STATUS_STAGE14.md"
    "docs/V1.5_PLAN.md"
    "docs/BUGFIX_KB_INFO_MISSING.md"
    "docs/STAGE14-17_COMPLETE_REFACTOR.md"
    "docs/V1.4.2_SUMMARY.md"
    "docs/KB_MODULE_GUIDE.md"
    "docs/MIGRATION_COMPLETE.md"
    "docs/MAIN_FILE_SIMPLIFICATION.md"
    "docs/RESOURCE_OPTIMIZATION_GUIDE.md"
    "docs/MIGRATION_PLAN.md"
    "docs/PLANB_COMPLETED.md"
    "docs/V1.6_FEATURES.md"
    "docs/BUGFIX_LOGGER_INTERFACE.md"
    "docs/FINAL_SYNC_REPORT.md"
    "docs/STAGE14_HOTFIX.md"
    "docs/USAGE_EXAMPLES.md"
    "docs/OPTIMIZATION_SUMMARY.md"
    "docs/V2.1_FEATURES.md"
    "docs/FINAL_VERIFICATION.md"
    "docs/V1.7_FEATURES.md"
    "docs/SYNC_VERIFICATION.md"
    "docs/RESOURCE_SCHEDULING_ANALYSIS.md"
    "docs/INSTALLATION.md"
    "docs/V1.7_MIGRATION_GUIDE.md"
    "docs/QUEUE_BLOCKING_FIX.md"
    
    # 旧版本测试文件
    "tests/test_v1.7_feasibility.py"
    "tests/test_v1.5.0_feasibility.py"
    "tests/test_v1.4.4_feasibility.py"
    "tests/test_v1.6_feasibility.py"
    "tests/test_v1.5.1_feasibility.py"
    "tests/test_v1.7.3_feasibility.py"
    "tests/test_documentation_feasibility.py"
    "tests/test_stage15_modules.py"
    "tests/test_stage16_modules.py"
    "tests/test_stage14_modules.py"
    "tests/test_planb_integration.py"
    "tests/test_resource_protection.py"
    "tests/test_deployment.py"
    "tests/test_v21_features.py"
    
    # 工具目录 - 开发工具，用户不需要
    "tools"
    
    # 多模态缓存目录（空的）
    "multimodal_cache"
)

# 统计信息
REMOVED_COUNT=0
KEPT_COUNT=0
TOTAL_SIZE=0

echo "📋 准备清理以下项目:"
for item in "${CLEANUP_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        if [ -f "$item" ]; then
            size=$(stat -f%z "$item" 2>/dev/null || echo 0)
            TOTAL_SIZE=$((TOTAL_SIZE + size))
            echo "   📄 $item ($(numfmt --to=iec $size))"
        elif [ -d "$item" ]; then
            size=$(du -sb "$item" 2>/dev/null | cut -f1 || echo 0)
            TOTAL_SIZE=$((TOTAL_SIZE + size))
            echo "   📁 $item/ ($(numfmt --to=iec $size))"
        fi
    else
        echo "   ⏭️  $item (不存在)"
    fi
done

echo ""
echo "💾 预计释放空间: $(numfmt --to=iec $TOTAL_SIZE)"
echo ""

# 确认清理
read -p "🤔 确认清理这些文件? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消清理"
    exit 0
fi

echo ""
echo "🧹 开始清理..."

# 执行清理
for item in "${CLEANUP_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        rm -rf "$item"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
        echo "✅ 已删除: $item"
    else
        KEPT_COUNT=$((KEPT_COUNT + 1))
    fi
done

# 清理空目录
echo ""
echo "🧹 清理空目录..."
find . -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true

# 清理.DS_Store文件
echo "🧹 清理.DS_Store文件..."
find . -name ".DS_Store" -delete 2>/dev/null || true

echo ""
echo "📊 清理完成!"
echo "   ✅ 删除: $REMOVED_COUNT 项"
echo "   ⏭️  跳过: $KEPT_COUNT 项"
echo "   💾 释放: $(numfmt --to=iec $TOTAL_SIZE)"

echo ""
echo "📋 保留的核心文档:"
echo "   📄 README.md - 项目主文档"
echo "   📄 CHANGELOG.md - 版本更新日志"
echo "   📄 API_DOCUMENTATION.md - API接口文档"
echo "   📄 FAQ.md - 常见问题"
echo "   📄 DEPLOYMENT.md - 部署指南"
echo "   📄 USER_MANUAL.md - 用户手册"
echo "   📄 TESTING.md - 测试指南"
echo "   📄 DOCS_INDEX.md - 文档索引"
echo "   📁 docs/V2.0_FEATURES.md - v2.0功能文档"

echo ""
echo "🎯 项目现在更加简洁，只保留用户需要的文档！"
