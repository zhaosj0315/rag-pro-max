#!/bin/bash
# 快速添加文件到 .gitignore

if [ $# -eq 0 ]; then
    echo "用法: ./scripts/add_to_gitignore.sh <文件名或目录>"
    echo "示例: ./scripts/add_to_gitignore.sh TEMP_NOTES.md"
    echo "示例: ./scripts/add_to_gitignore.sh draft/"
    exit 1
fi

FILE_TO_IGNORE="$1"

# 检查文件是否已在 .gitignore 中
if grep -q "^${FILE_TO_IGNORE}$" .gitignore; then
    echo "✅ ${FILE_TO_IGNORE} 已在 .gitignore 中"
    exit 0
fi

# 添加到 .gitignore 的临时材料区域
# 在 "⬇️ 新增临时材料添加到此处 ⬇️" 后面添加
sed -i '' "/⬇️ 新增临时材料添加到此处 ⬇️/a\\
${FILE_TO_IGNORE}
" .gitignore

echo "✅ 已添加 ${FILE_TO_IGNORE} 到 .gitignore"
echo "💡 记得提交 .gitignore 的更改"
