#!/bin/bash
# RAG Pro Max 新实例启动脚本 - 不杀死现有进程

echo "🚀 启动新的 RAG Pro Max 实例..."

# 智能端口检测 - 不杀死现有进程
find_available_port() {
    local start_port=${1:-8501}
    local port=$start_port
    
    echo "🔍 检测可用端口..."
    while [ $port -le 8520 ]; do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
        echo "   端口 $port 已被占用，跳过..."
        ((port++))
    done
    
    echo "❌ 端口 8501-8520 都被占用"
    return 1
}

# 查找可用端口
AVAILABLE_PORT=$(find_available_port 8501)
if [ $? -ne 0 ]; then
    echo "❌ 无法找到可用端口，请手动释放一些端口"
    exit 1
fi

echo "✅ 找到可用端口: $AVAILABLE_PORT"
echo "🌐 新实例将在端口 $AVAILABLE_PORT 启动"
echo "📱 访问地址: http://localhost:$AVAILABLE_PORT"
echo ""

# 显示现有实例
echo "📋 当前运行的实例:"
ps aux | grep "streamlit run" | grep -v grep | while read line; do
    echo "   $line"
done
echo ""

# 启动新实例
echo "🚀 启动新实例..."
streamlit run src/apppro.py --server.port $AVAILABLE_PORT --server.headless=false

echo "🎉 新实例启动完成！"
