#!/bin/bash
PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"
cd "$PROJECT_ROOT" || exit 1

echo "🔍 启动监控系统..."

# 运行健康检查
python3 scripts/daily_health_check.py

# 运行系统监控
python3 monitoring_system.py

echo "✅ 监控检查完成"
