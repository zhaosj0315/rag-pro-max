#!/bin/bash

# RAG Pro Max - 过程文件清理脚本
# 清理开发过程中产生的临时文件和文档

echo "🧹 开始清理过程文件..."

# 创建备份目录
mkdir -p archive/process_files_backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="archive/process_files_backup_$(date +%Y%m%d_%H%M%S)"

# 1. 临时测试文件
echo "📝 清理临时测试文件..."
files_to_backup=(
    "test_suggestion_logging.py"
    "test_terminal_logging.py" 
    "analyze_suggestions.py"
    "watch_suggestions.py"
    "verify_priority_fixes.py"
    "run_priority_tests.py"
)

for file in "${files_to_backup[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $file"
    fi
done

# 2. 过程文档
echo "📚 清理过程文档..."
process_docs=(
    "IMPLEMENTATION_SUMMARY.md"
    "INTEGRATION_COMPLETE.md"
    "INTEGRATION_GUIDE.md"
    "INTEGRATION_PATCH.py"
    "INTEGRATION_VERIFICATION.txt"
    "VERIFICATION_REPORT.md"
    "AUTO_DETECTION_FEATURE.md"
    "CONTENT_ANALYSIS_FEATURE.md"
    "METADATA_EXTRACTION_FEATURE.md"
    "FUNCTIONALITY_VERIFICATION.md"
    "UNIVERSAL_DATA_EXTRACTION.md"
    "DATA_ANALYSIS_CHECKLIST.md"
    "DATA_ANALYSIS_DELIVERY.txt"
    "DATA_ANALYSIS_README.md"
    "DATA_ANALYSIS_SUMMARY.md"
    "SMART_ANALYSIS_OPTIMIZATION.md"
    "SMART_OPTIMIZATION_COMPLETE.txt"
    "QUICK_START_DATA_ANALYSIS.md"
)

for doc in "${process_docs[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $doc"
    fi
done

# 3. 版本临时文件
echo "🚀 清理版本临时文件..."
version_files=(
    "release_v1.6.sh"
    "release_v1.7.sh" 
    "release_v2.2.2.sh"
    "run_v1.6_tests.sh"
    "RELEASE_SUMMARY_v2.2.2.md"
    "V1.5.0_REVIEW_CHECKLIST.md"
    "V1.7_INTEGRITY_CHECK.md"
    "V21_INSTALLATION_SUMMARY.md"
    "VERSION_ALIGNMENT_SUMMARY.md"
)

for file in "${version_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $file"
    fi
done

# 4. 营销文件
echo "📢 清理营销文件..."
marketing_files=(
    "TWITTER_POST_V2.2.1.md"
    "TWITTER_POST_V2.2.md"
    "TWITTER_POST.md"
    "PROMOTION_PLAN.md"
    "COMPETITIVE_ANALYSIS.md"
    "PRODUCT_PAGE.md"
)

for file in "${marketing_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $file"
    fi
done

# 5. 多版本配置文件
echo "⚙️ 清理多版本配置..."
config_files=(
    "requirements_v2.txt"
    "requirements_v21_fixed.txt"
    "requirements_v21.txt"
    "requirements_v23.txt"
    "requirements_lite.txt"
    "start_v2.sh"
    "start_v21_fixed.sh"
    "start_v23.sh"
    "stop_v2.sh"
    "start_clean.sh"
    "start_safe.sh"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $file"
    fi
done

# 6. 验证脚本
echo "🔍 清理验证脚本..."
verify_scripts=(
    "verify_integration.sh"
    "verify_planb.sh"
    "verify_v1.4.4.sh"
    "verify_v1.6.sh"
    "verify_v1.7.3.sh"
    "final_status_check.sh"
)

for script in "${verify_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $script"
    fi
done

echo ""
echo "✨ 清理完成！"
echo "📁 备份位置: $BACKUP_DIR"
echo "📊 统计信息:"
echo "  - 已移动文件数: $(ls -1 "$BACKUP_DIR" | wc -l)"
echo "  - 备份目录大小: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "💡 如需恢复文件，请从备份目录复制回来"
