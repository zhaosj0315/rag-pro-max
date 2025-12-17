#!/bin/bash
# Git 推送前检查脚本 - 确保遵循"非必要不推送"原则

echo "🔍 检查待推送文件..."

# 不该推送的文件/目录列表
FORBIDDEN_PATTERNS=(
    "vector_db_storage/"
    "chat_histories/"
    "temp_uploads/"
    "hf_cache/"
    "app_logs/"
    "__pycache__/"
    "dist/"
    "build/"
    "*.pyc"
    "*.pyo"
    "*.pyd"
    ".DS_Store"
    "^app_config.json$"
    "^rag_config.json$"
    "^projects_config.json$"
    "CHANGELOG.md"
    "TESTING.md"
    "FAQ.md"
    "DEPLOYMENT.md"
    "CONTRIBUTING.md"
    "DOCS_INDEX.md"
)

# 检查是否有不该推送的文件
FOUND_FORBIDDEN=0
for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if git ls-files | grep -q "$pattern"; then
        echo "❌ 发现不该推送的文件: $pattern"
        git ls-files | grep "$pattern" | head -5
        FOUND_FORBIDDEN=1
    fi
done

if [ $FOUND_FORBIDDEN -eq 1 ]; then
    echo ""
    echo "❌ 检查失败！请移除上述文件后再推送"
    echo "💡 使用: git rm --cached <文件名>"
    exit 1
fi

# 统计文件数量
FILE_COUNT=$(git ls-files | wc -l | tr -d ' ')
echo ""
echo "✅ 检查通过！"
echo "📦 待推送文件数: $FILE_COUNT"
echo ""
echo "文件分类："
echo "  源代码: $(git ls-files 'src/*.py' | wc -l | tr -d ' ') 个"
echo "  工具模块: $(git ls-files 'src/utils/*.py' | wc -l | tr -d ' ') 个"
echo "  测试: $(git ls-files 'tests/*.py' | wc -l | tr -d ' ') 个"
echo "  脚本: $(git ls-files 'scripts/*.sh' | wc -l | tr -d ' ') 个"
echo "  配置模板: $(git ls-files 'config/*.json' | wc -l | tr -d ' ') 个"
echo ""
echo "✅ 可以安全推送！"
