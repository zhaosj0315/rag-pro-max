#!/bin/bash
# RAG Pro Max - 免费公网访问 (localtunnel版本)
# 如果有 Node.js，使用 localtunnel；否则使用 SSH 隧道

echo "🌐 RAG Pro Max - 免费公网访问"
echo "=========================="
echo ""

# 启动应用
echo "🚀 启动应用..."
./scripts/start.sh > /dev/null 2>&1 &
APP_PID=$!

# 等待启动
echo "⏳ 等待启动..."
sleep 8

if ! curl -s http://localhost:8501 > /dev/null; then
    echo "❌ 应用启动失败"
    exit 1
fi

echo "✅ 应用启动成功"
echo ""

# 检查是否有 Node.js 和 npm
if command -v npm &> /dev/null; then
    echo "📦 检测到 Node.js，使用 localtunnel..."
    
    # 安装 localtunnel (如果没有)
    if ! command -v lt &> /dev/null; then
        echo "📥 安装 localtunnel..."
        npm install -g localtunnel > /dev/null 2>&1
    fi
    
    # 生成随机子域名
    SUBDOMAIN="rag-pro-max-$(date +%s | tail -c 6)"
    
    echo "🌐 创建 localtunnel 隧道..."
    lt --port 8501 --subdomain $SUBDOMAIN > /dev/null 2>&1 &
    LT_PID=$!
    
    sleep 3
    
    PUBLIC_URL="https://$SUBDOMAIN.loca.lt"
    
    echo ""
    echo "🎉 公网地址已生成！"
    echo "=================="
    echo ""
    echo "🌐 公网地址: $PUBLIC_URL"
    echo ""
    echo "📋 说明:"
    echo "   • 首次访问需要点击 'Click to Continue'"
    echo "   • 完全免费，无需注册"
    echo "   • 分享地址给其他人即可访问"
    echo ""
    
    # 等待中断
    trap "echo '🛑 停止中...'; kill $APP_PID $LT_PID 2>/dev/null; exit 0" INT
    wait
    
else
    echo "🔧 使用 SSH 隧道 (无需安装)..."
    
    # 生成随机子域名
    SUBDOMAIN="rag-$(date +%s | tail -c 6)"
    
    echo "🌐 创建 SSH 隧道..."
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -R $SUBDOMAIN:80:localhost:8501 serveo.net > /dev/null 2>&1 &
    SSH_PID=$!
    
    sleep 3
    
    PUBLIC_URL="https://$SUBDOMAIN.serveo.net"
    
    echo ""
    echo "🎉 公网地址已生成！"
    echo "=================="
    echo ""
    echo "🌐 公网地址: $PUBLIC_URL"
    echo ""
    echo "📋 说明:"
    echo "   • 完全免费，无需注册"
    echo "   • 自动 HTTPS 安全访问"
    echo "   • 分享地址给其他人即可访问"
    echo ""
    
    # 等待中断
    trap "echo '🛑 停止中...'; kill $APP_PID $SSH_PID 2>/dev/null; exit 0" INT
    wait
fi
