#!/bin/bash
# RAG Pro Max - 最终完整性检查
# 确保所有文档达到发布标准

echo "🎯 RAG Pro Max - 最终完整性检查"
echo "==============================="
echo "版本: v3.2.2"
echo "执行时间: $(date)"
echo ""

# 最终质量检查清单
total_checks=0
passed_checks=0

echo "📋 最终质量检查清单"
echo "=================="

# 1. 核心文档存在性检查
echo "1️⃣ 核心文档存在性检查..."
required_docs=(
    "README.md"
    "README.en.md"
    "DEPLOYMENT.md"
    "USER_MANUAL.md"
    "FAQ.md"
    "ARCHITECTURE.md"
    "API_DOCUMENTATION.md"
    "TESTING.md"
    "CONTRIBUTING.md"
    "CHANGELOG.md"
)

missing_docs=0
for doc in "${required_docs[@]}"; do
    total_checks=$((total_checks + 1))
    if [ -f "$doc" ]; then
        passed_checks=$((passed_checks + 1))
    else
        echo "   ❌ 缺失: $doc"
        missing_docs=$((missing_docs + 1))
    fi
done

if [ "$missing_docs" -eq 0 ]; then
    echo "   ✅ 所有核心文档存在 (${#required_docs[@]}/10)"
else
    echo "   ⚠️  缺失 $missing_docs 个核心文档"
fi

# 2. 版本一致性最终检查
echo ""
echo "2️⃣ 版本一致性最终检查..."
total_checks=$((total_checks + 1))

version_inconsistent=0
for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        # 检查是否包含v3.2.2
        if ! grep -q "v3\.2\.2\|3\.2\.2" "$doc"; then
            echo "   ⚠️  $doc 缺少v3.2.2版本信息"
            version_inconsistent=$((version_inconsistent + 1))
        fi
        
        # 检查是否包含过时版本
        old_versions=$(grep -o "v[12]\.[0-9]\.[0-9]" "$doc" 2>/dev/null | head -3)
        if [ ! -z "$old_versions" ]; then
            echo "   ⚠️  $doc 包含过时版本: $(echo $old_versions | tr '\n' ' ')"
            version_inconsistent=$((version_inconsistent + 1))
        fi
    fi
done

if [ "$version_inconsistent" -eq 0 ]; then
    echo "   ✅ 版本一致性检查通过"
    passed_checks=$((passed_checks + 1))
else
    echo "   ❌ 发现 $version_inconsistent 个版本不一致问题"
fi

# 3. 多语言支持检查
echo ""
echo "3️⃣ 多语言支持检查..."
total_checks=$((total_checks + 1))

if [ -d "docs/en" ]; then
    en_docs=$(find docs/en -name "*.md" | wc -l)
    if [ "$en_docs" -ge 4 ]; then
        echo "   ✅ 英文文档充足 ($en_docs 个文档)"
        passed_checks=$((passed_checks + 1))
    else
        echo "   ⚠️  英文文档不足 ($en_docs 个文档)"
    fi
else
    echo "   ❌ 英文文档目录不存在"
fi

# 4. 企业级特性检查
echo ""
echo "4️⃣ 企业级特性检查..."
total_checks=$((total_checks + 1))

enterprise_keywords=("企业级" "Enterprise" "离线" "本地" "数据安全")
enterprise_coverage=0

for keyword in "${enterprise_keywords[@]}"; do
    count=$(find . -name "*.md" -not -path "./.git/*" -not -path "./vector_db_storage/*" | xargs grep -l "$keyword" 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        enterprise_coverage=$((enterprise_coverage + 1))
    fi
done

enterprise_rate=$((enterprise_coverage * 100 / ${#enterprise_keywords[@]}))
if [ "$enterprise_rate" -ge 80 ]; then
    echo "   ✅ 企业级特性覆盖充足 ($enterprise_rate%)"
    passed_checks=$((passed_checks + 1))
else
    echo "   ⚠️  企业级特性覆盖不足 ($enterprise_rate%)"
fi

# 5. 配置文件完整性检查
echo ""
echo "5️⃣ 配置文件完整性检查..."
total_checks=$((total_checks + 1))

required_configs=("version.json" "config/app_config.json" "config/rag_config.json")
missing_configs=0

for config in "${required_configs[@]}"; do
    if [ ! -f "$config" ]; then
        echo "   ⚠️  缺失配置文件: $config"
        missing_configs=$((missing_configs + 1))
    fi
done

if [ "$missing_configs" -eq 0 ]; then
    echo "   ✅ 所有配置文件存在"
    passed_checks=$((passed_checks + 1))
else
    echo "   ❌ 缺失 $missing_configs 个配置文件"
fi

# 6. 质量保障工具检查
echo ""
echo "6️⃣ 质量保障工具检查..."
total_checks=$((total_checks + 1))

quality_tools=(
    "scripts/enterprise-quality-check.sh"
    "scripts/deep-critical-audit.sh"
    "scripts/file-by-file-audit.sh"
    "scripts/enterprise-docs-audit.sh"
)

missing_tools=0
for tool in "${quality_tools[@]}"; do
    if [ ! -f "$tool" ]; then
        echo "   ⚠️  缺失质量工具: $tool"
        missing_tools=$((missing_tools + 1))
    fi
done

if [ "$missing_tools" -eq 0 ]; then
    echo "   ✅ 所有质量保障工具存在"
    passed_checks=$((passed_checks + 1))
else
    echo "   ❌ 缺失 $missing_tools 个质量工具"
fi

# 生成最终报告
echo ""
echo "🏆 最终完整性报告"
echo "================"

pass_rate=$((passed_checks * 100 / total_checks))
echo "📊 检查通过率: $passed_checks/$total_checks ($pass_rate%)"

if [ "$pass_rate" -eq 100 ]; then
    quality_status="🥇 完美 (Perfect)"
    ready_status="✅ 完全就绪"
elif [ "$pass_rate" -ge 90 ]; then
    quality_status="🥈 优秀 (Excellent)"
    ready_status="✅ 基本就绪"
elif [ "$pass_rate" -ge 80 ]; then
    quality_status="🥉 良好 (Good)"
    ready_status="🟡 需要改进"
else
    quality_status="❌ 不合格 (Poor)"
    ready_status="🔴 不建议发布"
fi

echo "🎯 质量状态: $quality_status"
echo "🚀 发布就绪: $ready_status"

# 发布建议
echo ""
echo "💡 发布建议:"
if [ "$pass_rate" -eq 100 ]; then
    echo "   🎉 恭喜！项目已达到完美发布标准"
    echo "   ✅ 可以立即发布和推广"
    echo "   🌟 具备企业级竞争力"
elif [ "$pass_rate" -ge 90 ]; then
    echo "   👍 项目质量优秀，可以发布"
    echo "   📈 建议修复剩余小问题后推广"
else
    echo "   🔧 建议修复关键问题后再发布"
    echo "   📋 优先解决版本一致性和文档完整性"
fi

echo ""
echo "📅 检查完成时间: $(date)"
echo "🎯 最终完整性检查完成！"

# 返回状态
if [ "$pass_rate" -ge 90 ]; then
    exit 0
else
    exit 1
fi
