#!/bin/bash
# 多语言文档同步脚本

LANGUAGES=("zh" "en")
DOCS_DIR="docs"

echo "🌍 RAG Pro Max - 多语言文档同步检查"
echo "=================================="

# 确保所有语言目录存在
for lang in "${LANGUAGES[@]}"; do
    mkdir -p "$DOCS_DIR/$lang"
    echo "✅ 目录 $DOCS_DIR/$lang/ 已确保存在"
done

# 检查文档完整性
echo ""
echo "📋 检查文档完整性..."
for lang in "${LANGUAGES[@]}"; do
    echo ""
    echo "📁 语言: $lang"
    if [ -d "$DOCS_DIR/$lang" ]; then
        file_count=$(find "$DOCS_DIR/$lang" -name "*.md" | wc -l)
        echo "   文档数量: $file_count"
        if [ $file_count -gt 0 ]; then
            echo "   文档列表:"
            find "$DOCS_DIR/$lang" -name "*.md" -exec basename {} \; | sort | sed 's/^/   - /'
        else
            echo "   ⚠️  暂无文档文件"
        fi
    else
        echo "   ❌ 目录不存在"
    fi
done

echo ""
echo "🎯 下一步建议:"
echo "1. 将现有中文文档移动到 docs/zh/ 目录"
echo "2. 创建对应的英文文档到 docs/en/ 目录"
echo "3. 更新文档内的相对链接"

echo ""
echo "✨ 同步检查完成！"
