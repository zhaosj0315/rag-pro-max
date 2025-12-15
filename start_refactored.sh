#!/bin/bash

# RAG Pro Max 重构版启动脚本

echo "🚀 启动 RAG Pro Max (重构版)..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装"
    exit 1
fi

# 检查依赖
if ! python -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit 未安装，请运行: pip install -r requirements.txt"
    exit 1
fi

# 启动应用
echo "✅ 启动重构版应用..."
streamlit run src/apppro_refactored.py

echo "🎉 应用已启动！"
