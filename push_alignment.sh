#!/bin/bash
# 材料对齐推送脚本

echo "🚀 RAG Pro Max 材料对齐推送"
echo "=========================="

# 添加对齐后的文件
git add version.json
git add README.md  
git add CHANGELOG.md
git add MATERIAL_ALIGNMENT_REPORT.md

# 提交信息
COMMIT_MSG="📋 v2.4.9: 材料对齐和版本一致性更新

🔄 版本信息更新:
- 版本号: v2.4.9 (UI组件统一版)
- 发布日期: 2025-12-23
- 代码名: UI组件统一版

✅ 对齐验证:
- UI组件集成: ✅ 通过
- 函数依赖检查: ✅ 通过  
- 兼容性测试: ✅ 通过
- 版本一致性: ✅ 完全一致

📊 第一步UI统一成果:
- 统一 show_document_detail_dialog 函数
- 创建 unified_dialogs.py 组件库
- 减少重复代码 ~50行
- 保持100%功能兼容

🎯 系统优化进展:
- 发现23组重复问题
- 完成第1组函数统一
- 制定完整优化计划
- 准备继续第二步开发

📋 材料状态:
- 所有文档版本对齐: ✅
- 代码依赖关系正确: ✅  
- 功能完全兼容: ✅
- 准备继续开发: ✅"

echo "💬 提交信息:"
echo "$COMMIT_MSG"

echo ""
echo "🚀 执行推送..."
git commit -m "$COMMIT_MSG"

if [ $? -eq 0 ]; then
    git push origin main
    if [ $? -eq 0 ]; then
        echo "✅ 材料对齐推送成功!"
        echo "🎯 v2.4.9 版本已发布"
        echo "🚀 可以开始第二步开发"
    else
        echo "❌ 推送失败"
    fi
else
    echo "❌ 提交失败"
fi
