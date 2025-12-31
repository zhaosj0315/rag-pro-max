#!/bin/bash
PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"

echo "⚙️ 设置监控定时任务..."

# 备份现有crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# 添加监控任务
(crontab -l 2>/dev/null; cat << CRON
# RAG Pro Max 监控任务
0 */6 * * * $PROJECT_ROOT/scripts/daily_health_check.py >> $PROJECT_ROOT/monitoring_alerts/health_check.log 2>&1
*/30 * * * * $PROJECT_ROOT/monitoring_system.py >> $PROJECT_ROOT/monitoring_alerts/monitoring.log 2>&1
0 2 * * 0 find $PROJECT_ROOT/monitoring_alerts -name "*.json" -mtime +30 -delete
CRON
) | crontab -

echo "✅ 定时任务设置完成"
echo "📋 当前定时任务:"
crontab -l | grep "RAG Pro Max" -A 3
