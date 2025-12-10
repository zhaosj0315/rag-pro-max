#!/bin/bash

echo "🚀 启动 RAG Pro Max v2.0..."

# 检查虚拟环境
if [ -d "venv_v2" ]; then
    echo "🐍 激活虚拟环境..."
    source venv_v2/bin/activate
fi

# 启动主应用
echo "🌐 启动Streamlit应用 (端口 8501)..."
streamlit run src/apppro.py --server.port 8501 &
STREAMLIT_PID=$!

# 启动扩展API
echo "🔌 启动扩展API服务 (端口 8502)..."
python3 -m uvicorn src.api.extended_api:extended_app --host 0.0.0.0 --port 8502 &
API_PID=$!

echo "✅ RAG Pro Max v2.0 启动完成！"
echo ""
echo "📱 访问地址:"
echo "   主应用: http://localhost:8501"
echo "   API文档: http://localhost:8502/docs"
echo ""
echo "🛑 停止服务: Ctrl+C 或运行 ./stop_v2.sh"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $STREAMLIT_PID $API_PID 2>/dev/null; exit 0" INT
wait
