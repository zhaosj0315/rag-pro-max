#!/bin/bash
# RAG Pro Max 快速离线打包方案
# 不构建新镜像，而是打包现有环境

set -e

echo "📦 RAG Pro Max 快速离线打包"
echo "=================================================="

# 检查当前环境
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ 当前环境缺少依赖，请先运行: pip install -r requirements.txt"
    exit 1
fi

# 创建离线包目录
PACKAGE_DIR="rag-pro-max-offline-package"
echo "📁 创建离线包: ${PACKAGE_DIR}"
rm -rf "${PACKAGE_DIR}"
mkdir -p "${PACKAGE_DIR}"

# 1. 复制应用代码
echo "📋 复制应用代码..."
cp -r src/ "${PACKAGE_DIR}/"
cp -r config/ "${PACKAGE_DIR}/" 2>/dev/null || true
cp -r docs/ "${PACKAGE_DIR}/" 2>/dev/null || true
cp requirements.txt "${PACKAGE_DIR}/"
cp README.md "${PACKAGE_DIR}/"

# 2. 下载Python依赖包
echo "📦 下载Python依赖包..."
mkdir -p "${PACKAGE_DIR}/offline_packages"
pip download -r requirements.txt -d "${PACKAGE_DIR}/offline_packages"

# 3. 下载HuggingFace模型
echo "🤖 下载HuggingFace模型..."
python3 -c "
import os
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

# 下载到离线包目录
cache_dir = '${PACKAGE_DIR}/hf_models'
os.makedirs(cache_dir, exist_ok=True)

print('下载嵌入模型...')
model = SentenceTransformer('BAAI/bge-small-zh-v1.5', cache_folder=cache_dir)
tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-zh-v1.5', cache_dir=cache_dir)
model_hf = AutoModel.from_pretrained('BAAI/bge-small-zh-v1.5', cache_dir=cache_dir)
print('✅ 模型下载完成')
"

# 4. 下载Ollama二进制文件
echo "🔧 下载Ollama..."
mkdir -p "${PACKAGE_DIR}/ollama"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    curl -L https://ollama.com/download/ollama-darwin -o "${PACKAGE_DIR}/ollama/ollama"
else
    # Linux
    curl -L https://ollama.com/download/ollama-linux-amd64 -o "${PACKAGE_DIR}/ollama/ollama"
fi
chmod +x "${PACKAGE_DIR}/ollama/ollama"

# 5. 创建离线安装脚本
cat > "${PACKAGE_DIR}/install_offline.sh" << 'EOF'
#!/bin/bash
# RAG Pro Max 离线安装脚本

set -e
echo "🚀 RAG Pro Max 离线安装"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装Python 3.8+"
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install --no-index --find-links ./offline_packages -r requirements.txt

# 安装Ollama
echo "🔧 安装Ollama..."
sudo cp ollama/ollama /usr/local/bin/
sudo chmod +x /usr/local/bin/ollama

# 设置环境变量
export HF_HOME=$(pwd)/hf_models
export TRANSFORMERS_CACHE=$(pwd)/hf_models

# 创建启动脚本
cat > start.sh << 'STARTEOF'
#!/bin/bash
export HF_HOME=$(pwd)/hf_models
export TRANSFORMERS_CACHE=$(pwd)/hf_models
export HF_HUB_OFFLINE=1

# 启动Ollama (后台)
ollama serve &
sleep 5

# 下载模型 (如果需要)
ollama pull qwen2.5:7b 2>/dev/null || echo "模型已存在或网络不可用"

# 启动应用
python3 -m streamlit run src/apppro.py --server.address=0.0.0.0 --server.port=8501
STARTEOF

chmod +x start.sh

echo "✅ 安装完成!"
echo "🚀 运行: ./start.sh"
EOF

chmod +x "${PACKAGE_DIR}/install_offline.sh"

# 6. 创建README
cat > "${PACKAGE_DIR}/README_OFFLINE.md" << 'EOF'
# RAG Pro Max 离线版

## 安装步骤

1. 解压离线包
2. 运行安装脚本: `sudo bash install_offline.sh`
3. 启动应用: `./start.sh`
4. 访问: http://localhost:8501

## 系统要求

- Python 3.8+
- 8GB+ 内存
- 20GB+ 磁盘空间

## 注意事项

- 首次启动需要下载Ollama模型 (需要网络)
- 如果完全离线，请提前下载qwen2.5:7b模型
EOF

# 7. 打包
echo "📦 创建压缩包..."
tar -czf "${PACKAGE_DIR}.tar.gz" "${PACKAGE_DIR}"

# 显示结果
PACKAGE_SIZE=$(ls -lh "${PACKAGE_DIR}.tar.gz" | awk '{print $5}')
echo ""
echo "✅ 离线包创建完成!"
echo "📁 文件: ${PACKAGE_DIR}.tar.gz"
echo "📊 大小: ${PACKAGE_SIZE}"
echo ""
echo "🚀 使用方法:"
echo "1. 传输到Linux服务器: scp ${PACKAGE_DIR}.tar.gz user@server:/tmp/"
echo "2. 解压: tar -xzf ${PACKAGE_DIR}.tar.gz"
echo "3. 安装: cd ${PACKAGE_DIR} && sudo bash install_offline.sh"
echo "4. 启动: ./start.sh"
