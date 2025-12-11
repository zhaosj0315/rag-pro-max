#!/bin/bash
echo "🔄 强制重启应用以应用OCR优化..."

# 查找并停止Streamlit进程
echo "🛑 停止当前Streamlit进程..."
pkill -f "streamlit run"
pkill -f "apppro.py"

# 等待进程完全停止
sleep 2

# 设置OCR优化环境变量
export FORCE_OCR=true
export SKIP_OCR=false
export OCR_AGGRESSIVE=true

echo "🚀 启动优化后的应用..."

# 重新启动应用
cd /Users/zhaosj/Documents/rag-pro-max
streamlit run src/apppro.py --server.headless=true &

echo "✅ 应用已重启，OCR优化已生效"
echo "📊 现在上传PDF文档，应该能看到CPU使用率提升到70%+"
