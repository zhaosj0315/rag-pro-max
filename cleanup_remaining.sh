#!/bin/bash

# 清理剩余的过程文件
echo "🧹 清理剩余过程文件..."

BACKUP_DIR="archive/process_files_backup_$(date +%Y%m%d_%H%M%S)_remaining"
mkdir -p "$BACKUP_DIR"

remaining_files=(
    "BUG_FIX_REPORT.md"
    "COMPLETE_INTEGRATION_GUIDE.md"
    "COMPLETE_SOLUTION_SUMMARY.md"
    "CORRECT_WORKFLOW.md"
    "END_TO_END_TEST.md"
    "HOW_TO_USE_DATA_ANALYSIS.md"
    "OCR_OPTIMIZATION_SUMMARY.md"
    "OPTIMIZATION_SUMMARY.md"
    "QUICK_START_TEST.md"
    "FINAL_DELIVERY_REPORT.txt"
    "QUICK_REFERENCE.md"
    "FILE_MANIFEST.md"
)

for file in "${remaining_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$BACKUP_DIR/"
        echo "  ✅ 已移动: $file"
    fi
done

echo "✨ 剩余过程文件清理完成！"
echo "📁 备份位置: $BACKUP_DIR"
