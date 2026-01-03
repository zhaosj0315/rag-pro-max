#!/bin/bash
# RAG Pro Max - 逐文件深度审查脚本
# 检查每个文档的具体问题

echo "📋 RAG Pro Max - 逐文件深度审查"
echo "==============================="
echo "执行时间: $(date)"
echo ""

# 定义需要检查的核心文档
core_docs=(
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

total_issues=0

for doc in "${core_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "🔍 检查文档: $doc"
        echo "========================"
        
        doc_issues=0
        
        # 1. 检查版本信息格式
        if ! grep -q "**版本**: v3\.2\.2\|**Version**: v3\.2\.2" "$doc"; then
            echo "   ⚠️  缺少标准版本信息格式"
            doc_issues=$((doc_issues + 1))
        fi
        
        # 2. 检查更新日期
        if ! grep -q "2026-01-03" "$doc"; then
            echo "   ⚠️  缺少最新更新日期"
            doc_issues=$((doc_issues + 1))
        fi
        
        # 3. 检查重复版本信息
        version_count=$(grep -c "**版本**: v3\.2\.2\|**Version**: v3\.2\.2" "$doc")
        if [ "$version_count" -gt 1 ]; then
            echo "   ⚠️  发现重复版本信息 ($version_count 处)"
            doc_issues=$((doc_issues + 1))
        fi
        
        # 4. 检查过时版本引用
        old_versions=$(grep -o "v[12]\.[0-9]\.[0-9]" "$doc" | sort | uniq)
        if [ ! -z "$old_versions" ]; then
            echo "   ⚠️  发现过时版本引用: $(echo $old_versions | tr '\n' ' ')"
            doc_issues=$((doc_issues + 1))
        fi
        
        # 5. 检查企业级关键词
        enterprise_keywords=("企业级" "Enterprise" "离线" "本地" "数据安全")
        keyword_found=0
        for keyword in "${enterprise_keywords[@]}"; do
            if grep -q "$keyword" "$doc"; then
                keyword_found=$((keyword_found + 1))
            fi
        done
        
        if [ "$keyword_found" -lt 2 ]; then
            echo "   ⚠️  企业级关键词覆盖不足 ($keyword_found/5)"
            doc_issues=$((doc_issues + 1))
        fi
        
        # 6. 检查链接有效性
        broken_links=$(grep -o '\[.*\]([^)]*\.md[^)]*)' "$doc" 2>/dev/null | sed 's/.*(\([^)]*\)).*/\1/' | while read link; do
            if [ ! -z "$link" ] && [ ! -f "$link" ] && [ ! -f "$(dirname "$doc")/$link" ]; then
                echo "$link"
            fi
        done | wc -l)
        
        if [ "$broken_links" -gt 0 ]; then
            echo "   ⚠️  发现 $broken_links 个失效链接"
            doc_issues=$((doc_issues + broken_links))
        fi
        
        # 7. 检查非正式用词
        informal_words=("很好" "非常" "超级" "特别" "真的")
        informal_count=0
        for word in "${informal_words[@]}"; do
            count=$(grep -c "$word" "$doc" 2>/dev/null || echo 0)
            informal_count=$((informal_count + count))
        done
        
        if [ "$informal_count" -gt 0 ]; then
            echo "   ⚠️  发现 $informal_count 处非正式用词"
            doc_issues=$((doc_issues + 1))
        fi
        
        # 文档评分
        if [ "$doc_issues" -eq 0 ]; then
            echo "   ✅ 文档质量: 优秀 (0 个问题)"
        elif [ "$doc_issues" -le 2 ]; then
            echo "   🟡 文档质量: 良好 ($doc_issues 个问题)"
        else
            echo "   🔴 文档质量: 需要改进 ($doc_issues 个问题)"
        fi
        
        total_issues=$((total_issues + doc_issues))
        echo ""
        
    else
        echo "❌ 文档不存在: $doc"
        total_issues=$((total_issues + 1))
        echo ""
    fi
done

# 检查英文文档目录
echo "🌍 检查英文文档目录"
echo "=================="

if [ -d "docs/en" ]; then
    en_docs=$(find docs/en -name "*.md" | wc -l)
    echo "   📄 英文文档数量: $en_docs"
    
    if [ "$en_docs" -lt 4 ]; then
        echo "   ⚠️  英文文档数量不足"
        total_issues=$((total_issues + 1))
    else
        echo "   ✅ 英文文档数量充足"
    fi
else
    echo "   ❌ 英文文档目录不存在"
    total_issues=$((total_issues + 1))
fi

echo ""

# 生成总结报告
echo "📊 逐文件审查总结"
echo "================"
echo "📋 检查文档数量: ${#core_docs[@]}"
echo "📊 发现问题总数: $total_issues"

if [ "$total_issues" -eq 0 ]; then
    echo "🎉 所有文档质量优秀！"
    echo "✅ 达到企业级标准"
elif [ "$total_issues" -le 5 ]; then
    echo "🟡 文档质量良好，有少量改进空间"
    echo "📈 接近企业级标准"
else
    echo "🔴 文档需要系统性改进"
    echo "🔧 建议逐一修复问题"
fi

echo ""
echo "🎯 逐文件深度审查完成！"

if [ "$total_issues" -eq 0 ]; then
    exit 0
else
    exit 1
fi
