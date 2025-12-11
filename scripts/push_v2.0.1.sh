#!/bin/bash

# RAG Pro Max v2.0.1 - CPU保护增强版推送脚本
# 2025-12-11

echo "🚀 准备推送 RAG Pro Max v2.0.1 - CPU保护增强版"
echo "=================================================="

# 检查Git状态
echo "📋 检查Git状态..."
git status

# 添加所有修改的文件
echo "📦 添加文件到暂存区..."
git add .

# 检查是否有文件需要提交
if git diff --cached --quiet; then
    echo "❌ 没有文件需要提交"
    exit 1
fi

# 显示将要提交的文件
echo "📄 将要提交的文件:"
git diff --cached --name-only

# 创建提交信息
COMMIT_MESSAGE="🛡️ v2.0.1: CPU保护增强版

🚨 紧急CPU保护机制
- 连续3次CPU>98%时自动停止OCR处理
- CPU阈值从95%降至85%，更加安全
- 最大进程数限制为4个，保留10-12核给系统
- OCR超时时间缩短至10分钟
- 实时监控间隔优化为0.5秒

🔧 技术改进
- 修复batch_ocr_processor.py语法错误
- 修复temp_file未初始化问题
- 新增emergency_cpu_stop.py紧急停止脚本
- 完善异常处理和资源清理

📊 性能优化
- 动态进程数调整策略更保守
- CPU使用率严格控制在85%以下
- 系统稳定性显著提升，避免死机风险
- 处理速度适度降低但更稳定

📚 文档更新
- 新增CPU_PROTECTION_V2.md完整文档
- 更新README.md性能基准
- 新增TROUBLESHOOTING.md故障排除指南
- 新增PERFORMANCE_GUIDE.md性能优化指南
- 完整的CHANGELOG.md更新日志

🎯 测试验证
- 所有CPU保护机制测试通过
- 语法错误修复验证
- 紧急停止功能测试正常
- 系统稳定性大幅提升

Breaking Changes: 无
Backward Compatibility: ✅ 完全兼容

Fixes: #CPU过载 #系统死机 #OCR进程失控
Features: CPU保护机制, 紧急停止, 性能监控
Performance: 稳定性提升, CPU使用率控制"

# 提交更改
echo "💾 提交更改..."
git commit -m "$COMMIT_MESSAGE"

# 检查提交是否成功
if [ $? -ne 0 ]; then
    echo "❌ 提交失败"
    exit 1
fi

# 创建标签
TAG="v2.0.1"
echo "🏷️  创建标签 $TAG..."
git tag -a "$TAG" -m "RAG Pro Max v2.0.1 - CPU保护增强版

🛡️ 主要特性:
- 紧急CPU保护机制
- 智能进程数控制
- 实时系统监控
- 自动资源清理
- 完整故障排除

🎯 稳定性优先，防止系统死机"

# 推送到远程仓库
echo "🌐 推送到远程仓库..."
git push origin main

# 推送标签
echo "🏷️  推送标签..."
git push origin "$TAG"

# 检查推送结果
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 推送成功！"
    echo "=================================================="
    echo "📋 版本信息:"
    echo "   版本: v2.0.1"
    echo "   标签: $TAG"
    echo "   分支: main"
    echo ""
    echo "🔗 GitHub链接:"
    echo "   仓库: https://github.com/yourusername/rag-pro-max"
    echo "   发布: https://github.com/yourusername/rag-pro-max/releases/tag/$TAG"
    echo ""
    echo "📚 主要更新:"
    echo "   • 🛡️ CPU保护机制升级"
    echo "   • 🚨 紧急停止功能"
    echo "   • ⚡ 进程数优化"
    echo "   • 📊 实时监控"
    echo "   • 🧹 资源清理"
    echo "   • 📖 完整文档"
    echo ""
    echo "💡 下一步:"
    echo "   1. 在GitHub上创建Release"
    echo "   2. 更新项目描述"
    echo "   3. 通知用户升级"
else
    echo "❌ 推送失败，请检查网络连接和权限"
    exit 1
fi
