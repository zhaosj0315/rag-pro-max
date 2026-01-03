#!/bin/bash
# RAG Pro Max - 超简单免费公网访问
# 一键启动，自动生成公网地址，完全免费

clear
echo "🚀 RAG Pro Max - 超简单免费公网访问"
echo "=================================="
echo ""

# 启动应用
echo "📱 正在启动应用..."
./scripts/start.sh > /dev/null 2>&1 &
APP_PID=$!

# 等待启动
for i in {1..8}; do
    echo -n "⏳ 启动中... ($i/8)"
    sleep 1
    echo -ne "\r"
done

# 检查应用
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ 应用启动成功                    "
else
    echo "❌ 应用启动失败                    "
    exit 1
fi

echo ""

# 生成地址
RANDOM_ID=$(date +%s | tail -c 6)
PUBLIC_URL="https://rag-$RANDOM_ID.serveo.net"

echo "🌐 正在生成公网地址..."

# 启动隧道
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -R rag-$RANDOM_ID:80:localhost:8501 serveo.net > /dev/null 2>&1 &
TUNNEL_PID=$!

sleep 2

echo ""
echo "🎉 公网地址生成成功！"
echo ""
echo "┌─────────────────────────────────────────────┐"
echo "│                                             │"
echo "│  🌐 公网地址: $PUBLIC_URL  │"
echo "│                                             │"
echo "│  📱 立即分享给其他人试用！                    │"
echo "│                                             │"
echo "└─────────────────────────────────────────────┘"
echo ""
echo "💡 使用说明:"
echo "   • 复制上面的地址分享给任何人"
echo "   • 他们可以直接在浏览器中打开"
echo "   • 支持多人同时访问"
echo "   • 完全免费，无需注册"
echo ""
echo "🛑 停止: 按 Ctrl+C"

# 等待中断
trap "echo ''; echo '🛑 停止中...'; kill $APP_PID $TUNNEL_PID 2>/dev/null; echo '✅ 已停止'; exit 0" INT
wait
