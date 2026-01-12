#!/bin/bash
# RAG Pro Max - 稳定SSH隧道

echo "🌐 RAG Pro Max - 稳定SSH隧道"
echo "=========================="

# 启动应用（跳过测试）
echo "🚀 启动应用..."
cd /Users/zhaosj/Documents/rag-pro-max
export PYTHONPATH="${PWD}:${PYTHONPATH}"
streamlit run src/apppro.py --server.port 8501 > /dev/null 2>&1 &
APP_PID=$!

echo "⏳ 等待应用启动..."
sleep 15

echo "✅ 应用启动完成"
echo ""

# 启动SSH隧道
echo "🌐 建立SSH隧道..."
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R rag-pro-max:80:localhost:8501 serveo.net &
SSH_PID=$!

sleep 5

echo ""
echo "🎉 隧道已建立！"
echo "==============="
echo ""
echo "🌐 公网地址: https://rag-pro-max.serveousercontent.com"
echo "🏠 本地地址: http://localhost:8501"
echo ""
echo "🛑 停止服务: 按 Ctrl+C"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $APP_PID $SSH_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

wait
