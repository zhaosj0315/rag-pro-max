#!/bin/bash
# RAG Pro Max Linux 部署脚本

set -e

echo "============================================================"
echo "  RAG Pro Max Linux 部署"
echo "============================================================"

# 检查 Python 版本
echo ""
echo "1. 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    echo "请运行: sudo apt-get install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 检查 pip
echo ""
echo "2. 检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装"
    echo "请运行: sudo apt-get install python3-pip"
    exit 1
fi
echo "✅ pip3 已安装"

# 创建虚拟环境（可选）
echo ""
echo "3. 创建虚拟环境（可选）..."
read -p "是否创建虚拟环境？(y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
else
    echo "⏭️  跳过虚拟环境"
fi

# 安装依赖
echo ""
echo "4. 安装依赖..."
pip3 install -r requirements.txt
echo "✅ 依赖安装完成"

# 创建必要目录
echo ""
echo "5. 创建必要目录..."
mkdir -p vector_db_storage chat_histories temp_uploads hf_cache app_logs suggestion_history
echo "✅ 目录创建完成"

# 检查端口
echo ""
echo "6. 检查端口 8501..."
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 8501 已被占用"
    echo "可以使用其他端口: streamlit run src/apppro.py --server.port 8502"
else
    echo "✅ 端口 8501 可用"
fi

# 运行测试
echo ""
echo "7. 运行出厂测试..."
read -p "是否运行测试？(y/n): " run_test
if [ "$run_test" = "y" ]; then
    python3 tests/factory_test.py
else
    echo "⏭️  跳过测试"
fi

# 完成
echo ""
echo "============================================================"
echo "  部署完成！"
echo "============================================================"
echo ""
echo "启动应用:"
echo "  streamlit run src/apppro.py"
echo ""
echo "或使用自动测试启动:"
echo "  ./start.sh"
echo ""
