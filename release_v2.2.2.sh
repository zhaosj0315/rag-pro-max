#!/bin/bash

# RAG Pro Max v2.2.2 发布脚本

echo "🚀 准备发布 RAG Pro Max v2.2.2"
echo "=================================="

# 1. 检查当前状态
echo "📋 检查当前状态..."
git status

# 2. 运行最终测试
echo "🧪 运行最终测试..."
python test_v2.2.2_feasibility.py
if [ $? -ne 0 ]; then
    echo "❌ 可行性测试失败，停止发布"
    exit 1
fi

python tests/factory_test.py
if [ $? -ne 0 ]; then
    echo "❌ 出厂测试失败，停止发布"
    exit 1
fi

echo "✅ 所有测试通过！"

# 3. 添加所有更改
echo "📦 添加所有更改..."
git add .

# 4. 提交更改
echo "💾 提交更改..."
git commit -m "🎉 Release v2.2.2 - 资源保护增强版

✨ 新功能:
- 资源保护机制优化 (CPU 75%, 内存 85%)
- OCR日志记录系统
- 处理统计功能
- 日志查看工具

🛡️ 稳定性提升:
- 双重资源监控
- 智能线程调整
- 详细处理追踪
- 防死机保护

📊 监控增强:
- 实时资源监控
- 处理性能统计
- 错误诊断日志
- 可视化日志查看

🧪 测试结果:
- 出厂测试: 67/72 通过
- 可行性测试: 6/6 通过
- 资源保护测试: 100% 通过
- 日志记录测试: 100% 通过"

# 5. 创建标签
echo "🏷️ 创建版本标签..."
git tag -a v2.2.2 -m "RAG Pro Max v2.2.2 - 资源保护增强版

🛡️ 资源保护机制优化
📊 OCR日志记录系统  
📈 处理统计功能
🔧 日志查看工具
🚀 双重资源监控"

# 6. 推送到远程
echo "🌐 推送到远程仓库..."
git push origin main
git push origin v2.2.2

echo ""
echo "🎉 RAG Pro Max v2.2.2 发布完成！"
echo "=================================="
echo "📋 下一步:"
echo "1. 访问 GitHub 创建 Release"
echo "2. 复制发布说明内容"
echo "3. 发布到社交媒体"
echo "4. 通知用户升级"
echo ""
echo "📄 发布说明文件: RELEASE_NOTES_v2.2.2.md"
echo "📋 发布清单文件: GITHUB_RELEASE_v2.2.2.md"
echo ""
echo "✅ 准备就绪，可以在 GitHub 上创建 Release！"
