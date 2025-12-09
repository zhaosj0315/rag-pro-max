#!/bin/bash

echo "🗑️  清理测试知识库"
echo "================================"
echo ""

# 显示当前状态
echo "当前状态："
KB_COUNT=$(ls -1d vector_db_storage/*/ 2>/dev/null | wc -l)
KB_SIZE=$(du -sh vector_db_storage/ 2>/dev/null | cut -f1)
echo "  知识库数量: $KB_COUNT"
echo "  占用空间: $KB_SIZE"
echo ""

# 确认
read -p "是否清理所有测试知识库？(y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在清理..."
    
    # 删除所有测试知识库
    rm -rf vector_db_storage/batch_* 2>/dev/null
    rm -rf vector_db_storage/20251201 2>/dev/null
    
    # 保留目录结构
    mkdir -p vector_db_storage
    touch vector_db_storage/.gitkeep
    
    echo "✅ 清理完成！"
    echo ""
    echo "清理后状态："
    KB_COUNT_AFTER=$(ls -1d vector_db_storage/*/ 2>/dev/null | wc -l)
    KB_SIZE_AFTER=$(du -sh vector_db_storage/ 2>/dev/null | cut -f1)
    echo "  知识库数量: $KB_COUNT_AFTER"
    echo "  占用空间: $KB_SIZE_AFTER"
else
    echo "❌ 取消清理"
fi
