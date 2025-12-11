#!/bin/bash
export DISABLE_MODEL_SOURCE_CHECK=True
export HF_HUB_OFFLINE=1
export OCR_SINGLE_PROCESS=1
export TOKENIZERS_PARALLELISM=false

echo "🚀 启动 RAG Pro Max v2.1.0 (修复版)"
streamlit run src/apppro.py --server.headless=true
