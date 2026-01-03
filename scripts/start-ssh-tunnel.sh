#!/bin/bash
# RAG Pro Max - SSH 隧道公网访问 (无需安装)
# 使用 serveo.net 提供免费 SSH 隧道服务

echo "🌐 RAG Pro Max - SSH 隧道公网访问"
echo "==============================="
echo "使用 serveo.net 免费服务 (无需安装任何软件)"
echo ""

# 检查 SSH
if ! command -v ssh &> /dev/null; then
    echo "❌ SSH 未安装 (系统异常，SSH 应该是系统自带)"
    exit 1
fi

echo "✅ SSH 可用"
echo ""

# 启动应用
echo "🚀 启动 RAG Pro Max..."
./scripts/start.sh &
APP_PID=$!

# 等待应用启动
echo "⏳ 等待应用启动 (10秒)..."
sleep 10

# 检查应用状态
if ! curl -s http://localhost:8501 > /dev/null; then
    echo "❌ 应用启动失败，请检查错误信息"
    kill $APP_PID 2>/dev/null
    exit 1
fi

echo "✅ 应用启动成功"
echo ""

# 生成随机子域名
SUBDOMAIN="rag-pro-max-$(date +%s | tail -c 6)"

echo "🌐 创建 SSH 隧道..."
echo "📡 连接到 serveo.net..."
echo ""

# 启动 SSH 隧道
ssh -o StrictHostKeyChecking=no -R $SUBDOMAIN:80:localhost:8501 serveo.net &
SSH_PID=$!

# 等待连接建立
sleep 3

echo ""
echo "🎉 公网访问已就绪！"
echo "=================="
echo ""
echo "🌐 公网地址: https://$SUBDOMAIN.serveo.net"
echo "🏠 本地地址: http://localhost:8501"
echo ""
echo "📋 使用说明:"
echo "   • 完全免费，无需注册"
echo "   • 基于 SSH，安全可靠"
echo "   • 支持 HTTPS 访问"
echo "   • 分享地址给其他人即可访问"
echo ""
echo "⚠️  注意事项:"
echo "   • 首次连接可能需要几秒钟"
echo "   • 如果地址无法访问，请重新运行脚本"
echo "   • 重启后地址会改变"
echo ""
echo "🛑 停止服务: 按 Ctrl+C"
echo ""

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $APP_PID $SSH_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

# 保持运行
while true; do
    sleep 1
done
