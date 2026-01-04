#!/bin/bash
# RAG Pro Max - POST_DEVELOPMENT_SYNC_STANDARD 全面检查脚本
# 按照 POST_DEVELOPMENT_SYNC_STANDARD.md 执行六轮专家审查

echo "🔍 RAG Pro Max - 全量同步与清理检查"
echo "====================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查结果统计
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# 检查函数
check_item() {
    local description="$1"
    local command="$2"
    local type="${3:-error}" # error, warning, info
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "  [$TOTAL_CHECKS] $description... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [ "$type" = "warning" ]; then
            echo -e "${YELLOW}⚠️  WARN${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        else
            echo -e "${RED}❌ FAIL${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
        return 1
    fi
}

# 检查详细信息
check_detail() {
    local description="$1"
    local command="$2"
    
    echo "  📋 $description:"
    eval "$command" 2>/dev/null | head -5 | sed 's/^/      /'
    echo ""
}

echo "🏗️ 第一轮：静态与基础检查 (Round 1: Static & Foundation)"
echo "=================================================="

# 1. 代码锁定检查
echo -e "\n${BLUE}🔒 代码锁定状态检查${NC}"
check_item "Git工作区状态" "git diff --quiet && git diff --cached --quiet"
check_item "未跟踪文件检查" "[ \$(git ls-files --others --exclude-standard | wc -l) -eq 0 ]" "warning"

