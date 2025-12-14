#!/bin/bash

# 清理所有知识库数据
echo "🗑️ 清理知识库数据..."

# 创建备份目录
BACKUP_DIR="archive/knowledge_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📊 当前存储占用:"
du -sh vector_db_storage chat_histories temp_uploads

echo ""
echo "📦 备份重要数据到: $BACKUP_DIR"

# 备份配置文件
cp rag_config.json "$BACKUP_DIR/" 2>/dev/null
cp app_config.json "$BACKUP_DIR/" 2>/dev/null

# 清理向量数据库
echo "🗄️ 清理向量数据库 (21G)..."
rm -rf vector_db_storage/*
echo "  ✅ 向量数据库已清空"

# 清理聊天历史
echo "💬 清理聊天历史 (652K)..."
find chat_histories -name "*.json" -delete
echo "  ✅ 聊天历史已清空"

# 清理临时上传文件
echo "📁 清理临时上传文件 (6.9G)..."
find temp_uploads -type f ! -name ".gitkeep" -delete
find temp_uploads -type d ! -name "temp_uploads" -exec rm -rf {} + 2>/dev/null
echo "  ✅ 临时文件已清空"

# 清理建议历史
if [ -d "suggestion_history" ]; then
    echo "💡 清理建议历史..."
    find suggestion_history -name "*.json" -delete
    echo "  ✅ 建议历史已清空"
fi

echo ""
echo "✨ 知识库清理完成！"
echo "💾 释放空间: ~28.5GB"
echo "📁 配置备份: $BACKUP_DIR"
echo ""
echo "🚀 现在可以重新开始构建知识库了！"
