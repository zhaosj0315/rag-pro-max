#!/bin/bash
# RAG Pro Max - 飞牛NAS端口映射配置助手

echo "🐄 RAG Pro Max - 飞牛NAS端口映射配置助手"
echo "=========================================="
echo ""

# 获取Mac IP地址
MAC_IPS=($(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'))
echo "📱 检测到的Mac IP地址:"
for i in "${!MAC_IPS[@]}"; do
    echo "  [$((i+1))] ${MAC_IPS[i]}"
done
echo ""

# 检查RAG Pro Max运行状态
if lsof -i :8501 >/dev/null 2>&1; then
    echo "✅ RAG Pro Max正在运行 (端口8501)"
    RAG_PID=$(lsof -ti :8501)
    echo "   进程ID: $RAG_PID"
else
    echo "❌ RAG Pro Max未运行，请先启动:"
    echo "   ./start.sh"
    exit 1
fi
echo ""

# 网络连通性测试
echo "🌐 网络连通性测试:"
for ip in "${MAC_IPS[@]}"; do
    if curl -s --connect-timeout 3 "http://$ip:8501" >/dev/null; then
        echo "✅ $ip:8501 - 可访问"
        WORKING_IP="$ip"
    else
        echo "❌ $ip:8501 - 不可访问"
    fi
done
echo ""

if [ -n "$WORKING_IP" ]; then
    echo "🎯 推荐配置:"
    echo "============"
    echo "飞牛NAS端口转发设置:"
    echo "  服务名称: RAG-Pro-Max"
    echo "  外部端口: 8501 (或8502)"
    echo "  内部IP: $WORKING_IP"
    echo "  内部端口: 8501"
    echo "  协议: TCP"
    echo ""
    echo "配置完成后访问地址:"
    echo "  内网: http://飞牛IP:8501"
    echo "  外网: http://飞牛外网IP:8501"
    echo ""
    echo "🔧 配置步骤:"
    echo "1. 登录飞牛管理界面"
    echo "2. 进入 网络设置 → 端口转发"
    echo "3. 添加上述转发规则"
    echo "4. 保存并重启网络服务"
    echo "5. 测试访问"
else
    echo "❌ 未找到可用的IP地址，请检查网络配置"
fi

echo ""
echo "💡 提示:"
echo "- 确保飞牛和Mac在同一内网"
echo "- 确保飞牛防火墙开放对应端口"
echo "- 如果8501端口冲突，可使用8502等其他端口"
