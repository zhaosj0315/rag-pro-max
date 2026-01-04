#!/bin/bash
# RAG Pro Max - 过程性文件安全清理脚本
# 按照POST_DEVELOPMENT_SYNC_STANDARD执行深度清理

echo "🧹 RAG Pro Max - 过程性文件清理"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
DELETED_DIRS=0
DELETED_FILES=0
TOTAL_SIZE=0

# 安全删除函数
safe_delete() {
    local path="$1"
    local type="$2" # "dir" or "file"
    
    if [ ! -e "$path" ]; then
        echo -e "  ${YELLOW}⚠️  路径不存在: $path${NC}"
        return 1
    fi
    
    # 计算大小
    if [ "$type" = "dir" ]; then
        size=$(du -sh "$path" 2>/dev/null | cut -f1)
        echo -e "  ${BLUE}📁 删除目录: $path ($size)${NC}"
        rm -rf "$path"
        DELETED_DIRS=$((DELETED_DIRS + 1))
    else
        size=$(ls -lh "$path" 2>/dev/null | awk '{print $5}')
        echo -e "  ${BLUE}📄 删除文件: $path ($size)${NC}"
        rm -f "$path"
        DELETED_FILES=$((DELETED_FILES + 1))
    fi
}

# 确认删除
echo -e "${YELLOW}⚠️  即将删除以下过程性文件和目录:${NC}"
echo ""
echo "📁 目录:"
echo "  - work_plans/ (开发计划文件)"
echo "  - monitoring_alerts/ (监控告警历史)"
echo "  - .cleanup_backup/ (清理备份)"
echo "  - .ultra_conservative_backup/ (超保守备份)"
echo ""
echo "📄 文件:"
echo "  - iteration_log.json (迭代日志)"
echo "  - V2_ITERATION_PRACTICE_RECORD.md (实践记录)"
echo "  - start_task.py (任务启动器)"
echo "  - question_recommender.py (问题推荐器)"
echo "  - monitoring_system.py (监控系统)"
echo "  - existing_feature_protector.py (功能保护器)"
echo "  - error_handler.py (错误处理器)"
echo "  - intelligent_planner.py (智能规划器)"
echo "  - optimization_dashboard.py (优化仪表板)"
echo "  - optimization_scheduler.sh (优化调度器)"
echo "  - intelligent_project_manager.sh (智能项目管理器)"
echo "  - optimization_config.yaml (优化配置)"
echo "  - DOCUMENT_QUALITY_ASSESSMENT_GUIDE.md (文档质量评估指南)"
echo ""

read -p "确认删除这些过程性文件? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ 取消删除操作${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}🚀 开始清理过程性文件...${NC}"
echo ""

# 删除目录
echo -e "${BLUE}📁 清理过程性目录${NC}"
safe_delete "work_plans" "dir"
safe_delete "monitoring_alerts" "dir"
safe_delete ".cleanup_backup" "dir"
safe_delete ".ultra_conservative_backup" "dir"

echo ""

# 删除文件
echo -e "${BLUE}📄 清理过程性文件${NC}"
safe_delete "iteration_log.json" "file"
safe_delete "V2_ITERATION_PRACTICE_RECORD.md" "file"
safe_delete "start_task.py" "file"
safe_delete "question_recommender.py" "file"
safe_delete "monitoring_system.py" "file"
safe_delete "existing_feature_protector.py" "file"
safe_delete "error_handler.py" "file"
safe_delete "intelligent_planner.py" "file"
safe_delete "optimization_dashboard.py" "file"
safe_delete "optimization_scheduler.sh" "file"
safe_delete "intelligent_project_manager.sh" "file"
safe_delete "optimization_config.yaml" "file"
safe_delete "DOCUMENT_QUALITY_ASSESSMENT_GUIDE.md" "file"

echo ""
echo -e "${GREEN}✅ 清理完成!${NC}"
echo ""
echo "📊 清理统计:"
echo -e "  删除目录: ${GREEN}$DELETED_DIRS${NC} 个"
echo -e "  删除文件: ${GREEN}$DELETED_FILES${NC} 个"
echo ""

# 检查Git状态
echo -e "${BLUE}📋 检查Git状态${NC}"
git status --porcelain | head -10

echo ""
echo -e "${GREEN}🎉 过程性文件清理完成!${NC}"
echo "项目现在更加纯净，符合POST_DEVELOPMENT_SYNC_STANDARD要求"

exit 0
