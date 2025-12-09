#!/bin/bash

echo "🗑️  RAG Pro Max 清理脚本"
echo "================================"
echo ""

# 1. 删除 .DS_Store 文件
echo "1. 清理 .DS_Store 文件..."
find . -name ".DS_Store" -type f -delete
echo "   ✅ 完成"

# 2. 删除 Python 缓存
echo "2. 清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -type f -delete 2>/dev/null
echo "   ✅ 完成"

# 3. 移动旧的阶段总结到 docs/archive/
echo "3. 归档旧的阶段总结..."
mkdir -p docs/archive
mv STAGE_3.*.md docs/archive/ 2>/dev/null
mv RESOURCE_*.md docs/archive/ 2>/dev/null
echo "   ✅ 完成"

# 4. 清理旧的测试聊天历史（保留最近10个）
echo "4. 清理旧的测试聊天历史..."
cd chat_histories
ls -t batch_*.json 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
cd ..
echo "   ✅ 完成（保留最近10个）"

# 5. 清理临时上传文件
echo "5. 清理临时上传文件..."
rm -f temp_uploads/* 2>/dev/null
echo "   ✅ 完成"

echo ""
echo "================================"
echo "✅ 清理完成！"
echo ""
echo "清理内容："
echo "  - .DS_Store 文件"
echo "  - Python 缓存"
echo "  - 旧的阶段总结（已归档到 docs/archive/）"
echo "  - 旧的测试聊天历史（保留最近10个）"
echo "  - 临时上传文件"
