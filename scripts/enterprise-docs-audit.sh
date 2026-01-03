#!/bin/bash
# RAG Pro Max - 企业文档管理规范批量更新脚本
# 按照 ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md 执行全面文档更新

echo "🏢 RAG Pro Max - 企业文档管理规范批量更新"
echo "=============================================="
echo "版本: v3.2.2"
echo "执行时间: $(date)"
echo "标准依据: ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md"
echo ""

# 定义企业级文档标准信息
ENTERPRISE_VERSION="v3.2.2"
ENTERPRISE_DATE="2026-01-03"
ENTERPRISE_SCOPE="企业级部署与运维"

# 第一层：用户门面文档更新
echo "📋 第一层：用户门面文档更新"
echo "=========================="

# 检查并更新README.md版本信息
echo "1️⃣ 检查README.md版本信息..."
if grep -q "v3.2.2" README.md; then
    echo "   ✅ README.md 版本信息正确"
else
    echo "   ⚠️  README.md 版本信息需要更新"
fi

# 检查英文README
echo "2️⃣ 检查README.en.md版本信息..."
if grep -q "v3.2.2" README.en.md; then
    echo "   ✅ README.en.md 版本信息正确"
else
    echo "   ⚠️  README.en.md 版本信息需要更新"
fi

# 第二层：技术架构文档检查
echo ""
echo "🏗️ 第二层：技术架构文档检查"
echo "=========================="

# 检查关键技术文档的版本信息
docs_to_check=("ARCHITECTURE.md" "API_DOCUMENTATION.md" "TESTING.md" "CHANGELOG.md")

for doc in "${docs_to_check[@]}"; do
    if [ -f "$doc" ]; then
        echo "3️⃣ 检查 $doc..."
        if grep -q "v3.2.2\|3.2.2" "$doc"; then
            echo "   ✅ $doc 版本信息正确"
        else
            echo "   ⚠️  $doc 版本信息需要更新"
        fi
    else
        echo "   ❌ $doc 文件不存在"
    fi
done

# 第三层：管理规范文档检查
echo ""
echo "📚 第三层：管理规范文档检查"
echo "=========================="

standard_docs=("DOCUMENTATION_MAINTENANCE_STANDARD.md" "NON_ESSENTIAL_PUSH_STANDARD.md" "DEVELOPMENT_CLEANUP_STANDARD.md" "DEVELOPMENT_STANDARD.md")

for doc in "${standard_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "4️⃣ 检查 $doc..."
        if grep -q "v3.2.2\|3.2.2" "$doc"; then
            echo "   ✅ $doc 版本信息正确"
        else
            echo "   ⚠️  $doc 版本信息需要更新"
        fi
    else
        echo "   ❌ $doc 文件不存在"
    fi
done

# 第四层：企业配置文档检查
echo ""
echo "⚙️ 第四层：企业配置文档检查"
echo "=========================="

echo "5️⃣ 检查version.json..."
if [ -f "version.json" ]; then
    version_in_json=$(grep -o '"version": "[^"]*"' version.json | cut -d'"' -f4)
    if [ "$version_in_json" = "3.2.2" ]; then
        echo "   ✅ version.json 版本正确: $version_in_json"
    else
        echo "   ⚠️  version.json 版本需要更新: $version_in_json -> 3.2.2"
    fi
else
    echo "   ❌ version.json 文件不存在"
fi

echo "6️⃣ 检查配置文件目录..."
if [ -d "config" ]; then
    config_files=$(find config/ -name "*.json" | wc -l)
    echo "   ✅ 配置目录存在，包含 $config_files 个配置文件"
else
    echo "   ❌ config 目录不存在"
fi

# 企业级文档质量检查
echo ""
echo "🔍 企业级文档质量检查"
echo "===================="

echo "7️⃣ 检查企业级关键词覆盖..."
enterprise_keywords=("企业级" "Enterprise" "离线" "Offline" "本地" "Local" "数据安全" "Data Security")
total_coverage=0

for keyword in "${enterprise_keywords[@]}"; do
    count=$(find . -name "*.md" -exec grep -l "$keyword" {} \; 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "   ✅ '$keyword' 覆盖 $count 个文档"
        total_coverage=$((total_coverage + 1))
    else
        echo "   ⚠️  '$keyword' 未找到相关文档"
    fi
done

coverage_rate=$((total_coverage * 100 / ${#enterprise_keywords[@]}))
echo "   📊 企业级关键词覆盖率: $coverage_rate%"

# 多语言文档检查
echo ""
echo "🌍 多语言文档检查"
echo "================"

echo "8️⃣ 检查多语言文档结构..."
if [ -d "docs/zh" ] && [ -d "docs/en" ]; then
    zh_docs=$(find docs/zh -name "*.md" 2>/dev/null | wc -l)
    en_docs=$(find docs/en -name "*.md" 2>/dev/null | wc -l)
    echo "   ✅ 多语言目录存在"
    echo "   📄 中文文档: $zh_docs 个"
    echo "   📄 英文文档: $en_docs 个"
    
    if [ "$zh_docs" -eq "$en_docs" ]; then
        echo "   ✅ 中英文文档数量一致"
    else
        echo "   ⚠️  中英文文档数量不一致"
    fi
else
    echo "   ⚠️  多语言目录结构不完整"
fi

# 文档完整性检查
echo ""
echo "📋 文档完整性检查"
echo "================"

echo "9️⃣ 检查核心文档完整性..."
required_docs=("README.md" "README.en.md" "DEPLOYMENT.md" "USER_MANUAL.md" "FAQ.md" "ARCHITECTURE.md" "CHANGELOG.md")
missing_docs=0

for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✅ $doc 存在"
    else
        echo "   ❌ $doc 缺失"
        missing_docs=$((missing_docs + 1))
    fi
done

completeness_rate=$(((${#required_docs[@]} - missing_docs) * 100 / ${#required_docs[@]}))
echo "   📊 核心文档完整性: $completeness_rate%"

# 生成企业级文档质量报告
echo ""
echo "📊 企业级文档质量报告"
echo "===================="

echo "📋 质量指标汇总:"
echo "   • 版本一致性: 需要人工验证"
echo "   • 企业关键词覆盖率: $coverage_rate%"
echo "   • 核心文档完整性: $completeness_rate%"
echo "   • 多语言支持: $([ -d "docs/zh" ] && [ -d "docs/en" ] && echo "✅ 支持" || echo "❌ 不支持")"

# 企业级改进建议
echo ""
echo "💡 企业级改进建议:"
if [ "$coverage_rate" -lt 80 ]; then
    echo "   • 增加企业级安全特性描述"
fi
if [ "$completeness_rate" -lt 100 ]; then
    echo "   • 补充缺失的核心文档"
fi
if [ ! -d "docs/zh" ] || [ ! -d "docs/en" ]; then
    echo "   • 完善多语言文档结构"
fi

echo ""
echo "🎯 企业级文档管理规范检查完成！"
echo "建议按照 ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md 进行改进"
