#!/bin/bash
"""
RAG Pro Max 监控系统部署脚本
一键部署监控和告警系统
"""

PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"
MONITORING_DIR="$PROJECT_ROOT/monitoring_alerts"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "🚀 部署 RAG Pro Max 监控系统"
echo "================================"

# 创建必要目录
echo "📁 创建监控目录..."
mkdir -p "$MONITORING_DIR"
mkdir -p "$SCRIPTS_DIR"

# 安装Python依赖
echo "📦 安装监控依赖..."
pip3 install psutil requests --quiet

# 设置脚本权限
echo "🔧 设置脚本权限..."
chmod +x "$PROJECT_ROOT/monitoring_system.py"
chmod +x "$SCRIPTS_DIR/daily_health_check.py"

# 创建监控配置文件
echo "⚙️ 创建监控配置..."
cat > "$MONITORING_DIR/monitoring_config.json" << EOF
{
  "thresholds": {
    "response_time": 2.0,
    "error_rate": 0.05,
    "memory_usage": 0.85,
    "disk_usage": 0.90,
    "cpu_usage": 0.80
  },
  "alerts": {
    "email": {
      "enabled": false,
      "smtp_server": "",
      "smtp_port": 587,
      "username": "",
      "password": "",
      "recipients": []
    },
    "webhook": {
      "enabled": false,
      "url": "",
      "headers": {}
    }
  },
  "schedule": {
    "health_check": "0 */6 * * *",
    "monitoring": "*/5 * * * *",
    "cleanup": "0 2 * * 0"
  }
}
EOF

# 创建监控启动脚本
echo "🎯 创建监控启动脚本..."
cat > "$SCRIPTS_DIR/start_monitoring.sh" << 'EOF'
#!/bin/bash
PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"
cd "$PROJECT_ROOT" || exit 1

echo "🔍 启动监控系统..."

# 运行健康检查
python3 scripts/daily_health_check.py

# 运行系统监控
python3 monitoring_system.py

echo "✅ 监控检查完成"
EOF

chmod +x "$SCRIPTS_DIR/start_monitoring.sh"

# 创建定时任务脚本
echo "⏰ 创建定时任务脚本..."
cat > "$SCRIPTS_DIR/setup_monitoring_cron.sh" << 'EOF'
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
EOF

chmod +x "$SCRIPTS_DIR/setup_monitoring_cron.sh"

# 运行初始健康检查
echo "🏥 运行初始健康检查..."
cd "$PROJECT_ROOT" || exit 1
python3 scripts/daily_health_check.py

# 运行初始监控检查
echo "📊 运行初始监控检查..."
python3 monitoring_system.py

echo ""
echo "🎉 监控系统部署完成！"
echo ""
echo "📋 可用命令:"
echo "  ./scripts/start_monitoring.sh     - 手动运行监控"
echo "  ./scripts/setup_monitoring_cron.sh - 设置定时任务"
echo "  python3 monitoring_system.py      - 运行系统监控"
echo "  python3 scripts/daily_health_check.py - 运行健康检查"
echo ""
echo "📁 监控数据位置: $MONITORING_DIR"
echo "⚙️ 配置文件: $MONITORING_DIR/monitoring_config.json"
