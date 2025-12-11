#!/bin/bash
# 清理启动脚本 - 减少警告信息

# 设置环境变量
export DISABLE_MODEL_SOURCE_CHECK=True
export TOKENIZERS_PARALLELISM=false
export PYTHONWARNINGS="ignore::UserWarning:jieba,ignore::UserWarning:pydantic"

echo "🚀 启动 RAG Pro Max v2.2.1..."
echo "🔧 环境优化: 已禁用模型检查和并行警告"

# 启动应用
streamlit run src/apppro.py --server.headless=true
