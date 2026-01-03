#!/bin/bash
# RAG Pro Max - ngrok 快速公网访问
# 最简单的公网访问方案

echo "🌐 RAG Pro Max - 快速公网访问"
echo "============================"
echo ""

# 检查 ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok 未安装"
    echo ""
    echo "📦 快速安装 ngrok:"
    echo ""
    echo "macOS:"
    echo "  brew install ngrok/ngrok/ngrok"
    echo ""
    echo "Linux:"
    echo "  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc"
    echo "  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "  sudo apt update && sudo apt install ngrok"
    echo ""
    echo "Windows:"
    echo "  下载: https://ngrok.com/download"
    echo ""
    echo "安装后运行:"
    echo "  1. 注册 https://ngrok.com"
    echo "  2. 获取 authtoken"
    echo "  3. 运行: ngrok authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "✅ ngrok 已安装"
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

# 启动 ngrok
echo "🌐 创建公网隧道..."
ngrok http 8501 &
NGROK_PID=$!

# 等待 ngrok 启动
sleep 3

# 获取公网地址
echo "📡 获取公网地址..."
sleep 2

PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('tunnels') and len(data['tunnels']) > 0:
        print(data['tunnels'][0]['public_url'])
    else:
        print('未获取到')
except:
    print('解析失败')
" 2>/dev/null)

if [ "$PUBLIC_URL" = "未获取到" ] || [ "$PUBLIC_URL" = "解析失败" ] || [ -z "$PUBLIC_URL" ]; then
    echo ""
    echo "⚠️  自动获取公网地址失败"
    echo "📊 请手动查看 ngrok 控制台: http://localhost:4040"
    echo ""
else
    echo ""
    echo "🎉 公网访问已就绪！"
    echo "=================="
    echo ""
    echo "🌐 公网地址: $PUBLIC_URL"
    echo "🏠 本地地址: http://localhost:8501"
    echo "📊 ngrok 控制台: http://localhost:4040"
    echo ""
fi

echo "📋 使用说明:"
echo "   • 分享公网地址给其他人即可访问"
echo "   • 免费版本有连接数和带宽限制"
echo "   • 重启后地址会改变"
echo "   • 支持 HTTPS 安全访问"
echo ""
echo "🛑 停止服务: 按 Ctrl+C"
echo ""

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $APP_PID $NGROK_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

# 保持运行
while true; do
    sleep 1
done
