#!/bin/bash
# RAG Pro Max 第一步UI统一推送脚本

echo "🚀 RAG Pro Max 第一步UI统一推送"
echo "================================"

# 添加核心更改
echo "📁 添加第一步合并文件..."
git add src/ui/unified_dialogs.py
git add src/apppro.py  
git add src/document/document_manager_ui.py
git add SYSTEM_OPTIMIZATION_PLAN.md

# 创建提交信息
COMMIT_MSG="🔧 第一步UI统一: 合并重复对话框函数

✨ 功能优化:
- 统一 show_document_detail_dialog 函数
- 创建 src/ui/unified_dialogs.py 统一组件库
- 消除 apppro.py 和 document_manager_ui.py 中的重复代码

🎯 合并效果:
- 减少重复代码: ~50行
- 统一功能: 文档详情对话框
- 保持兼容: 所有现有功能正常

📋 系统优化计划:
- 添加完整的系统重复函数分析
- 制定分步骤优化计划
- 发现23组重复问题待优化

🔍 技术细节:
- 语法检查: ✅ 通过
- 功能兼容: ✅ 完全兼容
- 架构改进: 开始UI组件统一化

📊 下一步计划:
- 继续合并 render_chat_controls_2x2 函数
- 逐步统一所有重复UI组件
- 最终实现完全统一的UI组件库"

echo ""
echo "💬 提交信息预览:"
echo "$COMMIT_MSG"

echo ""
echo "🤔 是否继续提交并推送? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 执行提交..."
    git commit -m "$COMMIT_MSG"
    
    if [ $? -eq 0 ]; then
        echo "✅ 提交成功!"
        echo ""
        echo "🚀 推送到GitHub..."
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo "✅ 推送成功!"
            echo ""
            echo "🎉 第一步UI统一已成功推送到GitHub"
            echo "📱 查看: https://github.com/zhaosj0315/rag-pro-max"
        else
            echo "❌ 推送失败，请检查网络连接"
        fi
    else
        echo "❌ 提交失败"
    fi
else
    echo "❌ 取消推送"
fi
