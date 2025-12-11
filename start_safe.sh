#!/bin/bash

# RAG Pro Max 安全启动脚本
# 带CPU使用率保护，防止系统过载关机

echo "🛡️  RAG Pro Max 安全启动"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到，请先安装Python"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "import psutil" 2>/dev/null || {
    echo "⚠️  psutil 未安装，正在安装..."
    pip3 install psutil
}

# 检查当前CPU使用率
echo "📊 检查系统状态..."
CPU_USAGE=$(python3 -c "import psutil; print(f'{psutil.cpu_percent(interval=1):.1f}')")
MEM_USAGE=$(python3 -c "import psutil; print(f'{psutil.virtual_memory().percent:.1f}')")

echo "   CPU: ${CPU_USAGE}%"
echo "   内存: ${MEM_USAGE}%"

# 如果CPU使用率已经很高，警告用户
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "⚠️  警告: CPU使用率已经很高 (${CPU_USAGE}%)"
    echo "   建议先关闭其他程序再启动"
    read -p "   是否继续启动? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 启动已取消"
        exit 1
    fi
fi

# 启动CPU保护
echo "🛡️  启动CPU保护..."
python3 -c "
import sys, os
sys.path.insert(0, '.')
from src.utils.cpu_throttle import start_global_cpu_protection
start_global_cpu_protection()
print('✅ CPU保护已启动 (限制: 90%)')
" &

# 等待CPU保护启动
sleep 2

# 运行出厂测试（可选）
if [ "$1" != "--skip-test" ]; then
    echo "🧪 运行快速测试..."
    if python3 tests/factory_test.py --quick; then
        echo "✅ 测试通过"
    else
        echo "⚠️  测试失败，但继续启动"
    fi
fi

# 启动应用
echo "🚀 启动 RAG Pro Max..."
echo "   访问地址: http://localhost:8501"
echo "   按 Ctrl+C 停止应用"
echo "=================================="

# 使用trap捕获退出信号，确保清理CPU保护
trap 'echo "🛑 正在停止..."; python3 -c "from src.utils.cpu_throttle import stop_global_cpu_protection; stop_global_cpu_protection()"; exit 0' INT TERM

# 启动Streamlit应用
python3 -c "
import streamlit.web.cli as stcli
import sys
sys.argv = ['streamlit', 'run', 'src/apppro.py', '--server.headless=true']
stcli.main()
"
