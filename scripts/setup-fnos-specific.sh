#!/bin/bash
# RAG Pro Max - 飞牛NAS端口映射配置 (针对 192.168.31.56:5666)

echo "🐄 RAG Pro Max → 飞牛NAS端口映射配置"
echo "飞牛地址: http://192.168.31.56:5666/"
echo "=========================================="
echo ""

# 检查RAG Pro Max运行状态
if lsof -i :8501 >/dev/null 2>&1; then
    echo "✅ RAG Pro Max正在运行 (端口8501)"
else
    echo "❌ RAG Pro Max未运行，请先启动:"
    echo "   ./start.sh"
    exit 1
fi

# 获取Mac的内网IP
MAC_IP=$(ifconfig | grep "inet 192.168.31" | head -1 | awk '{print $2}')
echo "📱 Mac内网IP: $MAC_IP"
echo ""

# 测试本地访问
if curl -s --connect-timeout 3 "http://$MAC_IP:8501" >/dev/null; then
    echo "✅ 本地访问正常: http://$MAC_IP:8501"
else
    echo "❌ 本地访问失败，请检查防火墙设置"
fi
echo ""

echo "🎯 飞牛NAS端口转发配置:"
echo "========================="
echo "1. 访问飞牛管理界面: http://192.168.31.56:5666/"
echo "2. 登录管理员账户"
echo "3. 找到以下设置路径之一:"
echo "   - 网络设置 → 端口转发"
echo "   - 高级设置 → 虚拟服务器"
echo "   - 系统设置 → 网络 → 端口映射"
echo ""
echo "4. 添加端口转发规则:"
echo "   ┌─────────────────────────────────┐"
echo "   │ 服务名称: RAG-Pro-Max           │"
echo "   │ 外部端口: 8501                  │"
echo "   │ 内部IP: $MAC_IP        │"
echo "   │ 内部端口: 8501                  │"
echo "   │ 协议: TCP                       │"
echo "   │ 启用: ✅                        │"
echo "   └─────────────────────────────────┘"
echo ""
echo "5. 保存设置并重启网络服务"
echo ""

echo "🌐 配置完成后的访问地址:"
echo "========================"
echo "内网访问: http://192.168.31.56:8501"
echo "外网访问: http://飞牛外网IP:8501"
echo ""

echo "🔧 测试步骤:"
echo "============"
echo "1. 配置完成后，先测试内网访问:"
echo "   curl http://192.168.31.56:8501"
echo ""
echo "2. 如果内网正常，再测试外网访问"
echo ""

echo "💡 常见问题解决:"
echo "================"
echo "- 如果8501端口被占用，可改用8502、8503等"
echo "- 确保飞牛防火墙开放对应端口"
echo "- 确保Mac防火墙允许8501端口入站连接"
echo "- 如果找不到端口转发设置，查看飞牛型号说明书"

echo ""
echo "🚀 快速测试命令:"
echo "curl http://192.168.31.56:8501"
