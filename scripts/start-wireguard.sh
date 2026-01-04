#!/bin/bash
# RAG Pro Max - WireGuard 隧道启动方案
# 使用 Serveo WireGuard 服务

echo "🌐 RAG Pro Max - WireGuard 隧道"
echo "=============================="
echo ""

# 检查 WireGuard 是否安装
if ! command -v wg &> /dev/null; then
    echo "❌ WireGuard 未安装"
    echo ""
    echo "📦 安装 WireGuard:"
    echo "   macOS: brew install wireguard-tools"
    echo "   Linux: sudo apt install wireguard"
    echo ""
    echo "🌐 或访问: https://console.serveo.net/wireguard/keys"
    echo "   按照控制台说明配置 WireGuard"
    exit 1
fi

echo "✅ WireGuard 已安装"
echo ""

# 检查配置文件
WG_CONFIG="/usr/local/etc/wireguard/serveo.conf"
if [ ! -f "$WG_CONFIG" ]; then
    echo "❌ WireGuard 配置文件不存在: $WG_CONFIG"
    echo ""
    echo "📋 配置步骤:"
    echo "1. 访问: https://console.serveo.net/wireguard/keys"
    echo "2. 生成或添加 WireGuard 密钥"
    echo "3. 复制配置到: $WG_CONFIG"
    echo "4. 在控制台设置 HTTP 转发规则"
    echo ""
    exit 1
fi

echo "✅ WireGuard 配置文件存在"
echo ""

# 启动应用
echo "🚀 启动 RAG Pro Max..."
./scripts/start.sh &
APP_PID=$!

echo "⏳ 等待应用启动..."
sleep 8

if ! curl -s http://localhost:8501 > /dev/null; then
    echo "❌ 应用启动失败"
    kill $APP_PID 2>/dev/null
    exit 1
fi

echo "✅ 应用启动成功"
echo ""

# 启动 WireGuard 隧道
echo "🔗 启动 WireGuard 隧道..."
sudo wg-quick up serveo

if [ $? -eq 0 ]; then
    echo "✅ WireGuard 隧道已建立"
    echo ""
    echo "🌐 访问地址:"
    echo "   • 查看 Serveo 控制台获取公网地址"
    echo "   • 本地地址: http://localhost:8501"
    echo ""
    echo "📋 说明:"
    echo "   • WireGuard 提供更稳定的连接"
    echo "   • 支持永久隧道和自定义域名"
    echo "   • 性能比 SSH 隧道更好"
    echo ""
    echo "🛑 停止服务: 按 Ctrl+C"
    
    # 等待用户中断
    trap "echo ''; echo '🛑 正在停止服务...'; sudo wg-quick down serveo; kill $APP_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT
    
    wait
else
    echo "❌ WireGuard 隧道启动失败"
    echo "💡 请检查配置文件和网络连接"
    kill $APP_PID 2>/dev/null
    exit 1
fi
