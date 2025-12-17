#!/bin/bash

echo "📦 RAG Pro Max 优化完全离线包构建"
echo "=================================="

# 清理旧包
rm -rf rag-pro-max-optimized-offline
rm -f rag-pro-max-optimized-offline.tar.gz

# 创建目录
mkdir -p rag-pro-max-optimized-offline/{offline_packages,hf_models,ollama_models,ollama_bin}

echo "📋 复制应用代码..."
cp -r src/ rag-pro-max-optimized-offline/
cp requirements.txt rag-pro-max-optimized-offline/
cp -r config/ rag-pro-max-optimized-offline/ 2>/dev/null || true

echo "📦 下载Python依赖..."
pip download -r requirements.txt -d rag-pro-max-optimized-offline/offline_packages/ --platform linux_x86_64 --only-binary=:all: --python-version 3.10

echo "🤖 下载Ollama二进制..."
curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64 -o rag-pro-max-optimized-offline/ollama_bin/ollama
chmod +x rag-pro-max-optimized-offline/ollama_bin/ollama

echo "🧠 复制HuggingFace模型..."
python3 -c "
from sentence_transformers import SentenceTransformer
import shutil
import os
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
target_dir = 'rag-pro-max-optimized-offline/hf_models'
if os.path.exists(cache_dir):
    shutil.copytree(cache_dir, target_dir, dirs_exist_ok=True)
print('✅ HF模型复制完成')
"

echo "🎯 准备干净的Ollama环境..."
# 创建临时目录用于干净的模型下载
TEMP_OLLAMA_DIR="/tmp/ollama_clean_$(date +%s)"
mkdir -p "$TEMP_OLLAMA_DIR"

echo "📥 在干净环境中下载gemma2:2b..."
# 使用临时目录下载模型
export OLLAMA_MODELS="$TEMP_OLLAMA_DIR"

# 启动临时Ollama服务
ollama serve &
OLLAMA_PID=$!
sleep 10

# 下载指定模型
ollama pull gemma2:2b

# 停止服务
kill $OLLAMA_PID 2>/dev/null || true
sleep 5

echo "📋 复制干净的模型文件..."
cp -r "$TEMP_OLLAMA_DIR"/* rag-pro-max-optimized-offline/ollama_models/

echo "🧹 清理临时文件..."
rm -rf "$TEMP_OLLAMA_DIR"

echo "📝 创建安装脚本..."
cat > rag-pro-max-optimized-offline/install_optimized.sh << 'EOF'
#!/bin/bash
echo "🚀 RAG Pro Max 优化离线安装"

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install --no-index --find-links offline_packages/ -r requirements.txt

# 安装Ollama
echo "🤖 安装Ollama..."
sudo cp ollama_bin/ollama /usr/local/bin/
sudo chmod +x /usr/local/bin/ollama

# 复制HF模型
echo "🧠 复制HuggingFace模型..."
mkdir -p ~/.cache/huggingface/
cp -r hf_models/* ~/.cache/huggingface/ 2>/dev/null || true

# 复制Ollama模型
echo "🎯 复制Ollama模型..."
mkdir -p ~/.ollama/
cp -r ollama_models ~/.ollama/models 2>/dev/null || true

echo "✅ 优化安装完成！"
echo "🚀 启动: streamlit run src/apppro.py"
EOF

chmod +x rag-pro-max-optimized-offline/install_optimized.sh

echo "🗜️ 打包..."
tar -czf rag-pro-max-optimized-offline.tar.gz rag-pro-max-optimized-offline/

echo "✅ 优化离线包构建完成"
echo "📦 文件: rag-pro-max-optimized-offline.tar.gz"
ls -lh rag-pro-max-optimized-offline.tar.gz

# 显示各部分大小
echo ""
echo "📊 各部分大小:"
du -sh rag-pro-max-optimized-offline/*/

echo ""
echo "🎯 优化版本特点:"
echo "  - 只包含gemma2:2b模型 (~1.6GB)"
echo "  - 所有Python依赖完整"
echo "  - HuggingFace模型完整"
echo "  - 预计总大小: ~3-5GB"
