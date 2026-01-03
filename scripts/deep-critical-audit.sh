#!/bin/bash
# RAG Pro Max - 深度批判性审查脚本
# 发现隐藏问题和不一致性

echo "🔍 RAG Pro Max - 深度批判性审查"
echo "================================"
echo "执行时间: $(date)"
echo ""

# 深度版本一致性检查
echo "🎯 深度版本一致性检查"
echo "===================="

echo "1️⃣ 扫描所有文件中的版本信息..."
version_files=$(find . -name "*.md" -o -name "*.py" -o -name "*.json" | grep -v ".git" | xargs grep -l "v[0-9]\+\.[0-9]\+\.[0-9]\+" 2>/dev/null)

inconsistent_versions=0
for file in $version_files; do
    versions=$(grep -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" "$file" | sort | uniq)
    version_count=$(echo "$versions" | wc -l)
    if [ "$version_count" -gt 1 ]; then
        echo "   ⚠️  $file 包含多个版本: $(echo $versions | tr '\n' ' ')"
        inconsistent_versions=$((inconsistent_versions + 1))
    fi
done

if [ "$inconsistent_versions" -eq 0 ]; then
    echo "   ✅ 版本信息一致性检查通过"
else
    echo "   ❌ 发现 $inconsistent_versions 个文件版本不一致"
fi

# 术语一致性深度检查
echo ""
echo "📝 术语一致性深度检查"
echo "===================="

echo "2️⃣ 检查核心术语使用一致性..."

# 定义核心术语映射
declare -A term_mapping=(
    ["联网搜索"]="Web Search"
    ["深度思考"]="Deep Think"
    ["智能研究"]="Deep Research"
    ["知识库"]="Knowledge Base"
    ["企业级"]="Enterprise"
)

term_issues=0
for zh_term in "${!term_mapping[@]}"; do
    en_term="${term_mapping[$zh_term]}"
    
    zh_count=$(find . -name "*.md" | xargs grep -c "$zh_term" 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
    en_count=$(find . -name "*.md" | xargs grep -c "$en_term" 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
    
    if [ "$zh_count" -gt 0 ] && [ "$en_count" -eq 0 ]; then
        echo "   ⚠️  '$zh_term' 有中文但缺少英文对应 '$en_term'"
        term_issues=$((term_issues + 1))
    elif [ "$en_count" -gt 0 ] && [ "$zh_count" -eq 0 ]; then
        echo "   ⚠️  '$en_term' 有英文但缺少中文对应 '$zh_term'"
        term_issues=$((term_issues + 1))
    fi
done

if [ "$term_issues" -eq 0 ]; then
    echo "   ✅ 核心术语一致性检查通过"
else
    echo "   ❌ 发现 $term_issues 个术语不一致问题"
fi

# 链接有效性检查
echo ""
echo "🔗 链接有效性检查"
echo "================"

echo "3️⃣ 检查文档内部链接..."
broken_links=0

# 检查Markdown链接
md_files=$(find . -name "*.md" | grep -v ".git")
for file in $md_files; do
    # 提取相对路径链接
    links=$(grep -o '\[.*\]([^)]*\.md[^)]*)' "$file" 2>/dev/null | sed 's/.*(\([^)]*\)).*/\1/')
    for link in $links; do
        if [ ! -z "$link" ] && [ ! -f "$(dirname "$file")/$link" ] && [ ! -f "$link" ]; then
            echo "   ❌ $file: 链接失效 -> $link"
            broken_links=$((broken_links + 1))
        fi
    done
done

if [ "$broken_links" -eq 0 ]; then
    echo "   ✅ 内部链接检查通过"
else
    echo "   ❌ 发现 $broken_links 个失效链接"
fi

# 代码示例一致性检查
echo ""
echo "💻 代码示例一致性检查"
echo "===================="

echo "4️⃣ 检查代码示例的准确性..."
code_issues=0

# 检查Python导入语句
import_statements=$(find . -name "*.md" | xargs grep -n "from src\." 2>/dev/null)
if [ ! -z "$import_statements" ]; then
    echo "$import_statements" | while read line; do
        file=$(echo "$line" | cut -d: -f1)
        import_path=$(echo "$line" | grep -o "from src\.[^ ]*" | sed 's/from //')
        module_file=$(echo "$import_path" | sed 's/\./\//g').py
        
        if [ ! -f "$module_file" ]; then
            echo "   ⚠️  $file: 导入路径可能无效 -> $import_path"
            code_issues=$((code_issues + 1))
        fi
    done
fi

# 检查配置文件路径
config_paths=$(find . -name "*.md" | xargs grep -o "config/[^)]*\.json" 2>/dev/null | sort | uniq)
for path in $config_paths; do
    if [ ! -f "$path" ]; then
        echo "   ⚠️  配置文件路径无效: $path"
        code_issues=$((code_issues + 1))
    fi
done

if [ "$code_issues" -eq 0 ]; then
    echo "   ✅ 代码示例一致性检查通过"
fi

# 企业级语言规范检查
echo ""
echo "🏢 企业级语言规范检查"
echo "===================="

echo "5️⃣ 检查语言专业性..."
language_issues=0

# 检查非正式用词
informal_words=("很好" "非常" "超级" "特别" "真的" "确实")
for word in "${informal_words[@]}"; do
    count=$(find . -name "*.md" | xargs grep -c "$word" 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
    if [ "$count" -gt 0 ]; then
        echo "   ⚠️  发现非正式用词 '$word': $count 处"
        language_issues=$((language_issues + 1))
    fi
done

# 检查是否有足够的企业级术语
enterprise_terms=("解决方案" "架构" "部署" "集成" "监控" "审计" "合规" "安全")
enterprise_coverage=0
for term in "${enterprise_terms[@]}"; do
    count=$(find . -name "*.md" | xargs grep -c "$term" 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
    if [ "$count" -gt 0 ]; then
        enterprise_coverage=$((enterprise_coverage + 1))
    fi
done

enterprise_rate=$((enterprise_coverage * 100 / ${#enterprise_terms[@]}))
echo "   📊 企业级术语覆盖率: $enterprise_rate%"

if [ "$enterprise_rate" -lt 80 ]; then
    echo "   ⚠️  企业级术语覆盖率偏低"
    language_issues=$((language_issues + 1))
fi

# 文档结构一致性检查
echo ""
echo "📋 文档结构一致性检查"
echo "===================="

echo "6️⃣ 检查文档标题结构..."
structure_issues=0

# 检查是否所有主要文档都有版本信息
main_docs=("README.md" "DEPLOYMENT.md" "USER_MANUAL.md" "FAQ.md" "ARCHITECTURE.md" "API_DOCUMENTATION.md" "TESTING.md")
for doc in "${main_docs[@]}"; do
    if [ -f "$doc" ]; then
        if ! grep -q "版本.*v3\.2\.2\|Version.*v3\.2\.2\|**版本**.*3\.2\.2" "$doc"; then
            echo "   ⚠️  $doc 缺少标准版本信息格式"
            structure_issues=$((structure_issues + 1))
        fi
        
        if ! grep -q "更新日期.*2026-01-03\|更新时间.*2026-01-03\|Last.*2026-01-03" "$doc"; then
            echo "   ⚠️  $doc 缺少最新更新日期"
            structure_issues=$((structure_issues + 1))
        fi
    fi
done

if [ "$structure_issues" -eq 0 ]; then
    echo "   ✅ 文档结构一致性检查通过"
fi

# 安全敏感信息深度扫描
echo ""
echo "🛡️ 安全敏感信息深度扫描"
echo "======================"

echo "7️⃣ 深度扫描敏感信息..."
security_issues=0

# 检查可能的敏感信息模式
sensitive_patterns=(
    "password.*=" 
    "secret.*=" 
    "token.*=" 
    "key.*=.*['\"][^'\"]{10,}['\"]"
    "localhost:[0-9]{4,5}"
    "127\.0\.0\.1:[0-9]{4,5}"
    "api[_-]?key.*['\"][^'\"]{20,}['\"]"
)

for pattern in "${sensitive_patterns[@]}"; do
    matches=$(find . -name "*.md" -o -name "*.py" -o -name "*.json" | grep -v ".git" | xargs grep -E "$pattern" 2>/dev/null | wc -l)
    if [ "$matches" -gt 0 ]; then
        echo "   ⚠️  发现可能的敏感信息模式 '$pattern': $matches 处"
        # 显示具体位置但不显示内容
        find . -name "*.md" -o -name "*.py" -o -name "*.json" | grep -v ".git" | xargs grep -l -E "$pattern" 2>/dev/null | head -3 | while read file; do
            echo "      -> $file"
        done
        security_issues=$((security_issues + 1))
    fi
done

if [ "$security_issues" -eq 0 ]; then
    echo "   ✅ 安全敏感信息扫描通过"
fi

# 生成深度审查报告
echo ""
echo "📊 深度审查报告汇总"
echo "=================="

total_issues=$((inconsistent_versions + term_issues + broken_links + code_issues + language_issues + structure_issues + security_issues))

echo "📋 问题统计:"
echo "   • 版本不一致: $inconsistent_versions"
echo "   • 术语不一致: $term_issues" 
echo "   • 失效链接: $broken_links"
echo "   • 代码示例问题: $code_issues"
echo "   • 语言规范问题: $language_issues"
echo "   • 结构不一致: $structure_issues"
echo "   • 安全问题: $security_issues"
echo "   ────────────────────"
echo "   📊 总计问题: $total_issues"

if [ "$total_issues" -eq 0 ]; then
    echo ""
    echo "🎉 深度批判性审查通过！"
    echo "   所有检查项目都符合企业级标准"
    exit 0
else
    echo ""
    echo "⚠️  发现 $total_issues 个需要改进的问题"
    echo "   建议按优先级逐一修复"
    exit 1
fi
