#!/bin/bash
# RAG Pro Max - 全量同步与清理检查脚本
# 按照 POST_DEVELOPMENT_SYNC_STANDARD.md 执行

echo "🔍 RAG Pro Max - 全量同步与清理检查"
echo "=================================="
echo "版本: v3.2.2"
echo "执行时间: $(date)"
echo ""

# 第一轮：静态与基础检查
echo "🏗️ 第一轮：静态与基础检查"
echo "========================"

# 1. 代码锁定检查
echo "1️⃣ 检查代码锁定状态..."
git_status=$(git status --porcelain)
if [ -z "$git_status" ]; then
    echo "   ✅ 工作区干净，代码已锁定"
else
    echo "   ❌ 工作区不干净，存在未提交变更"
    echo "$git_status"
    exit 1
fi

# 2. 版本一致性检查
echo "2️⃣ 检查版本一致性..."
version_errors=0

# 检查 version.json
if [ -f "version.json" ]; then
    version_json=$(grep -o '"version": "[^"]*"' version.json | cut -d'"' -f4)
    echo "   📄 version.json: $version_json"
else
    echo "   ❌ version.json 不存在"
    version_errors=$((version_errors + 1))
fi

# 检查 README 文件
readme_version=$(grep -o 'version-v[0-9.]*-' README.md | head -1 | sed 's/version-v//;s/-//')
echo "   📄 README.md: v$readme_version"

readme_en_version=$(grep -o 'version-v[0-9.]*-' README.en.md | head -1 | sed 's/version-v//;s/-//')
echo "   📄 README.en.md: v$readme_en_version"

# 检查主应用文件
app_version=$(grep -o '__version__ = "[^"]*"' src/apppro.py | cut -d'"' -f2)
echo "   📄 src/apppro.py: $app_version"

# 验证版本一致性
if [ "$version_json" = "$readme_version" ] && [ "$readme_version" = "$readme_en_version" ] && [ "$readme_en_version" = "$app_version" ]; then
    echo "   ✅ 版本号一致性检查通过"
else
    echo "   ❌ 版本号不一致"
    version_errors=$((version_errors + 1))
fi

# 3. TODO/FIXME 检查
echo "3️⃣ 检查 TODO/FIXME 残留..."
todo_count=$(find src/ -name "*.py" -exec grep -l "TODO\|FIXME\|XXX\|HACK" {} \; 2>/dev/null | wc -l)
if [ "$todo_count" -gt 0 ]; then
    echo "   ⚠️  发现 $todo_count 个文件包含 TODO/FIXME"
    find src/ -name "*.py" -exec grep -Hn "TODO\|FIXME\|XXX\|HACK" {} \; 2>/dev/null | head -5
else
    echo "   ✅ 无 TODO/FIXME 残留"
fi

# 4. 敏感信息检查
echo "4️⃣ 检查敏感信息泄露..."
# 检查真实的API密钥泄露
real_secrets=0

# 检查OpenAI API密钥格式
openai_keys=$(find . -name "*.py" -o -name "*.json" -o -name "*.md" | xargs grep -E "sk-[a-zA-Z0-9]{48}" 2>/dev/null | grep -v ".git" | grep -v "test" | wc -l)
if [ "$openai_keys" -gt 0 ]; then
    echo "   ❌ 发现 $openai_keys 个真实 OpenAI API 密钥"
    real_secrets=$((real_secrets + openai_keys))
fi

# 检查其他长密钥格式
long_secrets=$(find . -name "*.py" -o -name "*.json" -o -name "*.md" | xargs grep -E "['\"][a-zA-Z0-9]{32,}['\"]" 2>/dev/null | grep -v ".git" | grep -v "test" | grep -v "type.*password" | grep -v "key.*=" | wc -l)
if [ "$long_secrets" -gt 0 ]; then
    echo "   ⚠️  发现 $long_secrets 处可能的长密钥"
    real_secrets=$((real_secrets + long_secrets))
fi

if [ "$real_secrets" -eq 0 ]; then
    echo "   ✅ 无真实敏感信息泄露"
fi

sensitive_found=$real_secrets

# 5. 临时文件清理检查
echo "5️⃣ 检查临时文件清理..."
temp_files=$(find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" -o -name "*.tmp" -o -name "nohup.out" | wc -l)
if [ "$temp_files" -gt 0 ]; then
    echo "   ⚠️  发现 $temp_files 个临时文件需要清理"
    find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" -o -name "*.tmp" -o -name "nohup.out" | head -5
else
    echo "   ✅ 临时文件已清理"
fi

echo ""
echo "📊 第一轮检查结果："
echo "   版本错误: $version_errors"
echo "   TODO残留: $todo_count"
echo "   敏感信息: $sensitive_found"
echo "   临时文件: $temp_files"

if [ "$version_errors" -eq 0 ] && [ "$todo_count" -eq 0 ] && [ "$sensitive_found" -eq 0 ] && [ "$temp_files" -eq 0 ]; then
    echo "   ✅ 第一轮检查通过"
    exit 0
else
    echo "   ⚠️  第一轮检查发现问题，需要修复"
    exit 1
fi
