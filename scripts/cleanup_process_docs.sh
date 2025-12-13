#!/bin/bash
# 清理过程文档脚本

echo "🧹 开始清理过程文档..."

# 创建备份目录
mkdir -p docs/archive/process_docs_backup_$(date +%Y%m%d)
BACKUP_DIR="docs/archive/process_docs_backup_$(date +%Y%m%d)"

# 移动旧版本发布文档到备份
echo "📦 备份发布文档..."
mv RELEASE_NOTES_v2.0.1.md $BACKUP_DIR/ 2>/dev/null
mv RELEASE_NOTES_v2.1.0.md $BACKUP_DIR/ 2>/dev/null
mv RELEASE_NOTES_v2.2.1*.md $BACKUP_DIR/ 2>/dev/null
mv RELEASE_NOTES_v2.2.2.md $BACKUP_DIR/ 2>/dev/null
mv RELEASE_v1.7.*.md $BACKUP_DIR/ 2>/dev/null

# 移动GitHub流程文档
echo "📦 备份GitHub流程文档..."
mv GITHUB_RELEASE_*.md $BACKUP_DIR/ 2>/dev/null
mv GITHUB_TOPICS.md $BACKUP_DIR/ 2>/dev/null

# 移动临时更新文档
echo "📦 备份临时文档..."
mv UPDATE_SUMMARY_*.md $BACKUP_DIR/ 2>/dev/null
mv APPPRO_UPDATE_GUIDE.md $BACKUP_DIR/ 2>/dev/null
mv NEXT_STEPS.md $BACKUP_DIR/ 2>/dev/null
mv AWESOME_SUBMISSION.md $BACKUP_DIR/ 2>/dev/null
mv SOCIAL_PROMOTION.md $BACKUP_DIR/ 2>/dev/null

# 移动开发过程文档
echo "📦 备份开发文档..."
mv file_processing_analysis.md $BACKUP_DIR/ 2>/dev/null
mv RESOURCE_SCHEDULING_SUMMARY.md $BACKUP_DIR/ 2>/dev/null
mv BATCH_OCR_OPTIMIZATION.md $BACKUP_DIR/ 2>/dev/null
mv FRONTEND_PREVIEW.md $BACKUP_DIR/ 2>/dev/null

# 清理临时测试文件
echo "🗑️ 清理临时测试文件..."
rm -f test_*.py 2>/dev/null

# 清理缓存目录
echo "🗑️ 清理缓存目录..."
rm -rf multimodal_cache/ 2>/dev/null

echo "✅ 清理完成！备份保存在: $BACKUP_DIR"
echo "📊 清理统计:"
echo "   - 备份文档: $(ls $BACKUP_DIR 2>/dev/null | wc -l) 个"
echo "   - 当前目录文档数: $(ls *.md 2>/dev/null | wc -l) 个"
