#!/bin/bash

# RAG Pro Max v2.0 部署脚本
# 支持增量更新、API扩展、多模态处理

set -e

echo "🚀 RAG Pro Max v2.0 部署开始..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要 >= 3.8，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 安装系统依赖（OCR支持）
echo "📦 安装系统依赖..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew >/dev/null 2>&1; then
        echo "安装 Tesseract OCR..."
        brew install tesseract tesseract-lang
    else
        echo "⚠️  未检测到 Homebrew，请手动安装 Tesseract OCR"
        echo "   brew install tesseract tesseract-lang"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get >/dev/null 2>&1; then
        # Ubuntu/Debian
        echo "安装 Tesseract OCR (Ubuntu/Debian)..."
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
        sudo apt-get install -y python3-tk  # Tkinter支持
    elif command -v yum >/dev/null 2>&1; then
        # CentOS/RHEL
        echo "安装 Tesseract OCR (CentOS/RHEL)..."
        sudo yum install -y epel-release
        sudo yum install -y tesseract tesseract-langpack-chi_sim tesseract-langpack-eng
        sudo yum install -y python3-tkinter
    else
        echo "⚠️  未识别的Linux发行版，请手动安装 Tesseract OCR"
    fi
fi

# 安装Java（表格提取需要）
echo "☕ 检查Java环境..."
if ! command -v java >/dev/null 2>&1; then
    echo "⚠️  未检测到Java，表格提取功能可能不可用"
    echo "   请安装Java 8+: https://adoptopenjdk.net/"
else
    java_version=$(java -version 2>&1 | head -n1 | cut -d'"' -f2)
    echo "✅ Java版本: $java_version"
fi

# 创建虚拟环境（可选）
if [ "$1" = "--venv" ]; then
    echo "🐍 创建虚拟环境..."
    python3 -m venv venv_v2
    source venv_v2/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install --upgrade pip

# 先安装基础依赖
pip install -r requirements.txt

# 安装v2.0新增依赖
if [ -f "requirements_v2.txt" ]; then
    echo "📦 安装v2.0新增依赖..."
    pip install -r requirements_v2.txt
else
    echo "📦 安装v2.0核心依赖..."
    pip install fastapi uvicorn[standard] python-multipart
    pip install Pillow pytesseract tabula-py
    pip install watchdog filelock xlrd xlwt lxml
fi

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p vector_db_storage
mkdir -p chat_histories
mkdir -p temp_uploads
mkdir -p hf_cache
mkdir -p app_logs
mkdir -p suggestion_history
mkdir -p multimodal_cache  # v2.0新增

# 运行测试
echo "🧪 运行v2.0功能测试..."
if [ -f "tests/test_v2_features.py" ]; then
    python3 tests/test_v2_features.py
    if [ $? -eq 0 ]; then
        echo "✅ v2.0功能测试通过"
    else
        echo "⚠️  v2.0功能测试有警告，但可以继续"
    fi
else
    echo "⚠️  未找到v2.0测试文件，跳过测试"
fi

# 运行基础测试
echo "🧪 运行基础功能测试..."
if [ -f "tests/factory_test.py" ]; then
    python3 tests/factory_test.py
    if [ $? -ne 0 ]; then
        echo "❌ 基础功能测试失败，请检查环境"
        exit 1
    fi
else
    echo "⚠️  未找到基础测试文件"
fi

# 检查配置文件
echo "⚙️  检查配置文件..."
config_files=("config/app_config.json" "config/rag_config.json")
for config_file in "${config_files[@]}"; do
    if [ ! -f "$config_file" ]; then
        echo "⚠️  配置文件不存在: $config_file"
        echo "   将使用默认配置"
    fi
done

# 创建启动脚本
echo "📝 创建v2.0启动脚本..."
cat > start_v2.sh << 'EOF'
#!/bin/bash

echo "🚀 启动 RAG Pro Max v2.0..."

# 检查虚拟环境
if [ -d "venv_v2" ]; then
    echo "🐍 激活虚拟环境..."
    source venv_v2/bin/activate
fi

# 启动主应用
echo "🌐 启动Streamlit应用 (端口 8501)..."
streamlit run src/apppro.py --server.port 8501 &
STREAMLIT_PID=$!

# 启动扩展API
echo "🔌 启动扩展API服务 (端口 8502)..."
python3 -m uvicorn src.api.extended_api:extended_app --host 0.0.0.0 --port 8502 &
API_PID=$!

echo "✅ RAG Pro Max v2.0 启动完成！"
echo ""
echo "📱 访问地址:"
echo "   主应用: http://localhost:8501"
echo "   API文档: http://localhost:8502/docs"
echo ""
echo "🛑 停止服务: Ctrl+C 或运行 ./stop_v2.sh"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $STREAMLIT_PID $API_PID 2>/dev/null; exit 0" INT
wait
EOF

chmod +x start_v2.sh

# 创建停止脚本
cat > stop_v2.sh << 'EOF'
#!/bin/bash

echo "🛑 停止 RAG Pro Max v2.0..."

# 停止Streamlit
pkill -f "streamlit run"

# 停止API服务
pkill -f "uvicorn.*extended_api"

echo "✅ 服务已停止"
EOF

chmod +x stop_v2.sh

# 完成部署
echo ""
echo "🎉 RAG Pro Max v2.0 部署完成！"
echo ""
echo "📋 新功能概览:"
echo "   ✨ 增量更新 - 智能检测文件变化，无需重建知识库"
echo "   🔌 API扩展 - RESTful API接口，支持程序化调用"
echo "   🎨 多模态支持 - 图片OCR、表格提取"
echo ""
echo "🚀 启动方式:"
echo "   ./start_v2.sh     # 启动完整v2.0服务"
echo "   ./start.sh        # 启动基础版本"
echo ""
echo "📚 文档:"
echo "   API文档: http://localhost:8502/docs (启动后访问)"
echo "   README: 查看项目根目录 README.md"
echo ""
echo "🔧 故障排除:"
echo "   - OCR不工作: 检查 tesseract 安装"
echo "   - 表格提取失败: 检查 Java 环境"
echo "   - API无法访问: 检查端口 8502 是否被占用"
