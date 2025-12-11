#!/bin/bash

# RAG Pro Max 快速启动脚本
# 跳过扫描版PDF的OCR处理，大幅提升处理速度

echo "🚀 RAG Pro Max 快速启动模式"
echo "⚡ 跳过扫描版PDF OCR处理，提升处理速度"
echo "============================================================"

# 设置环境变量跳过OCR
export SKIP_OCR=true

# 启动应用
echo "🌐 启动 Streamlit 应用..."
streamlit run src/apppro.py --server.headless=true &

# 启动API服务
echo "🔌 启动 API 服务..."
cd src/api && python fastapi_server.py &

echo ""
echo "🎉 RAG Pro Max 快速模式启动完成！"
echo ""
echo "📱 访问地址:"
echo "   主应用: http://localhost:8501"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "⚡ 快速模式特性:"
echo "   • 跳过扫描版PDF OCR处理"
echo "   • 大幅提升文档处理速度"
echo "   • 适合快速测试和演示"
echo ""
echo "💡 如需完整OCR功能，请使用: ./start.sh"
echo "🛑 停止服务: Ctrl+C"
echo ""

# 等待用户中断
wait
