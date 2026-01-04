#!/bin/bash
# 文档规范检查脚本 - 基于 POST_DEVELOPMENT_SYNC_STANDARD.md

echo "🔍 RAG Pro Max - 文档规范检查"
echo "基于 POST_DEVELOPMENT_SYNC_STANDARD.md"
echo "=================================="
echo ""

# 获取当前版本
VERSION=$(grep -o '"version": "[^"]*"' version.json | cut -d'"' -f4)
echo "📋 当前版本: $VERSION"
echo ""

# 1. 检查核心文档是否存在
echo "1️⃣ 核心文档存在性检查"
echo "========================"

CORE_DOCS=(
    "README.md"
    "CHANGELOG.md" 
    "USER_MANUAL.md"
    "FAQ.md"
    "API_DOCUMENTATION.md"
    "ARCHITECTURE.md"
)

for doc in "${CORE_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc - 存在"
    else
        echo "❌ $doc - 缺失"
    fi
done

echo ""

# 2. 检查版本号一致性
echo "2️⃣ 版本号一致性检查"
echo "===================="

echo "🔍 扫描文档中的版本号..."
grep -r "v[0-9]\+\.[0-9]\+\.[0-9]\+" *.md | head -10

echo ""
echo "🔍 检查是否有旧版本号残留..."
OLD_VERSIONS=("v3.2.5" "v3.2.4" "v3.2.3" "v3.2.2" "v3.2.1")
for old_ver in "${OLD_VERSIONS[@]}"; do
    if grep -r "$old_ver" *.md >/dev/null 2>&1; then
        echo "⚠️  发现旧版本号 $old_ver:"
        grep -r "$old_ver" *.md | head -3
    fi
done

echo ""

# 3. 检查过程性文档
echo "3️⃣ 过程性文档清理检查"
echo "======================"

PROCESS_DOCS=(
    "*PLAN*.md"
    "*TODO*.md" 
    "*DRAFT*.md"
    "*TEMP*.md"
    "*SCRATCH*.md"
    "REFACTOR_*.md"
    "*_SUMMARY_v*.md"
)

for pattern in "${PROCESS_DOCS[@]}"; do
    files=$(ls $pattern 2>/dev/null)
    if [ -n "$files" ]; then
        echo "⚠️  发现过程性文档: $files"
    fi
done

echo ""

# 4. 检查术语一致性
echo "4️⃣ 术语一致性检查"
echo "=================="

TERMS=(
    "联网搜索:Web Search:web_search"
    "深度思考:Deep Think:deep_think" 
    "知识库:Knowledge Base:knowledge_base"
    "RAG Pro Max:RAG Pro Max:rag_pro_max"
)

for term_set in "${TERMS[@]}"; do
    IFS=':' read -ra TERMS_ARRAY <<< "$term_set"
    chinese="${TERMS_ARRAY[0]}"
    english="${TERMS_ARRAY[1]}"
    code="${TERMS_ARRAY[2]}"
    
    echo "🔍 检查术语: $chinese / $english / $code"
    
    # 检查中文术语
    if grep -r "$chinese" *.md >/dev/null 2>&1; then
        echo "  ✅ 中文术语 '$chinese' 存在"
    else
        echo "  ⚠️  中文术语 '$chinese' 未找到"
    fi
    
    # 检查英文术语  
    if grep -r "$english" *.md >/dev/null 2>&1; then
        echo "  ✅ 英文术语 '$english' 存在"
    else
        echo "  ⚠️  英文术语 '$english' 未找到"
    fi
done

echo ""

# 5. 检查敏感信息
echo "5️⃣ 敏感信息检查"
echo "================"

SENSITIVE_PATTERNS=(
    "password"
    "secret"
    "token"
    "api_key"
    "private_key"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if grep -ri "$pattern" *.md >/dev/null 2>&1; then
        echo "⚠️  发现敏感信息模式 '$pattern':"
        grep -ri "$pattern" *.md | head -2
    fi
done

echo ""

# 6. 检查死链
echo "6️⃣ 内部链接检查"
echo "================"

echo "🔍 检查 Markdown 内部链接..."
grep -r "\[.*\](.*\.md)" *.md | while read line; do
    file=$(echo "$line" | cut -d: -f1)
    link=$(echo "$line" | grep -o "([^)]*\.md)" | tr -d "()")
    
    if [ ! -f "$link" ]; then
        echo "❌ 死链: $file -> $link"
    fi
done

echo ""

# 7. 生成检查报告
echo "7️⃣ 检查报告摘要"
echo "================"

echo "📊 文档统计:"
echo "  - Markdown 文件总数: $(find . -name "*.md" | wc -l)"
echo "  - 核心文档完整性: $(ls README.md CHANGELOG.md USER_MANUAL.md FAQ.md 2>/dev/null | wc -l)/4"
echo "  - 当前版本: $VERSION"

echo ""
echo "✅ 文档规范检查完成"
echo "📋 建议: 根据上述检查结果修复发现的问题"
