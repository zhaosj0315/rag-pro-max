#!/bin/bash

echo "🛑 停止 RAG Pro Max v2.0..."

# 停止Streamlit
pkill -f "streamlit run"

# 停止API服务
pkill -f "uvicorn.*extended_api"

echo "✅ 服务已停止"
