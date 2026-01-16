#!/bin/bash
# 材料维护自动化脚本 (Material Maintenance Automation Script)
# 版本: v1.0
# 生成时间: 2026-01-16

set -e  # 遇到错误立即退出

echo "🧹 RAG Pro Max - 材料维护清理脚本"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 确认执行
echo -e "${YELLOW}⚠️  警告: 此脚本将执行以下操作:${NC}"
echo "  1. 清理 temp_uploads/ 目录"
echo "  2. 移动根目录测试脚本到 tests/integration/"
echo "  3. 移动诊断脚本到 scripts/maintenance/"
echo "  4. 创建 docs/standards/ 目录"
echo "  5. 移动标准文档到 docs/standards/"
echo ""
read -p "是否继续? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ 操作已取消"
    exit 1
fi

echo ""
echo "🚀 开始执行清理..."
echo ""

# ============================================
# P0 任务: 立即执行
# ============================================

echo "📋 [P0-1] 清理 temp_uploads/ 目录..."
if [ -d "temp_uploads" ]; then
    # 统计文件数量
    FILE_COUNT=$(find temp_uploads -type f | wc -l)
    echo "  发现 $FILE_COUNT 个临时文件"
    
    # 清理
    rm -rf temp_uploads/*
    echo -e "  ${GREEN}✓${NC} 已清理 temp_uploads/ 目录"
else
    echo "  ℹ️  temp_uploads/ 目录不存在，跳过"
fi

echo ""
echo "📋 [P0-2] 移动根目录测试脚本..."
# 创建目标目录
mkdir -p tests/integration

# 移动测试脚本
TEST_FILES=(
    "test_all_scenarios.py"
    "test_e2e_scenario.py"
    "test_mock_data.py"
    "test_real_csv.py"
    "test_real_integration.py"
    "test_temp_table_mock.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" tests/integration/
        echo -e "  ${GREEN}✓${NC} 已移动 $file"
    else
        echo "  ℹ️  $file 不存在，跳过"
    fi
done

echo ""
echo "📋 [P0-3] 移动诊断脚本..."
# 创建目标目录
mkdir -p scripts/maintenance

# 移动诊断脚本
DIAG_FILES=(
    "diagnose_kb.py"
    "fix_existing_kb.py"
)

for file in "${DIAG_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" scripts/maintenance/
        echo -e "  ${GREEN}✓${NC} 已移动 $file"
    else
        echo "  ℹ️  $file 不存在，跳过"
    fi
done

echo ""
echo "📋 [P0-4] 更新 .gitignore..."
# 检查 .gitignore 是否已包含 temp_uploads/
if ! grep -q "temp_uploads/" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# 临时上传文件" >> .gitignore
    echo "temp_uploads/" >> .gitignore
    echo -e "  ${GREEN}✓${NC} 已添加 temp_uploads/ 到 .gitignore"
else
    echo "  ℹ️  .gitignore 已包含 temp_uploads/，跳过"
fi

# ============================================
# P1 任务: 本周完成
# ============================================

echo ""
echo "📋 [P1-1] 创建 docs/standards/ 目录..."
mkdir -p docs/standards
echo -e "  ${GREEN}✓${NC} 已创建 docs/standards/ 目录"

echo ""
echo "📋 [P1-2] 移动标准文档..."
# 标准文档列表
STANDARD_DOCS=(
    "DOCUMENTATION_MAINTENANCE_STANDARD.md"
    "DEVELOPMENT_CLEANUP_STANDARD.md"
    "NON_ESSENTIAL_PUSH_STANDARD.md"
    "SINGLE_FEATURE_ITERATION_STANDARD.md"
    "ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md"
    "CONTINUOUS_QUALITY_SOP.md"
    "CONTINUOUS_OPTIMIZATION_GUIDE.md"
    "POST_DEVELOPMENT_SYNC_STANDARD.md"
    "PROJECT_KANBAN_TEMPLATE.md"
    "FREE_PUBLIC_ACCESS.md"
)

for file in "${STANDARD_DOCS[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/standards/
        echo -e "  ${GREEN}✓${NC} 已移动 $file"
    else
        echo "  ℹ️  $file 不存在，跳过"
    fi
done

echo ""
echo "📋 [P1-3] 创建 docs/standards/README.md..."
cat > docs/standards/README.md << 'EOF'
# 开发标准与规范 (Development Standards)

本目录包含 RAG Pro Max 项目的内部开发标准和规范文档。

## 📋 文档清单

### 核心标准
- **DOCUMENTATION_MAINTENANCE_STANDARD.md** - 文档维护标准
- **DEVELOPMENT_CLEANUP_STANDARD.md** - 开发清理标准
- **NON_ESSENTIAL_PUSH_STANDARD.md** - 推送规范

### 开发流程
- **SINGLE_FEATURE_ITERATION_STANDARD.md** - 单功能迭代标准
- **POST_DEVELOPMENT_SYNC_STANDARD.md** - 开发后同步标准
- **CONTINUOUS_QUALITY_SOP.md** - 持续质量 SOP

### 管理规范
- **ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md** - 企业文档管理标准
- **PROJECT_KANBAN_TEMPLATE.md** - 项目看板模板
- **CONTINUOUS_OPTIMIZATION_GUIDE.md** - 持续优化指南

### 其他
- **FREE_PUBLIC_ACCESS.md** - 公开访问说明

## 🎯 使用说明

这些文档是**内部开发规范**，用于指导团队开发工作。

- **开发者**: 请遵循这些标准进行开发
- **用户**: 这些文档对您无用，请查看根目录的用户文档

## 📚 相关文档

- [用户手册](../../USER_MANUAL.md)
- [API 文档](../../API_DOCUMENTATION.md)
- [部署指南](../../DEPLOYMENT.md)
EOF

echo -e "  ${GREEN}✓${NC} 已创建 docs/standards/README.md"

# ============================================
# 完成
# ============================================

echo ""
echo "=================================="
echo -e "${GREEN}✅ 清理完成！${NC}"
echo "=================================="
echo ""
echo "📊 清理统计:"
echo "  - 已清理临时文件: $FILE_COUNT 个"
echo "  - 已移动测试脚本: ${#TEST_FILES[@]} 个"
echo "  - 已移动诊断脚本: ${#DIAG_FILES[@]} 个"
echo "  - 已移动标准文档: ${#STANDARD_DOCS[@]} 个"
echo ""
echo "📋 后续任务:"
echo "  1. 检查 tests/integration/ 中的测试是否正常运行"
echo "  2. 合并 Mock Data 文档 (手动)"
echo "  3. 更新 README.md 添加开发者文档链接 (手动)"
echo "  4. 提交更改到 Git"
echo ""
echo "💡 提示: 查看 MATERIAL_MAINTENANCE_REPORT.md 了解详细信息"
echo ""
