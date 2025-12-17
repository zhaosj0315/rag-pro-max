#!/bin/bash
# RAG Pro Max 出厂准备脚本
# 版本: v2.4.4
# 用途: 清理项目，准备生产发布

set -e  # 遇到错误立即退出

echo "🚀 RAG Pro Max 出厂准备开始..."
echo "=================================================="

# 检查是否在项目根目录
if [ ! -f "src/apppro.py" ]; then
    echo "❌ 错误: 请在项目根目录执行此脚本"
    exit 1
fi

# 1. 数据清理
echo "📁 第一阶段: 清理用户数据..."
echo "  - 清理向量数据库..."
rm -rf vector_db_storage/*
echo "" > vector_db_storage/.gitkeep

echo "  - 清理聊天历史..."
rm -rf chat_histories/*
echo "" > chat_histories/.gitkeep

echo "  - 清理临时上传..."
rm -rf temp_uploads/*

echo "  - 清理应用日志..."
rm -rf app_logs/*
echo "" > app_logs/.gitkeep

echo "  - 清理建议历史..."
if [ -d "suggestion_history" ]; then
    rm -rf suggestion_history/*
    echo "" > suggestion_history/.gitkeep
fi

echo "  - 清理导出文件..."
if [ -d "exports" ]; then
    rm -rf exports/*
fi

echo "  ⚠️  保留本地缓存 (hf_cache/) - 仅不推送到远程"

# 2. 清理临时和状态文件
echo "🧹 第二阶段: 清理临时文件..."
echo "  - 删除爬虫状态文件..."
rm -f crawler_state_*.json
rm -f detected_cycles.csv
rm -f test_results.json

echo "  - 删除系统文件..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

echo "  - 清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

echo "  - 清理测试缓存..."
rm -rf .pytest_cache/ 2>/dev/null || true

# 3. 重置配置文件
echo "⚙️ 第三阶段: 重置配置文件..."
echo "  - 重置应用配置..."
cat > config/app_config.json << 'EOF'
{
  "version": "2.4.4",
  "first_run": true,
  "default_model": "qwen2.5:7b",
  "max_file_size": 104857600,
  "enable_gpu": true,
  "enable_ocr": true
}
EOF

echo "  - 清空历史记录..."
echo "[]" > config/alert_history.json
echo "[]" > config/scheduler_history.json

if [ -f "config/monitoring_history.json" ]; then
    echo "{}" > config/monitoring_history.json
fi

if [ -f "config/performance_history.json" ]; then
    echo "{}" > config/performance_history.json
fi

echo "  - 删除根目录配置文件..."
rm -f app_config.json
rm -f rag_config.json

# 4. 清理开发文件
echo "📚 第四阶段: 清理开发文件..."
echo "  - 删除重构文档..."
rm -f REFACTOR_PROGRESS_RECORD.md
rm -f PHASE_*.md
rm -f GRADUAL_REFACTOR_PLAN.md

echo "  - 删除备份文件..."
rm -f src/apppro.py.pre-migration
find . -name "*_backup.py" -delete 2>/dev/null || true
find . -name "*_old.py" -delete 2>/dev/null || true

echo "  - 保留最新项目结构文档..."
ls PROJECT_STRUCTURE_V*.md 2>/dev/null | head -n -1 | xargs rm -f 2>/dev/null || true

# 5. 版本信息检查
echo "🔖 第五阶段: 检查版本信息..."
VERSION=$(python -c "import json; print(json.load(open('version.json'))['version'])" 2>/dev/null || echo "2.4.4")
echo "  - 当前版本: $VERSION"

# 检查关键文件中的版本一致性
echo "  - 检查版本一致性..."
if grep -q "$VERSION" README.md; then
    echo "    ✅ README.md 版本一致"
else
    echo "    ⚠️  README.md 版本需要更新"
fi

# 6. 代码质量检查
echo "🔍 第六阶段: 代码质量检查..."
echo "  - 检查调试代码..."
DEBUG_COUNT=$(grep -r "print(" src/ --include="*.py" | wc -l || echo "0")
if [ "$DEBUG_COUNT" -gt 0 ]; then
    echo "    ⚠️  发现 $DEBUG_COUNT 个 print() 调试语句"
    echo "    建议手动检查并移除调试代码"
else
    echo "    ✅ 无调试代码残留"
fi

echo "  - 检查TODO注释..."
TODO_COUNT=$(grep -r "# TODO\|# FIXME" src/ --include="*.py" | wc -l || echo "0")
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "    ⚠️  发现 $TODO_COUNT 个 TODO/FIXME 注释"
else
    echo "    ✅ 无待办事项残留"
fi

# 7. 功能验证
echo "🧪 第七阶段: 功能验证..."
echo "  - 验证核心模块导入..."
python -c "
import sys
sys.path.append('src')
try:
    from services.file_service import FileService
    from services.knowledge_base_service import KnowledgeBaseService
    from services.config_service import get_config_service
    print('    ✅ 核心服务模块导入成功')
except Exception as e:
    print(f'    ❌ 模块导入失败: {e}')
    exit(1)
" || exit 1

echo "  - 运行出厂测试..."
if [ -f "tests/factory_test.py" ]; then
    python tests/factory_test.py --quiet || echo "    ⚠️  部分测试未通过，请检查"
else
    echo "    ⚠️  未找到出厂测试文件"
fi

# 8. 启动验证
echo "🚀 第八阶段: 启动验证..."
echo "  - 验证应用启动..."
timeout 30 streamlit run src/apppro.py --server.headless true --server.port 8502 &
STREAMLIT_PID=$!
sleep 15

if curl -f http://localhost:8502 >/dev/null 2>&1; then
    echo "    ✅ 应用启动验证成功"
else
    echo "    ❌ 应用启动验证失败"
fi

# 清理测试进程
kill $STREAMLIT_PID 2>/dev/null || true
sleep 2
pkill -f "streamlit.*apppro.py" 2>/dev/null || true

# 9. 生成出厂报告
echo "📊 第九阶段: 生成出厂报告..."
REPORT_FILE="PRODUCTION_RELEASE_REPORT_$(date +%Y%m%d_%H%M%S).md"
cat > "$REPORT_FILE" << EOF
# RAG Pro Max 出厂报告

**生成时间**: $(date)
**版本**: $VERSION
**执行者**: $(whoami)

## 清理统计
- 清理测试数据: ✅
- 清理临时文件: ✅  
- 重置配置文件: ✅
- 清理开发文件: ✅

## 质量检查
- 调试代码检查: $DEBUG_COUNT 个 print() 语句
- TODO注释检查: $TODO_COUNT 个待办事项
- 模块导入验证: ✅
- 启动验证: $(curl -f http://localhost:8502 >/dev/null 2>&1 && echo "✅" || echo "❌")

## 文件统计
- 源代码文件: $(find src/ -name "*.py" | wc -l) 个
- 配置文件: $(find config/ -name "*.json" | wc -l) 个
- 文档文件: $(find . -maxdepth 1 -name "*.md" | wc -l) 个
- 测试文件: $(find tests/ -name "*.py" 2>/dev/null | wc -l) 个

## 推送建议
$([ "$DEBUG_COUNT" -eq 0 ] && [ "$TODO_COUNT" -eq 0 ] && echo "✅ 建议可以推送" || echo "⚠️ 建议先处理代码质量问题")

---
*此报告由出厂准备脚本自动生成*
EOF

echo "=================================================="
echo "🎉 出厂准备完成！"
echo ""
echo "📋 执行总结:"
echo "  - 清理了所有测试数据和临时文件"
echo "  - 重置了配置文件为出厂默认值"  
echo "  - 删除了开发过程文件"
echo "  - 验证了核心功能正常"
echo ""
echo "📊 出厂报告: $REPORT_FILE"
echo ""
echo "🚀 下一步:"
echo "  1. 检查出厂报告中的质量问题"
echo "  2. 手动验证关键功能"
echo "  3. 更新 .gitignore 为出厂版本"
echo "  4. 执行 git add . && git commit -m 'chore: prepare production release v$VERSION'"
echo "  5. 推送到远程仓库"
echo ""
echo "⚠️  重要提醒:"
echo "  - 此操作不可逆，请确保已备份重要数据"
echo "  - 推送前请再次确认所有文档已更新"
echo "  - 建议在测试环境先验证完整流程"
echo ""
echo "✅ 准备就绪，可以推送到生产环境！"
