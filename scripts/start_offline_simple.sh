#!/bin/bash
set -e

echo "🚀 启动RAG Pro Max离线版..."

# 启动Ollama服务
echo "📦 启动Ollama服务..."
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
OLLAMA_PID=$!

# 等待Ollama启动
sleep 15

# 验证模型
echo "🔍 验证模型..."
ollama list

# 启动RAG Pro Max
echo "🌟 启动RAG Pro Max应用..."
python3 -m streamlit run src/apppro.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false &

APP_PID=$!

echo "🎉 服务启动完成!"
echo "📱 访问地址: http://localhost:8501"

# 保持运行
wait $APP_PID

# 清理
kill $OLLAMA_PID 2>/dev/null || true
