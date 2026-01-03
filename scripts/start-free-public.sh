#!/bin/bash
# RAG Pro Max - 一键免费公网访问
# 完全免费，无需注册，一启动就有公网地址

echo "🌐 RAG Pro Max - 一键免费公网访问"
echo "==============================="
echo ""

# 启动应用
echo "🚀 启动 RAG Pro Max..."
./scripts/start.sh &
APP_PID=$!

# 等待应用启动
echo "⏳ 等待应用启动..."
sleep 8

# 检查应用状态
if ! curl -s http://localhost:8501 > /dev/null; then
    echo "❌ 应用启动失败"
    kill $APP_PID 2>/dev/null
    exit 1
fi

echo "✅ 应用启动成功"
echo ""

# 生成随机子域名
SUBDOMAIN="rag-$(date +%s | tail -c 6)"

echo "🌐 创建免费公网隧道..."
echo "📡 正在连接..."

# 使用 serveo.net 免费服务
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -R $SUBDOMAIN:80:localhost:8501 serveo.net &
SSH_PID=$!

# 等待连接建立
sleep 3

echo ""
echo "🎉 公网地址已生成！"
echo "=================="
echo ""
echo "🌐 公网地址: https://$SUBDOMAIN.serveo.net"
echo "🏠 本地地址: http://localhost:8501"
echo ""
echo "📋 分享信息:"
echo "   ✅ 完全免费，无需注册"
echo "   ✅ 自动 HTTPS 安全访问"
echo "   ✅ 任何人都可以通过公网地址访问"
echo "   ✅ 支持多人同时使用"
echo ""
echo "📱 立即分享这个地址给其他人试用："
echo "   https://$SUBDOMAIN.serveo.net"
echo ""
echo "🛑 停止服务: 按 Ctrl+C"
echo ""

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $APP_PID $SSH_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

# 保持运行
while true; do
    sleep 1
done