# 2. 版本一致性检查
echo -e "\n${BLUE}🏷️ 版本一致性检查${NC}"
VERSION=$(grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' README.md | head -1)
echo "  检测到版本: $VERSION"

check_item "README.md版本号" "grep -q '$VERSION' README.md"
check_item "CHANGELOG.md版本号" "grep -q '$VERSION' CHANGELOG.md"
check_item "代码中版本号一致性" "! grep -r 'version.*[0-9]\+\.[0-9]\+\.[0-9]\+' src/ | grep -v '$VERSION\|Safari\|Mozilla\|WebKit' | grep -q ."

# 3. 基础文件存在性检查
echo -e "\n${BLUE}📁 核心文件存在性检查${NC}"
CORE_FILES=(
    "README.md"
    "README.en.md" 
    "CHANGELOG.md"
    "LICENSE"
    "requirements.txt"
    "src/apppro.py"
    "USER_MANUAL.md"
    "API_DOCUMENTATION.md"
    "ARCHITECTURE.md"
    "FAQ.md"
    "TESTING.md"
    "DEPLOYMENT.md"
)

for file in "${CORE_FILES[@]}"; do
    check_item "核心文件: $file" "[ -f '$file' ]"
done

echo -e "\n💼 第二轮：逻辑与功能检查 (Round 2: Logic & Functionality)"
echo "=================================================="

# 4. 配置文件检查
echo -e "\n${BLUE}⚙️ 配置文件检查${NC}"
check_item "应用配置文件" "[ -f 'config/app_config.json' ]"
check_item "RAG配置文件" "[ -f 'config/rag_config.json' ]"
check_item "调度配置文件" "[ -f 'config/scheduler_config.json' ]"

# 5. 脚本可执行性检查
echo -e "\n${BLUE}🔧 脚本可执行性检查${NC}"
SCRIPTS=(
    "scripts/start.sh"
    "scripts/deploy_linux.sh"
    "scripts/deploy_windows.bat"
    "scripts/docker-build.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        check_item "脚本可执行: $script" "[ -x '$script' ]"
    fi
done

echo -e "\n🎨 第三轮：体验与一致性检查 (Round 3: Experience & Consistency)"
echo "=================================================="

# 6. 术语一致性检查
echo -e "\n${BLUE}📝 术语一致性检查${NC}"
TERMS=(
    "联网搜索:Web Search:web_search"
    "深度思考:Deep Think:deep_think"
    "知识库:Knowledge Base:knowledge_base"
    "向量数据库:Vector Database:vector_db"
)

for term_set in "${TERMS[@]}"; do
    IFS=':' read -ra TERMS_ARRAY <<< "$term_set"
    chinese_term="${TERMS_ARRAY[0]}"
    english_term="${TERMS_ARRAY[1]}"
    code_term="${TERMS_ARRAY[2]}"
    
    check_item "术语一致性: $chinese_term" "grep -q '$chinese_term' README.md && grep -q '$english_term' README.en.md" "warning"
done

# 7. 文档链接检查
echo -e "\n${BLUE}🔗 文档链接检查${NC}"
check_item "README中的文档链接" "grep -o '\[.*\](.*\.md)' README.md | cut -d'(' -f2 | cut -d')' -f1 | xargs -I {} test -f {}" "warning"

echo -e "\n🧹 第四轮：代码与规范检查 (Round 4: Code & Standards)"
echo "=================================================="

# 8. 代码清理检查
echo -e "\n${BLUE}🗑️ 代码清理检查${NC}"
check_item "无__pycache__目录" "! find . -name '__pycache__' -type d | grep -q ."
check_item "无.DS_Store文件" "! find . -name '.DS_Store' | grep -q ."
check_item "无临时日志文件" "! find . -name '*.log' -o -name '*.tmp' | grep -q ."
check_item "无TODO注释" "! grep -r 'TODO' src/ | grep -q ." "warning"

# 9. 敏感信息检查
echo -e "\n${BLUE}🛡️ 敏感信息检查${NC}"
check_item "无API密钥泄露" "! grep -r 'api[_-]key.*=[^\"]*[a-zA-Z0-9]{20}' src/ | grep -v 'placeholder\|example\|<.*>\|EMPTY\|test' | grep -q ."
check_item "无密码硬编码" "! grep -r 'password.*=[^\"]*[a-zA-Z0-9]{8}' src/ | grep -v 'placeholder\|example\|<.*>\|type=\"password\"' | grep -q ."
check_item "无私钥文件" "! find . -name '*.pem' -o -name '*.key' -o -name 'id_rsa' | grep -q ."

echo -e "\n🕵️ 第五轮：红队批判性审计 (Round 5: Red Team Critical Audit)"
echo "=================================================="

# 10. 功能空壳检查
echo -e "\n${BLUE}🎭 功能空壳检查${NC}"
check_item "无空函数体" "! grep -r 'def.*:$' src/ -A 1 | grep -B 1 'pass$' | grep -q ." "warning"
check_item "无硬编码返回值" "! grep -r 'return.*\".*\"' src/ | grep -v 'error\|message\|status' | grep -q ." "warning"

# 11. 标准逃逸检查
echo -e "\n${BLUE}⚖️ 标准逃逸检查${NC}"
check_item "无原生logging导入" "! grep -r 'import logging' src/ | grep -q ." "warning"
check_item "无原生print调用" "! grep -r 'print(' src/ | grep -v 'debug\|test' | grep -q ." "warning"

# 12. 全域版本一致性再检查
echo -e "\n${BLUE}🔄 全域版本一致性再检查${NC}"
check_item "API版本一致性" "! grep -r 'version.*[0-9]\+\.[0-9]\+\.[0-9]\+' src/api/ | grep -v '$VERSION' | grep -q ." "warning"

echo -e "\n✅ 第六轮：终局验收 (Round 6: Final Sign-off)"
echo "=================================================="

# 13. 最终状态检查
echo -e "\n${BLUE}🏁 最终状态检查${NC}"
check_item "Git状态最终确认" "git status --porcelain | wc -l | grep -q '^0$'"
check_item "主要功能模块存在" "[ -f 'src/apppro.py' ] && [ -d 'src/services' ] && [ -d 'src/ui' ]"

# 14. 文档完整性最终检查
echo -e "\n${BLUE}📚 文档完整性最终检查${NC}"
DOC_STANDARDS=(
    "POST_DEVELOPMENT_SYNC_STANDARD.md"
    "NON_ESSENTIAL_PUSH_STANDARD.md"
    "DEVELOPMENT_CLEANUP_STANDARD.md"
    "DOCUMENTATION_MAINTENANCE_STANDARD.md"
)

for doc in "${DOC_STANDARDS[@]}"; do
    check_item "标准文档: $doc" "[ -f '$doc' ]"
done

echo ""
echo "📊 检查结果统计"
echo "================"
echo -e "总检查项: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "通过: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "失败: ${RED}$FAILED_CHECKS${NC}"
echo -e "警告: ${YELLOW}$WARNING_CHECKS${NC}"

# 计算通过率
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "通过率: ${BLUE}$PASS_RATE%${NC}"
    
    if [ $PASS_RATE -ge 90 ]; then
        echo -e "\n🎉 ${GREEN}优秀！项目已通过POST_DEVELOPMENT_SYNC_STANDARD检查${NC}"
        echo "✅ 准予发布"
    elif [ $PASS_RATE -ge 80 ]; then
        echo -e "\n⚠️  ${YELLOW}良好，但建议修复失败项后再发布${NC}"
    else
        echo -e "\n❌ ${RED}需要修复关键问题后再发布${NC}"
    fi
fi

echo ""
echo "🔍 详细问题分析"
echo "================"

# 显示具体的失败项
if [ $FAILED_CHECKS -gt 0 ]; then
    echo -e "${RED}❌ 失败项需要修复：${NC}"
    # 这里可以添加具体的失败项列表
fi

if [ $WARNING_CHECKS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  警告项建议关注：${NC}"
    # 这里可以添加具体的警告项列表
fi

echo ""
echo "📋 建议后续行动"
echo "================"
echo "1. 修复所有❌失败项"
echo "2. 关注⚠️警告项"
echo "3. 运行 git status 确认状态"
echo "4. 按需执行 git push"

exit 0
