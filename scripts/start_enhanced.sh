#!/bin/bash
# RAG Pro Max 增强启动脚本 (Omni-Service Edition) - v2.4.7
# 修正了启动阻塞问题，确保公网地址正常显示

echo "🚀 RAG Pro Max 旗舰版启动中..."

# 切换到项目目录
cd /Users/zhaosj/Documents/rag-pro-max

# 1. 强制清理端口
echo "🧹 清理已有进程与端口 (8501, 8502, 8899)..."
{ lsof -ti:8501,8502,8899 | xargs kill -9 2>/dev/null || true; }
pkill -f "ssh.*serveo.net" 2>/dev/null || true
sleep 2

# 2. 检测网络配置
echo "🔍 检测网络配置..."
LOCAL_IPS=()
while IFS= read -r ip; do
    if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && [[ $ip != "127.0.0.1" ]]; then
        LOCAL_IPS+=("$ip")
    fi
done < <(ifconfig | grep -oE 'inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}')

# 3. 设置环境变量
export PYTHONPATH="${PWD}:${PYTHONPATH}"
export DISABLE_MODEL_SOURCE_CHECK=True
export TOKENIZERS_PARALLELISM=false

# 4. 运行出厂测试 (保持严谨)
echo "🔍 启动前核心自检..."
python3 tests/factory_test.py
if [ $? -ne 0 ]; then
    echo "❌ 出厂测试失败！请检查系统环境。"
    exit 1
fi

# 5. 启动服务 (不使用 start.sh 避免阻塞)
# 创建日志目录
mkdir -p app_logs
RUN_LOG="app_logs/runtime_$(date +%Y%m%d).log"
echo "🌐 启动 Streamlit 应用 (端口 8501)..."
echo "📝 运行时日志记录于: $RUN_LOG"
# 使用 unbuffer 或 python -u 确保日志实时刷新，同时输出到文件
nohup streamlit run src/apppro.py --server.port 8501 > "$RUN_LOG" 2>&1 &
APP_PID=$!

echo "🔌 启动 API 服务 (端口 8502)..."
python3 src/api/fastapi_server.py > /dev/null 2>&1 &
API_PID=$!

# 6. 建立公网隧道 (Serveo)
echo "🌍 建立远程公网隧道 (Auto-healing)..."
(
    while true;
    do
        ssh -o StrictHostKeyChecking=no \
            -o ExitOnForwardFailure=yes \
            -o ConnectTimeout=10 \
            -o ServerAliveInterval=30 \
            -o ServerAliveCountMax=3 \
            -R rag-pro-max:80:localhost:8501 serveo.net
        sleep 5
    done
) > /dev/null 2>&1 &
SSH_PID=$!

# 7. 倒计时等待就绪
echo -n "⏳ 等待全量服务就绪"
for i in {1..8}; do
    echo -n "."
    sleep 1
done
echo ""

# 8. 状态检查与输出
if lsof -i:8501 >/dev/null 2>&1; then
    echo "🎉 RAG Pro Max 启动完成！"
    echo ""
    echo "📱 访问矩阵:"
    echo "   🏠 本地访问: http://localhost:8501"
    echo "   🌐 公网隧道: https://rag-pro-max.serveousercontent.com"
    echo "   🔌 API 文档: http://localhost:8502/docs"

    if [ ${#LOCAL_IPS[@]} -gt 0 ]; then
        echo "   📡 局域网访问:"
        for ip in "${LOCAL_IPS[@]}"; do
            echo "     - http://$ip:8501"
        done
    fi
else
    echo "❌ 服务启动异常，请检查日志: $RUN_LOG"
    kill $APP_PID $API_PID $SSH_PID 2>/dev/null
    exit 1
fi

echo ""
echo "💡 提示: 公网隧道支持断线重连。停止服务请按 Ctrl+C。"
echo "⬇️  以下是实时应用日志:"
echo "--------------------------------------------------"

# 统一停止逻辑
trap "echo -e '\n🛑 正在执行物理停机流程...'; kill $APP_PID $API_PID $SSH_PID 2>/dev/null; { lsof -ti:8501,8502,8899 | xargs kill -9 2>/dev/null || true; }; pkill -f 'ssh.*serveo.net' 2>/dev/null || true; echo '✅ 所有服务已安全退出'; exit 0" INT

# 实时显示日志
tail -f "$RUN_LOG" &
TAIL_PID=$!

# 等待主应用结束
wait $APP_PID
# 清理 tail 进程
kill $TAIL_PID 2>/dev/null