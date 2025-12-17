#!/bin/bash

# RAG Pro Max - 开发过程材料清理脚本
# 删除所有非必要的开发过程材料

echo "🧹 RAG Pro Max 开发材料清理"
echo "=========================="

# 删除内部开发文档
echo "📋 删除内部开发文档..."
rm -f PRODUCTION_RELEASE_STANDARD.md
rm -f RELEASE_CHECKLIST.md
rm -f PROJECT_STRUCTURE_V*.md
rm -f DOCUMENTATION_STRATEGY.md
rm -f REFACTOR_PROGRESS_RECORD.md
rm -f PHASE_*.md
rm -f GRADUAL_REFACTOR_PLAN.md

# 删除开发工具
echo "🛠️  删除开发工具..."
rm -rf tools/
rm -f rag kbllama view_crawl_logs.py

# 删除版本历史文档
echo "📁 删除版本历史文档..."
rm -rf docs/

# 删除测试数据
echo "📊 删除测试和导出数据..."
rm -rf exports/ test_*_output/ refactor_backups/
rm -f PRODUCTION_RELEASE_REPORT_*.md
rm -f *_test_*.txt *_test_*.json

# 删除技术细节文档
echo "🔧 删除技术细节文档..."
rm -f UX_IMPROVEMENTS.md BM25.md RERANK.md
rm -f OCR_LOGGING_SYSTEM.md RESOURCE_PROTECTION_V2.md

# 删除备份和临时文件
echo "🗂️  删除备份和临时文件..."
rm -f *_backup.py *_old.py *.pre-migration
rm -f crawler_state*.json *.tmp *.temp .DS_Store

echo ""
echo "✅ 开发过程材料清理完成！"
echo "📊 清理统计:"
echo "   - 保留核心源代码和配置"
echo "   - 保留用户必需文档"
echo "   - 保留维护标准文档"
echo "   - 删除所有开发过程材料"
echo ""
echo "🎯 项目现在专注于核心功能和用户体验！"
