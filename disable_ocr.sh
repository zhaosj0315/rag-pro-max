#!/bin/bash
# 禁用自动OCR处理
export SKIP_OCR=true
echo "✅ 已设置 SKIP_OCR=true，将跳过扫描版PDF的OCR处理"
echo "启动应用..."
streamlit run src/apppro.py
