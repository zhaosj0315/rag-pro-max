#!/bin/bash

echo "🚀 启动 RAG Pro Max v2.3.0 - 智能监控版"
echo "=========================================="

# 检查依赖
echo "📦 检查v2.3.0依赖..."
python -c "import plotly, pandas, plyer; print('✅ 依赖检查通过')" || {
    echo "❌ 缺少依赖，正在安装..."
    pip install plotly pandas plyer
}

# 运行测试
echo "🧪 运行v2.3.0功能测试..."
python test_v2.3.0_features.py || {
    echo "❌ 功能测试失败"
    exit 1
}

echo "✅ v2.3.0功能测试通过"
echo ""
echo "🎯 新功能位置:"
echo "  📊 监控面板: 侧边栏 → 📊 监控 标签页"
echo "  🤖 智能调度: 侧边栏顶部实时状态显示"
echo "  🚨 告警系统: 自动运行，异常时桌面通知"
echo "  📈 进度追踪: 文件处理时自动显示"
echo ""

# 启动应用
echo "🚀 启动应用..."
streamlit run src/apppro.py
