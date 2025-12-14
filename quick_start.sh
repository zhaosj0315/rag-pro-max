#!/bin/bash
# RAG Pro Max 快速启动脚本 (跳过测试)

echo "⚡ RAG Pro Max 快速启动..."

# 智能端口检测
find_port() {
    for port in {8501..8510}; do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
    done
    echo 8501  # 默认端口
}

PORT=$(find_port)
echo "🌐 启动端口: $PORT"
echo "📱 访问: http://localhost:$PORT"

streamlit run src/apppro.py --server.port $PORT
