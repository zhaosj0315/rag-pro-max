#!/bin/bash

# CPU保护功能快速部署脚本
# 一键应用所有CPU保护措施

echo "🛡️  RAG Pro Max CPU保护部署"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到，请先安装Python"
    exit 1
fi

# 安装必要依赖
echo "📦 检查并安装依赖..."
python3 -c "import psutil" 2>/dev/null || {
    echo "   安装 psutil..."
    pip3 install psutil
}

# 检查文件是否存在
echo "🔍 检查CPU保护文件..."
files=(
    "src/utils/cpu_throttle.py"
    "config/cpu_protection.json"
    "start_safe.sh"
    "cpu_protection_hotfix.py"
    "test_cpu_throttle.py"
)

missing_files=()
for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ 缺少以下文件:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo "请确保所有CPU保护文件都已创建"
    exit 1
fi

echo "✅ 所有文件检查通过"

# 设置执行权限
echo "🔧 设置执行权限..."
chmod +x start_safe.sh
chmod +x test_cpu_throttle.py
chmod +x cpu_protection_hotfix.py

# 备份原始启动脚本
if [ -f "start.sh" ] && [ ! -f "start.sh.backup" ]; then
    echo "💾 备份原始启动脚本..."
    cp start.sh start.sh.backup
fi

# 测试CPU保护功能
echo "🧪 测试CPU保护功能..."
if python3 -c "
import sys
sys.path.insert(0, '.')
from src.utils.cpu_throttle import CPUThrottle
throttle = CPUThrottle(max_cpu_percent=90.0)
print('✅ CPU保护模块加载成功')
throttle.start_monitoring()
import time
time.sleep(1)
throttle.stop_monitoring()
print('✅ CPU监控功能正常')
"; then
    echo "✅ CPU保护功能测试通过"
else
    echo "❌ CPU保护功能测试失败"
    exit 1
fi

# 检查当前系统状态
echo "📊 检查当前系统状态..."
python3 -c "
import psutil
cpu = psutil.cpu_percent(interval=1)
mem = psutil.virtual_memory().percent
print(f'   CPU: {cpu:.1f}%')
print(f'   内存: {mem:.1f}%')
if cpu > 80:
    print('⚠️  警告: CPU使用率较高，建议先关闭其他程序')
if mem > 80:
    print('⚠️  警告: 内存使用率较高')
"

# 创建快捷启动别名
echo "🔗 创建快捷启动方式..."
cat > rag_safe << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./start_safe.sh "$@"
EOF
chmod +x rag_safe

# 部署完成
echo "=================================="
echo "✅ CPU保护部署完成！"
echo ""
echo "🚀 启动方式:"
echo "   方式1: ./start_safe.sh"
echo "   方式2: ./rag_safe"
echo "   方式3: bash start_safe.sh"
echo ""
echo "🧪 测试方式:"
echo "   python3 test_cpu_throttle.py"
echo ""
echo "🚨 紧急修复:"
echo "   python3 cpu_protection_hotfix.py"
echo ""
echo "📖 详细文档:"
echo "   docs/CPU_PROTECTION.md"
echo ""
echo "⚙️ 配置文件:"
echo "   config/cpu_protection.json"
echo "=================================="

# 询问是否立即启动
read -p "🚀 是否立即启动应用? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 启动 RAG Pro Max (带CPU保护)..."
    ./start_safe.sh
else
    echo "👋 部署完成，稍后可使用 ./start_safe.sh 启动"
fi
