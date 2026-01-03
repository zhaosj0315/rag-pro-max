#!/bin/bash
# RAG Pro Max 公网访问启动脚本
# 基于现有代码，不修改任何源码，提供公网访问能力

echo "🌐 RAG Pro Max - 公网访问启动"
echo "=============================="
echo "版本: v3.2.2"
echo "执行时间: $(date)"
echo ""

# 检查依赖
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ 缺少依赖: $1"
        return 1
    fi
    return 0
}

# 方案选择菜单
echo "🚀 选择公网访问方案:"
echo "1. ngrok 隧道 (推荐) - 免费，稳定"
echo "2. localtunnel - 免费，简单"
echo "3. serveo.net - 免费，无需安装"
echo "4. 自定义端口 + 防火墙配置"
echo "5. 查看所有方案说明"
echo ""

read -p "请选择方案 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔥 方案1: ngrok 隧道"
        echo "==================="
        
        if ! check_dependency "ngrok"; then
            echo "📦 ngrok 未安装，正在提供安装指导..."
            echo ""
            echo "安装 ngrok:"
            echo "1. 访问 https://ngrok.com/download"
            echo "2. 下载适合你系统的版本"
            echo "3. 解压并添加到 PATH"
            echo "4. 注册账号获取 authtoken"
            echo "5. 运行: ngrok authtoken YOUR_TOKEN"
            echo ""
            echo "快速安装 (macOS):"
            echo "brew install ngrok/ngrok/ngrok"
            echo ""
            echo "快速安装 (Linux):"
            echo "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
            echo "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
            echo "sudo apt update && sudo apt install ngrok"
            exit 1
        fi
        
        echo "✅ ngrok 已安装"
        echo ""
        echo "🚀 启动 RAG Pro Max..."
        
        # 启动应用 (后台)
        ./scripts/start.sh &
        APP_PID=$!
        
        # 等待应用启动
        echo "⏳ 等待应用启动..."
        sleep 10
        
        # 检查应用是否启动成功
        if curl -s http://localhost:8501 > /dev/null; then
            echo "✅ 应用启动成功"
        else
            echo "❌ 应用启动失败"
            kill $APP_PID 2>/dev/null
            exit 1
        fi
        
        echo ""
        echo "🌐 创建 ngrok 隧道..."
        ngrok http 8501 --log=stdout &
        NGROK_PID=$!
        
        # 等待 ngrok 启动
        sleep 5
        
        # 获取公网地址
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('获取失败')
")
        
        if [ "$PUBLIC_URL" != "获取失败" ]; then
            echo ""
            echo "🎉 公网访问地址创建成功！"
            echo "================================"
            echo "🌐 公网地址: $PUBLIC_URL"
            echo "🏠 本地地址: http://localhost:8501"
            echo "📊 ngrok 控制台: http://localhost:4040"
            echo ""
            echo "📋 分享信息:"
            echo "   • 任何人都可以通过公网地址访问"
            echo "   • 免费版本有连接数限制"
            echo "   • 地址在重启后会改变"
            echo ""
            echo "🛑 停止服务: Ctrl+C"
        else
            echo "❌ 无法获取公网地址，请检查 ngrok 配置"
            kill $APP_PID $NGROK_PID 2>/dev/null
            exit 1
        fi
        
        # 等待用户中断
        trap "echo '🛑 正在停止服务...'; kill $APP_PID $NGROK_PID 2>/dev/null; exit 0" INT
        wait
        ;;
        
    2)
        echo ""
        echo "🔥 方案2: localtunnel"
        echo "==================="
        
        if ! check_dependency "lt"; then
            echo "📦 localtunnel 未安装，正在安装..."
            if check_dependency "npm"; then
                npm install -g localtunnel
            else
                echo "❌ 需要先安装 Node.js 和 npm"
                echo "访问: https://nodejs.org/"
                exit 1
            fi
        fi
        
        echo "✅ localtunnel 已安装"
        echo ""
        echo "🚀 启动 RAG Pro Max..."
        
        # 启动应用 (后台)
        ./scripts/start.sh &
        APP_PID=$!
        
        # 等待应用启动
        echo "⏳ 等待应用启动..."
        sleep 10
        
        echo ""
        echo "🌐 创建 localtunnel 隧道..."
        lt --port 8501 --subdomain rag-pro-max-$(date +%s) &
        LT_PID=$!
        
        echo ""
        echo "🎉 localtunnel 隧道创建成功！"
        echo "================================"
        echo "🌐 公网地址将在上方显示"
        echo "🏠 本地地址: http://localhost:8501"
        echo ""
        echo "📋 使用说明:"
        echo "   • 首次访问需要点击确认"
        echo "   • 免费使用，无需注册"
        echo "   • 地址在重启后会改变"
        echo ""
        echo "🛑 停止服务: Ctrl+C"
        
        # 等待用户中断
        trap "echo '🛑 正在停止服务...'; kill $APP_PID $LT_PID 2>/dev/null; exit 0" INT
        wait
        ;;
        
    3)
        echo ""
        echo "🔥 方案3: serveo.net SSH 隧道"
        echo "============================"
        
        if ! check_dependency "ssh"; then
            echo "❌ SSH 未安装"
            exit 1
        fi
        
        echo "✅ SSH 可用"
        echo ""
        echo "🚀 启动 RAG Pro Max..."
        
        # 启动应用 (后台)
        ./scripts/start.sh &
        APP_PID=$!
        
        # 等待应用启动
        echo "⏳ 等待应用启动..."
        sleep 10
        
        echo ""
        echo "🌐 创建 serveo.net 隧道..."
        
        # 生成随机子域名
        SUBDOMAIN="rag-pro-max-$(date +%s)"
        
        echo "ssh -R $SUBDOMAIN:80:localhost:8501 serveo.net"
        ssh -R $SUBDOMAIN:80:localhost:8501 serveo.net &
        SSH_PID=$!
        
        echo ""
        echo "🎉 serveo.net 隧道创建成功！"
        echo "================================"
        echo "🌐 公网地址: https://$SUBDOMAIN.serveo.net"
        echo "🏠 本地地址: http://localhost:8501"
        echo ""
        echo "📋 使用说明:"
        echo "   • 完全免费，无需注册"
        echo "   • 基于 SSH，安全可靠"
        echo "   • 地址在重启后会改变"
        echo ""
        echo "🛑 停止服务: Ctrl+C"
        
        # 等待用户中断
        trap "echo '🛑 正在停止服务...'; kill $APP_PID $SSH_PID 2>/dev/null; exit 0" INT
        wait
        ;;
        
    4)
        echo ""
        echo "🔥 方案4: 自定义端口 + 防火墙配置"
        echo "==============================="
        echo ""
        echo "📋 配置步骤:"
        echo "1. 修改 Streamlit 配置允许外部访问"
        echo "2. 配置防火墙开放端口"
        echo "3. 获取公网 IP"
        echo ""
        
        # 创建临时配置文件
        mkdir -p ~/.streamlit
        cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
