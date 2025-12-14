#!/bin/bash

# 彻底删除所有知识库数据
echo "🗑️ 彻底删除知识库数据..."

echo "📊 删除前存储占用:"
du -sh vector_db_storage chat_histories temp_uploads suggestion_history 2>/dev/null

# 删除向量数据库
echo "🗄️ 删除向量数据库..."
rm -rf vector_db_storage/*
echo "  ✅ 向量数据库已删除"

# 删除聊天历史
echo "💬 删除聊天历史..."
find chat_histories -name "*.json" -delete
echo "  ✅ 聊天历史已删除"

# 删除临时上传文件
echo "📁 删除临时上传文件..."
find temp_uploads -type f ! -name ".gitkeep" -delete
find temp_uploads -type d ! -name "temp_uploads" -exec rm -rf {} + 2>/dev/null
echo "  ✅ 临时文件已删除"

# 删除建议历史
if [ -d "suggestion_history" ]; then
    echo "💡 删除建议历史..."
    find suggestion_history -name "*.json" -delete
    echo "  ✅ 建议历史已删除"
fi

echo ""
echo "✨ 知识库数据彻底删除完成！"
echo "💾 释放空间: ~28.5GB"
