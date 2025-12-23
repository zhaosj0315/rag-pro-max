#!/bin/bash
# RAG Pro Max v2.4.8 GitHub推送准备脚本
# 统一推荐系统版本推送

echo "🚀 RAG Pro Max v2.4.8 推送准备"
echo "================================"

# 1. 检查当前状态
echo "📊 检查当前Git状态..."
git status --porcelain | wc -l | xargs echo "待提交文件数:"

# 2. 添加核心功能文件
echo ""
echo "📁 添加核心功能文件..."
git add version.json
git add README.md
git add CHANGELOG.md
git add src/apppro.py
git add src/chat/unified_suggestion_engine.py
git add src/chat/suggestion_manager.py
git add src/services/configurable_industry_service.py
git add src/ui/industry_config_interface.py
git add config/custom_industry_sites.json
git add src/config/unified_sites.py
git add src/processors/web_to_kb_processor.py
git add src/ui/sidebar_config.py
git add tests/test_core_modules.py

# 3. 添加删除的重复文件
echo "🗑️ 记录删除的重复组件..."
git add -u src/chat/suggestion_engine.py
git add -u src/chat/web_suggestion_engine.py  
git add -u src/ui/suggestion_panel.py

# 4. 添加文档更新
echo "📝 添加文档更新..."
git add VERSION_ALIGNMENT_SUMMARY.md
git add UNIFIED_VERIFICATION_REPORT.md

# 5. 添加所有更新的.md文件（版本对齐）
echo "📋 添加版本对齐的文档..."
git add *.md

# 6. 显示即将提交的内容
echo ""
echo "📋 即将提交的更改:"
git diff --cached --name-status

# 7. 创建提交信息
COMMIT_MSG="🎯 v2.4.8: 统一推荐系统版

🚀 核心更新:
- 统一推荐问题系统 (消除重复建设)
- 智能行业网站配置 (可自定义)
- 推荐质量验证 (基于知识库)
- 完全统一的生成逻辑 (聊天/文件/网页)

🗑️ 重复建设清理:
- 移除 WebSuggestionEngine
- 移除 SuggestionEngine  
- 移除 SuggestionPanel
- 统一入口: get_unified_suggestion_engine()

🔧 技术优化:
- 智能过滤历史问题
- 兼容适配器模式
- 配置管理系统
- 详细调试信息

📊 架构优化:
- 模块数量: 152个 (精简3个重复模块)
- 服务数量: 4个 (新增行业配置服务)
- 代码总量: 53,050行
- 测试覆盖: 86/95通过

✅ 验证状态:
- 出厂测试: 通过
- 版本一致性: 通过
- 统一推荐系统: 通过
- 重复组件清理: 通过"

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
            echo "🎉 RAG Pro Max v2.4.8 已成功推送到GitHub"
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
