#!/bin/bash

# RAG Pro Max v2.0 快速提交脚本

echo "🚀 RAG Pro Max v2.0 提交准备"
echo "================================"

# 添加所有v2.0相关文件
echo "📦 添加文件到Git..."

# 核心功能文件
git add src/kb/incremental_updater.py
git add src/processors/multimodal_processor.py  
git add src/core/v2_integration.py

# 测试文件
git add tests/test_v2_features.py
git add tests/test_v2.0_feasibility.py

# 文档和配置
git add docs/V2.0_FEATURES.md
git add requirements_v2.txt
git add .github/RELEASE_TEMPLATE.md

# 脚本文件
git add scripts/deploy_v2.sh
git add scripts/check_docs_sync.sh
git add scripts/prepare_release.sh
git add start_v2.sh
git add stop_v2.sh

# 修改的文件
git add README.md
git add scripts/start.sh
git add src/api/fastapi_server.py
git add src/apppro.py
git add src/kb/kb_manager.py
git add tests/factory_test.py

echo "✅ 文件已添加"

# 提交
echo "💾 提交v2.0版本..."
git commit -m "🚀 Release v2.0.0: 增量更新、多模态支持、API扩展

✨ 新功能:
- 增量更新: 智能检测文件变化，无需重建整个知识库
- 多模态支持: 图片OCR识别、表格数据提取  
- API接口扩展: 完整RESTful API，支持程序化调用
- 智能启动: 自动检测v2.0功能，向后兼容v1.8

🔧 改进:
- 修复队列阻塞问题，添加重置功能
- 修复摘要标题截取问题，显示更完整内容
- 更新文档和测试，保持代码文档一致性

🧪 测试:
- 新增v2.0功能测试 (9个测试用例)
- 新增v2.0可行性测试 (25个测试用例)  
- 更新出厂测试，包含v2.0功能验证

📚 文档:
- 完整的v2.0功能文档和使用指南
- 更新README版本信息和路线图
- 新增部署脚本和同步检查工具

🎯 兼容性:
- 完全向后兼容v1.8版本
- 智能检测和启用v2.0功能
- 统一启动命令，自动适配版本"

echo "✅ 提交完成"

# 创建标签
echo "🏷️  创建v2.0.0标签..."
git tag -a v2.0.0 -m "RAG Pro Max v2.0.0 - 增量更新、多模态支持、API扩展"

echo "✅ 标签创建完成"

echo ""
echo "🎉 v2.0.0 已提交到本地仓库！"
echo ""
echo "📋 下一步:"
echo "   git push origin main      # 推送代码"
echo "   git push origin v2.0.0    # 推送标签"
echo ""
echo "🔗 然后在GitHub上创建Release"
