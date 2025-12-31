#!/bin/bash
"""
RAG Pro Max 持续优化调度器
定期运行优化循环，实现良性循环机制
"""

# 配置参数
PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"
OPTIMIZATION_SCRIPT="$PROJECT_ROOT/continuous_optimization_system.py"
LOG_FILE="$PROJECT_ROOT/optimization_reports/scheduler.log"
LOCK_FILE="$PROJECT_ROOT/optimization_reports/scheduler.lock"

# 创建必要目录
mkdir -p "$PROJECT_ROOT/optimization_reports"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查锁文件
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "优化进程正在运行 (PID: $pid)，跳过本次执行"
            exit 0
        else
            log "发现僵尸锁文件，清理中..."
            rm -f "$LOCK_FILE"
        fi
    fi
}

# 创建锁文件
create_lock() {
    echo $$ > "$LOCK_FILE"
}

# 清理锁文件
cleanup_lock() {
    rm -f "$LOCK_FILE"
}

# 运行优化循环
run_optimization() {
    log "🚀 开始优化循环"
    
    cd "$PROJECT_ROOT" || exit 1
    
    # 运行优化脚本
    if python3 "$OPTIMIZATION_SCRIPT" "$PROJECT_ROOT"; then
        log "✅ 优化循环完成"
        return 0
    else
        log "❌ 优化循环失败"
        return 1
    fi
}

# 清理旧报告
cleanup_old_reports() {
    local reports_dir="$PROJECT_ROOT/optimization_reports"
    local days_to_keep=30
    
    log "🧹 清理 $days_to_keep 天前的旧报告"
    find "$reports_dir" -name "optimization_report_*.json" -mtime +$days_to_keep -delete
    find "$reports_dir" -name "*.log" -mtime +$days_to_keep -delete
}

# 主函数
main() {
    log "📋 RAG Pro Max 优化调度器启动"
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log "❌ Python3 未找到"
        exit 1
    fi
    
    # 检查优化脚本
    if [ ! -f "$OPTIMIZATION_SCRIPT" ]; then
        log "❌ 优化脚本未找到: $OPTIMIZATION_SCRIPT"
        exit 1
    fi
    
    # 检查锁文件
    check_lock
    
    # 创建锁文件
    create_lock
    trap cleanup_lock EXIT
    
    # 运行优化
    if run_optimization; then
        # 清理旧报告
        cleanup_old_reports
        log "🎉 调度任务完成"
    else
        log "💥 调度任务失败"
        exit 1
    fi
}

# 如果直接运行此脚本
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
