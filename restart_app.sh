#!/bin/bash
"""
重启应用以应用推荐问题日志修复
"""

echo "🔄 重启 RAG Pro Max 应用..."

# 查找并终止现有的streamlit进程
echo "📋 查找现有进程..."
PIDS=$(ps aux | grep "streamlit run src/apppro.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$PIDS" ]; then
    echo "🛑 终止现有进程: $PIDS"
    echo $PIDS | xargs kill
    sleep 2
else
    echo "ℹ️ 未找到运行中的应用"
fi

# 启动应用
echo "🚀 启动应用..."
streamlit run src/apppro.py &

echo "✅ 应用已重启"
echo "💡 现在日志中会显示具体的推荐问题内容"
echo "📋 查看日志: tail -f app_logs/log_$(date +%Y%m%d).jsonl"
