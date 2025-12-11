#!/bin/bash

# RAG Pro Max v2.1.0 推送脚本

echo "🚀 准备推送 RAG Pro Max v2.1.0 到 GitHub..."
echo "============================================================"

# 检查当前分支
current_branch=$(git branch --show-current)
echo "📍 当前分支: $current_branch"

# 检查提交状态
commit_count=$(git log --oneline origin/main..HEAD | wc -l)
echo "📝 待推送提交: $commit_count 个"

if [ $commit_count -eq 0 ]; then
    echo "⚠️  没有新的提交需要推送"
    exit 0
fi

# 显示最新提交
echo ""
echo "📋 最新提交:"
git log --oneline -1

# 显示标签
echo ""
echo "🏷️  标签:"
git tag -l "v2.1*" | tail -3

echo ""
echo "============================================================"
echo "🚀 开始推送..."

# 推送主分支
echo "📤 推送主分支..."
if git push origin main; then
    echo "✅ 主分支推送成功"
else
    echo "❌ 主分支推送失败"
    exit 1
fi

# 推送标签
echo "📤 推送标签..."
if git push origin --tags; then
    echo "✅ 标签推送成功"
else
    echo "❌ 标签推送失败"
    exit 1
fi

echo ""
echo "============================================================"
echo "🎉 RAG Pro Max v2.1.0 推送完成！"
echo "============================================================"
echo ""
echo "📱 GitHub 地址:"
echo "   https://github.com/zhaosj0315/rag-pro-max"
echo ""
echo "🏷️  发布页面:"
echo "   https://github.com/zhaosj0315/rag-pro-max/releases/tag/v2.1.0"
echo ""
echo "📊 主要改进:"
echo "   • 查询速度提升30-37%"
echo "   • 5大新功能模块"
echo "   • 充分利用多核CPU"
echo "   • 完整多模态支持"
echo ""
