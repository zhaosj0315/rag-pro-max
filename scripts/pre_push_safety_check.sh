#!/bin/bash

# RAG Pro Max - 推送前安全检查脚本
# 确保遵守"非必要不推送"原则

echo "🔍 RAG Pro Max 推送前安全检查"
echo "================================"

# 检查是否有违规文件将被推送
echo "📋 检查待推送文件..."
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
    echo "⚠️  没有待推送的文件"
    exit 1
fi

echo "待推送文件数量: $(echo "$STAGED_FILES" | wc -l)"

# 检查违规文件
echo ""
echo "🚨 检查违规文件..."
VIOLATION_FILES=$(echo "$STAGED_FILES" | grep -E "(vector_db_storage|chat_histories|app_logs|temp_uploads|hf_cache|exports|refactor_backups|test_.*_output|PRODUCTION_RELEASE_REPORT|\.pyc$|__pycache__|\.log$|\.db$|\.sqlite|\.pkl|\.pickle|crawler_state.*\.json|\.DS_Store|\.tmp$|\.temp$)" | grep -v "\.gitkeep$")

if [ ! -z "$VIOLATION_FILES" ]; then
    echo "❌ 发现违规文件，禁止推送:"
    echo "$VIOLATION_FILES"
    echo ""
    echo "🔧 修复建议:"
    echo "1. 更新 .gitignore 文件"
    echo "2. 运行: git rm -r --cached 违规文件名"
    echo "3. 重新提交"
    exit 1
fi

echo "✅ 没有发现违规文件"

# 检查文件大小
echo ""
echo "📏 检查文件大小..."
LARGE_FILES=$(echo "$STAGED_FILES" | xargs ls -la 2>/dev/null | awk '$5 > 1048576 {print $9, $5}')

if [ ! -z "$LARGE_FILES" ]; then
    echo "⚠️  发现大文件 (>1MB):"
    echo "$LARGE_FILES"
    echo "请确认这些文件是否必要推送"
fi

# 检查 .gitignore 完整性
echo ""
echo "🛡️  检查 .gitignore 完整性..."
REQUIRED_RULES=(
    "vector_db_storage/"
    "chat_histories/"
    "app_logs/"
    "temp_uploads/"
    "hf_cache/"
    "exports/"
    "crawler_state*.json"
    ".DS_Store"
    "__pycache__/"
    "*.pyc"
)

MISSING_RULES=""
for rule in "${REQUIRED_RULES[@]}"; do
    if ! grep -q "$rule" .gitignore; then
        MISSING_RULES="$MISSING_RULES\n$rule"
    fi
done

if [ ! -z "$MISSING_RULES" ]; then
    echo "⚠️  .gitignore 缺少规则:"
    echo -e "$MISSING_RULES"
    echo "建议添加这些规则到 .gitignore"
fi

# 最终检查
echo ""
echo "🎯 最终安全评估..."
TOTAL_FILES=$(echo "$STAGED_FILES" | wc -l)

if [ $TOTAL_FILES -gt 50 ]; then
    echo "⚠️  推送文件数量较多 ($TOTAL_FILES 个)，请确认是否合理"
fi

echo ""
echo "✅ 安全检查完成！"
echo "📤 可以安全推送到远程仓库"
echo ""
echo "推送命令: git push origin $(git branch --show-current)"
