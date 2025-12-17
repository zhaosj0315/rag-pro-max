#!/bin/bash
set -e
cd /Users/zhaosj/Documents/rag-pro-max

echo "🧹 清理开始..."

# 1. 删除备份文件
rm -f src/apppro.py.bak
echo "✅ 删除备份文件"

# 2. 删除临时测试
rm -f tests/test_stage5_3.py tests/test_stage5_performance.py tests/test_interface_compatibility.py
echo "✅ 删除临时测试"

# 3. 归档文档
mkdir -p docs/archive
mv docs/STAGE*.md docs/REFACTOR*.md docs/archive/ 2>/dev/null || true
mv docs/*_PLAN.md docs/*_COMPLETE.md docs/archive/ 2>/dev/null || true
echo "✅ 归档临时文档"

# 4. 清理缓存
find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ 清理 Python 缓存"

echo "✅ 清理完成！"
