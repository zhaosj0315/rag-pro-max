#!/bin/bash
# RAG Pro Max 项目管理脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${CYAN}🎯 RAG Pro Max 项目管理工具${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
    echo -e "${YELLOW}用法:${NC} ./manage.sh [命令]"
    echo ""
    echo -e "${YELLOW}可用命令:${NC}"
    echo -e "  ${GREEN}sync${NC}        - 执行完整项目同步"
    echo -e "  ${GREEN}start${NC}       - 启动应用程序"
    echo -e "  ${GREEN}test${NC}        - 运行测试"
    echo -e "  ${GREEN}status${NC}      - 检查项目状态"
    echo -e "  ${GREEN}backup${NC}      - 创建项目备份"
    echo -e "  ${GREEN}clean${NC}       - 清理临时文件"
    echo -e "  ${GREEN}install${NC}     - 安装依赖"
    echo -e "  ${GREEN}help${NC}        - 显示此帮助信息"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo -e "  ./manage.sh sync     # 同步所有代码和文档"
    echo -e "  ./manage.sh start    # 启动RAG Pro Max应用"
    echo -e "  ./manage.sh status   # 查看项目状态"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        exit 1
    fi
    
    if ! python3 -c "import streamlit" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Streamlit 未安装，正在安装依赖...${NC}"
        pip3 install -r requirements.txt
    fi
}

# 执行完整同步
run_sync() {
    echo -e "${BLUE}🚀 执行完整项目同步...${NC}"
    python3 master_sync.py
    echo -e "${GREEN}✅ 同步完成!${NC}"
}

# 启动应用
start_app() {
    echo -e "${BLUE}🚀 启动 RAG Pro Max 应用...${NC}"
    check_python
    
    # 设置环境变量
    export PADDLE_LOG_LEVEL=50
    export GLOG_minloglevel=3
    export OMP_NUM_THREADS=1
    export OPENBLAS_NUM_THREADS=1
    
    echo -e "${GREEN}📱 应用将在浏览器中打开: http://localhost:8501${NC}"
    streamlit run src/apppro.py
}

# 运行测试
run_tests() {
    echo -e "${BLUE}🧪 运行项目测试...${NC}"
    
    if [ -f "tests/factory_test.py" ]; then
        python3 tests/factory_test.py
    else
        echo -e "${YELLOW}⚠️  测试文件不存在${NC}"
    fi
}

# 检查项目状态
check_status() {
    echo -e "${BLUE}🔍 检查项目状态...${NC}"
    echo ""
    
    # 检查核心文件
    echo -e "${YELLOW}核心文件状态:${NC}"
    files=("src/apppro.py" "README.md" "requirements.txt" "CHANGELOG.md")
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            echo -e "  ✅ $file (${size} bytes)"
        else
            echo -e "  ❌ $file (缺失)"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}目录结构:${NC}"
    dirs=("src" "config" "sync_results" "backups")
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            count=$(find "$dir" -type f | wc -l | tr -d ' ')
            echo -e "  ✅ $dir/ (${count} 个文件)"
        else
            echo -e "  ❌ $dir/ (不存在)"
        fi
    done
    
    echo ""
    echo -e "${YELLOW}最近同步记录:${NC}"
    if [ -d "sync_results" ]; then
        ls -lt sync_results/master_sync_summary_*.md 2>/dev/null | head -3 | while read line; do
            echo -e "  📋 $(echo $line | awk '{print $9}' | sed 's/.*\///')"
        done
    else
        echo -e "  📋 无同步记录"
    fi
}

# 创建备份
create_backup() {
    echo -e "${BLUE}💾 创建项目备份...${NC}"
    python3 sync_codebase.py
    echo -e "${GREEN}✅ 备份完成!${NC}"
}

# 清理临时文件
clean_temp() {
    echo -e "${BLUE}🧹 清理临时文件...${NC}"
    
    # 清理Python缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理临时上传文件
    if [ -d "temp_uploads" ]; then
        find temp_uploads -type f -mtime +7 -delete 2>/dev/null || true
        echo -e "  🗑️  清理了7天前的临时上传文件"
    fi
    
    # 清理旧日志
    if [ -d "app_logs" ]; then
        find app_logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
        echo -e "  🗑️  清理了30天前的日志文件"
    fi
    
    echo -e "${GREEN}✅ 清理完成!${NC}"
}

# 安装依赖
install_deps() {
    echo -e "${BLUE}📦 安装项目依赖...${NC}"
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        echo -e "${GREEN}✅ 依赖安装完成!${NC}"
    else
        echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
        exit 1
    fi
}

# 主逻辑
case "${1:-help}" in
    "sync")
        run_sync
        ;;
    "start")
        start_app
        ;;
    "test")
        run_tests
        ;;
    "status")
        check_status
        ;;
    "backup")
        create_backup
        ;;
    "clean")
        clean_temp
        ;;
    "install")
        install_deps
        ;;
    "help"|*)
        show_help
        ;;
esac
