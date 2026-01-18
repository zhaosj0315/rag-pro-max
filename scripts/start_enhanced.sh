#!/bin/bash
# RAG Pro Max 增强启动脚本
# 支持网络访问和IP地址自动检测

echo "🚀 RAG Pro Max 启动中..."

# 切换到项目目录
cd /Users/zhaosj/Documents/rag-pro-max

# 强制停止已有进程
echo "🧹 清理已有进程..."
lsof -ti:8501,8502 | xargs kill -9 2>/dev/null || true
sleep 2

# 检测网络接口和IP地址
echo "🔍 检测网络配置..."
LOCAL_IPS=()

# 获取所有非回环IP地址
while IFS= read -r ip; do
    if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && [[ $ip != "127.0.0.1" ]]; then
        LOCAL_IPS+=("$ip")
    fi
done < <(ifconfig | grep -oE 'inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}')

# 显示检测到的IP
if [ ${#LOCAL_IPS[@]} -gt 0 ]; then
    echo "✅ 检测到 ${#LOCAL_IPS[@]} 个网络接口:"
    for ip in "${LOCAL_IPS[@]}"; do
        echo "   📡 $ip"
    done
else
    echo "⚠️  未检测到外部网络接口，仅支持本地访问"
fi

echo ""

# 启动应用
echo "🌐 启动应用服务..."
./scripts/start.sh &
START_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if lsof -i:8501 >/dev/null 2>&1; then
    echo "✅ 主应用服务已启动 (端口 8501)"
else
    echo "❌ 主应用服务启动失败"
    exit 1
fi

if lsof -i:8502 >/dev/null 2>&1; then
    echo "✅ API服务已启动 (端口 8502)"
    API_AVAILABLE=true
else
    echo "ℹ️  API服务未启动 (v1.8模式)"
    API_AVAILABLE=false
fi

echo ""
echo "🎉 RAG Pro Max 启动完成！"
echo ""
echo "📱 访问地址:"
echo "   🏠 本地访问:"
echo "     主应用: http://localhost:8501"
if [ "$API_AVAILABLE" = true ]; then
    echo "     API文档: http://localhost:8502/docs"
fi

if [ ${#LOCAL_IPS[@]} -gt 0 ]; then
    echo ""
    echo "   🌐 网络访问 (局域网/外网):"
    for ip in "${LOCAL_IPS[@]}"; do
        echo "     主应用: http://$ip:8501"
        if [ "$API_AVAILABLE" = true ]; then
            echo "     API文档: http://$ip:8502/docs"
        fi
        echo ""
    done
    
    echo "💡 提示:"
    echo "   • 局域网用户可通过上述IP访问"
    echo "   • 如需外网访问，请配置路由器端口转发"
    echo "   • 防火墙需开放 8501 和 8502 端口"
fi

echo ""
echo "🛑 停止服务: Ctrl+C 或运行 'pkill -f streamlit'"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $START_PID 2>/dev/null; lsof -ti:8501,8502 | xargs kill -9 2>/dev/null || true; exit 0" INT

wait $START_PID
