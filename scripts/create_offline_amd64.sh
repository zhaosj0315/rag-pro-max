#!/bin/bash

echo "📦 RAG Pro Max AMD64 Linux 离线包构建"
echo "===================================================="

# 清理旧包
rm -rf rag-pro-max-offline-amd64
rm -f rag-pro-max-offline-amd64.tar.gz

# 创建目录
mkdir -p rag-pro-max-offline-amd64/{offline_packages,hf_models,ollama}

echo "📋 复制应用代码..."
cp -r src/ rag-pro-max-offline-amd64/
cp requirements.txt rag-pro-max-offline-amd64/
cp -r config/ rag-pro-max-offline-amd64/ 2>/dev/null || true

echo "📦 下载AMD64 Python依赖..."
pip download -r requirements.txt -d rag-pro-max-offline-amd64/offline_packages/ --platform linux_x86_64 --only-binary=:all: --python-version 3.10

echo "🤖 下载AMD64 Ollama..."
curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64 -o rag-pro-max-offline-amd64/ollama/ollama
chmod +x rag-pro-max-offline-amd64/ollama/ollama

echo "🧠 下载HuggingFace模型..."
python3 -c "
from sentence_transformers import SentenceTransformer
import shutil
import os
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
target_dir = 'rag-pro-max-offline-amd64/hf_models'
if os.path.exists(cache_dir):
    shutil.copytree(cache_dir, target_dir, dirs_exist_ok=True)
print('✅ 模型复制完成')
"

echo "📝 创建AMD64安装脚本..."
cat > rag-pro-max-offline-amd64/install_offline.sh << 'EOF'
#!/bin/bash
echo "🚀 RAG Pro Max AMD64 Linux 离线安装"

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install --no-index --find-links offline_packages/ -r requirements.txt

# 安装Ollama
echo "🤖 安装Ollama..."
sudo cp ollama/ollama /usr/local/bin/
sudo chmod +x /usr/local/bin/ollama

# 复制模型
echo "🧠 复制模型..."
mkdir -p ~/.cache/huggingface/
cp -r hf_models/* ~/.cache/huggingface/ 2>/dev/null || true

# 创建启动脚本
echo "📝 创建启动脚本..."
cat > start.sh << 'STARTEOF'
#!/bin/bash
echo "🚀 启动RAG Pro Max..."
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
sleep 5
ollama pull qwen2.5:7b
streamlit run src/apppro.py --server.address=0.0.0.0 --server.port=8501
STARTEOF
chmod +x start.sh

echo "✅ 安装完成！运行 ./start.sh 启动应用"
EOF

chmod +x rag-pro-max-offline-amd64/install_offline.sh

echo "📄 创建README..."
cat > rag-pro-max-offline-amd64/README_OFFLINE.md << 'EOF'
# RAG Pro Max AMD64 Linux 离线版

## 安装步骤

1. 解压离线包
2. 运行安装脚本: `sudo bash install_offline.sh`
3. 启动应用: `./start.sh`
4. 访问: http://localhost:8501

## 系统要求

- Linux AMD64 (x86_64)
- Python 3.8+
- 8GB+ 内存
- 20GB+ 磁盘空间

## 注意事项

- 首次启动需要下载Ollama模型 (需要网络)
- 如果完全离线，请提前下载qwen2.5:7b模型
EOF

echo "🗜️ 打包..."
tar -czf rag-pro-max-offline-amd64.tar.gz rag-pro-max-offline-amd64/

echo "✅ AMD64离线包构建完成"
ls -lh rag-pro-max-offline-amd64.tar.gz
