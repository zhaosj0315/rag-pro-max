#!/bin/bash
# GitHub 推送前安全检查脚本
# 版本: v1.0
# 基于: NON_ESSENTIAL_PUSH_STANDARD.md

set -e

echo "🔒 GitHub 推送前安全检查"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查计数
ISSUES=0

# 1. 检查是否有私有数据目录
echo "📋 [1/5] 检查私有数据目录..."
PRIVATE_DIRS=(
    "vector_db_storage"
    "chat_histories"
    "app_logs"
    "temp_uploads"
    "hf_cache"
    "exports"
)

for dir in "${PRIVATE_DIRS[@]}"; do
    if git ls-files --error-unmatch "$dir" >/dev/null 2>&1; then
        echo -e "  ${RED}✗${NC} 发现私有目录: $dir"
        ISSUES=$((ISSUES + 1))
    fi
done

if [ $ISSUES -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} 无私有数据目录"
fi

# 2. 检查配置文件
echo ""
echo "📋 [2/5] 检查配置文件..."
CONFIG_FILES=(
    "config/sessions.json"
    "config/users.json"
    "config/app_config.json"
    "config/alert_history.json"
)

for file in "${CONFIG_FILES[@]}"; do
    if git diff --cached --name-only | grep -q "$file"; then
        echo -e "  ${YELLOW}⚠️${NC}  配置文件将被推送: $file"
        echo "     建议: 确认是否包含敏感信息"
    fi
done

# 3. 检查临时文件
echo ""
echo "📋 [3/5] 检查临时文件..."
TEMP_PATTERNS=(
    "*.tmp"
    "*.temp"
    "*_backup.py"
    "*_old.py"
    "crawler_state*.json"
    "test_*_output"
)

for pattern in "${TEMP_PATTERNS[@]}"; do
    if git ls-files --error-unmatch $pattern >/dev/null 2>&1; then
        echo -e "  ${RED}✗${NC} 发现临时文件: $pattern"
        ISSUES=$((ISSUES + 1))
    fi
done

if [ $ISSUES -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} 无临时文件"
fi

# 4. 检查大文件
echo ""
echo "📋 [4/5] 检查大文件 (>1MB)..."
LARGE_FILES=$(find . -type f -size +1M ! -path "./.git/*" ! -path "./vector_db_storage/*" ! -path "./chat_histories/*" ! -path "./temp_uploads/*" ! -path "./hf_cache/*" 2>/dev/null)

if [ -n "$LARGE_FILES" ]; then
    echo -e "  ${YELLOW}⚠️${NC}  发现大文件:"
    echo "$LARGE_FILES" | while read file; do
        SIZE=$(du -h "$file" | cut -f1)
        echo "     - $file ($SIZE)"
    done
else
    echo -e "  ${GREEN}✓${NC} 无大文件"
fi

# 5. 检查 .gitignore
echo ""
echo "📋 [5/5] 检查 .gitignore..."
if [ -f ".gitignore" ]; then
    # 检查必需的规则
    REQUIRED_RULES=(
        "vector_db_storage"
        "chat_histories"
        "temp_uploads"
        "app_logs"
        "config/sessions.json"
        "config/users.json"
    )
    
    MISSING=0
    for rule in "${REQUIRED_RULES[@]}"; do
        if ! grep -q "$rule" .gitignore; then
            echo -e "  ${RED}✗${NC} .gitignore 缺少规则: $rule"
            MISSING=$((MISSING + 1))
        fi
    done
    
    if [ $MISSING -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} .gitignore 规则完整"
    else
        ISSUES=$((ISSUES + MISSING))
    fi
else
    echo -e "  ${RED}✗${NC} .gitignore 文件不存在"
    ISSUES=$((ISSUES + 1))
fi

# 总结
echo ""
echo "=================================="
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ 安全检查通过！可以推送${NC}"
    echo "=================================="
    exit 0
else
    echo -e "${RED}❌ 发现 $ISSUES 个问题，请修复后再推送${NC}"
    echo "=================================="
    exit 1
fi
