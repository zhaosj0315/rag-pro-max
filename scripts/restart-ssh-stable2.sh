#!/bin/bash

LOG_FILE="/tmp/ssh-stable2-restart.log"
SCRIPT_NAME="start-ssh-stable2.sh"
PROJECT_DIR="/Users/zhaosj/Documents/rag-pro-max"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查是否有活跃的SSH连接
if netstat -an | grep -q ":22.*ESTABLISHED"; then
    log "Active SSH connections detected, skipping restart"
    exit 0
fi

# 优雅停止
if pgrep -f "$SCRIPT_NAME" > /dev/null; then
    log "Stopping existing $SCRIPT_NAME processes"
    pkill -TERM -f "$SCRIPT_NAME"
    sleep 5
    # 如果还在运行，强制杀死
    pkill -KILL -f "$SCRIPT_NAME" 2>/dev/null
fi

# 启动服务
log "Starting $SCRIPT_NAME"
cd "$PROJECT_DIR" && ./scripts/"$SCRIPT_NAME" >> "$LOG_FILE" 2>&1 &

log "Restart completed"
