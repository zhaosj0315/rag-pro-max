#!/bin/bash
# RAG Pro Max - 简单SSH隧道

echo "🌐 RAG Pro Max - SSH隧道启动"
echo "=========================="

# 启动应用
echo "🚀 启动应用..."
./scripts/start.sh &
APP_PID=$!

echo "⏳ 等待应用启动..."
sleep 10

# 检查应用
if ! curl -s http://localhost:8501 > /dev/null; then
    echo "❌ 应用启动失败"
    kill $APP_PID 2>/dev/null
    exit 1
fi

echo "✅ 应用启动成功"
echo ""

# 启动SSH隧道 - 使用你的注册账号
echo "🌐 建立SSH隧道..."
ssh -o StrictHostKeyChecking=no -R rag-pro-max:80:localhost:8501 serveo.net &
SSH_PID=$!

sleep 3

echo ""
echo "🎉 隧道已建立！"
echo "==============="
echo ""
echo "🌐 公网地址: https://rag-pro-max.serveo.net"
echo "🏠 本地地址: http://localhost:8501"
echo ""
echo "🛑 停止服务: 按 Ctrl+C"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $APP_PID $SSH_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

wait
