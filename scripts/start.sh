#!/bin/bash
# RAG Pro Max 启动脚本 - v2.0 兼容版
# 自动检测并启用v2.0功能，保持向后兼容

echo "🚀 RAG Pro Max 启动中..."
echo ""

# 检查是否有v2.0依赖
V2_AVAILABLE=true

# 检查关键v2.0模块
if ! python3 -c "from src.kb.incremental_updater import IncrementalUpdater" 2>/dev/null; then
    V2_AVAILABLE=false
fi

if ! python3 -c "from src.processors.multimodal_processor import MultimodalProcessor" 2>/dev/null; then
    V2_AVAILABLE=false
fi

# 显示版本信息
if [ "$V2_AVAILABLE" = true ]; then
    echo "✨ 检测到 v2.0 功能模块"
    echo "📋 可用功能: 增量更新、多模态支持、扩展API"
else
    echo "📦 运行 v1.8 基础版本"
    echo "💡 如需v2.0功能，运行: ./scripts/deploy_v2.sh"
fi

echo ""

# 运行出厂测试
echo "🔍 启动前检测..."
python3 tests/factory_test.py

# 检查测试结果
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 出厂测试失败！应用未启动"
    echo "💡 请修复问题后再启动"
    exit 1
fi

echo ""
echo "✅ 测试通过！正在启动应用..."

# 设置环境变量
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# 启动主应用
echo "🌐 启动 Streamlit 应用 (端口 8501)..."
streamlit run src/apppro.py --server.port 8501 &
STREAMLIT_PID=$!

# 如果v2.0可用，启动API服务
if [ "$V2_AVAILABLE" = true ]; then
    echo "🔌 启动 API 服务 (端口 8000)..."
    python3 src/api/fastapi_server.py &
    API_PID=$!
    
    echo ""
    echo "🎉 RAG Pro Max v2.0 启动完成！"
    echo ""
    echo "📱 访问地址:"
    echo "   主应用: http://localhost:8501"
    echo "   API文档: http://localhost:8000/docs"
    echo ""
    echo "🆕 v2.0 新功能:"
    echo "   • 增量更新 - 智能检测文件变化"
    echo "   • 多模态支持 - 图片OCR、表格提取"
    echo "   • 扩展API - 程序化调用接口"
else
    echo ""
    echo "🎉 RAG Pro Max v1.8 启动完成！"
    echo ""
    echo "📱 访问地址: http://localhost:8501"
fi

echo ""
echo "🛑 停止服务: Ctrl+C"

# 等待用户中断
if [ "$V2_AVAILABLE" = true ]; then
    trap "echo '🛑 正在停止服务...'; kill $STREAMLIT_PID $API_PID 2>/dev/null; exit 0" INT
else
    trap "echo '🛑 正在停止服务...'; kill $STREAMLIT_PID 2>/dev/null; exit 0" INT
fi

wait