port = 8501

[browser]
gatherUsageStats = false
EOF
        
        echo "✅ Streamlit 配置已更新"
        echo ""
        echo "🚀 启动 RAG Pro Max (允许外部访问)..."
        
        # 启动应用，允许外部访问
        streamlit run src/apppro.py --server.address 0.0.0.0 --server.port 8501 &
        APP_PID=$!
        
        # 获取本机 IP
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
        
        echo ""
        echo "🎉 应用已启动 (允许外部访问)！"
        echo "================================"
        echo "🏠 本地访问: http://localhost:8501"
        echo "🌐 局域网访问: http://$LOCAL_IP:8501"
        echo ""
        echo "📋 公网访问配置:"
        echo "1. 配置路由器端口转发 (8501 -> $LOCAL_IP:8501)"
        echo "2. 或配置防火墙开放 8501 端口"
        echo "3. 使用公网 IP 访问: http://YOUR_PUBLIC_IP:8501"
        echo ""
        echo "⚠️  安全提醒:"
        echo "   • 公网访问存在安全风险"
        echo "   • 建议设置访问密码或 IP 白名单"
        echo "   • 仅在需要时开放公网访问"
        echo ""
        echo "🛑 停止服务: Ctrl+C"
        
        # 等待用户中断
        trap "echo '🛑 正在停止服务...'; kill $APP_PID 2>/dev/null; exit 0" INT
        wait
        ;;
        
    5)
        echo ""
        echo "📚 所有公网访问方案说明"
        echo "======================"
        echo ""
        echo "🔥 方案1: ngrok (推荐)"
        echo "   优点: 稳定、功能丰富、HTTPS支持"
        echo "   缺点: 需要注册、免费版有限制"
        echo "   适用: 正式演示、长期使用"
        echo ""
        echo "🔥 方案2: localtunnel"
        echo "   优点: 简单、无需注册"
        echo "   缺点: 需要 Node.js、稳定性一般"
        echo "   适用: 快速测试、临时分享"
        echo ""
        echo "🔥 方案3: serveo.net"
        echo "   优点: 完全免费、基于SSH、无需安装"
        echo "   缺点: 依赖第三方服务"
        echo "   适用: 临时演示、快速分享"
        echo ""
        echo "🔥 方案4: 自定义配置"
        echo "   优点: 完全控制、无第三方依赖"
        echo "   缺点: 需要网络配置知识、安全风险"
        echo "   适用: 企业内网、有公网IP的服务器"
        echo ""
        echo "💡 推荐选择:"
        echo "   • 演示用途: 选择方案1 (ngrok)"
        echo "   • 快速测试: 选择方案3 (serveo.net)"
        echo "   • 企业部署: 选择方案4 (自定义)"
        echo ""
        echo "重新运行脚本选择具体方案"
        ;;
        
    *)
        echo "❌ 无效选择，请重新运行脚本"
        exit 1
        ;;
esac
