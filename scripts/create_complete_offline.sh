#!/bin/bash

echo "📦 RAG Pro Max 完全离线包构建 (包含所有模型)"
echo "===================================================="

# 清理旧包
rm -rf rag-pro-max-complete-offline
rm -f rag-pro-max-complete-offline.tar.gz

# 创建目录
mkdir -p rag-pro-max-complete-offline/{offline_packages,hf_models,ollama_models,ollama_bin}

echo "📋 复制应用代码..."
cp -r src/ rag-pro-max-complete-offline/
cp requirements.txt rag-pro-max-complete-offline/
cp -r config/ rag-pro-max-complete-offline/ 2>/dev/null || true

echo "📦 下载AMD64 Python依赖..."
pip download -r requirements.txt -d rag-pro-max-complete-offline/offline_packages/ --platform linux_x86_64 --only-binary=:all: --python-version 3.10

echo "🤖 下载AMD64 Ollama二进制..."
curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64 -o rag-pro-max-complete-offline/ollama_bin/ollama
chmod +x rag-pro-max-complete-offline/ollama_bin/ollama

echo "🧠 下载HuggingFace模型..."
python3 -c "
from sentence_transformers import SentenceTransformer
import shutil
import os
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
target_dir = 'rag-pro-max-complete-offline/hf_models'
if os.path.exists(cache_dir):
    shutil.copytree(cache_dir, target_dir, dirs_exist_ok=True)
print('✅ HF模型复制完成')
"

echo "🎯 下载Ollama模型 (gemma2:2b - 约1.6GB)..."
# 启动临时Ollama服务下载模型
export OLLAMA_MODELS="$(pwd)/rag-pro-max-complete-offline/ollama_models"
mkdir -p "$OLLAMA_MODELS"

# 使用本地Ollama下载模型
ollama serve &
OLLAMA_PID=$!
sleep 10

echo "📥 下载gemma2:2b模型..."
ollama pull gemma2:2b

# 停止Ollama服务
kill $OLLAMA_PID 2>/dev/null || true

# 复制模型文件
cp -r ~/.ollama/models/* rag-pro-max-complete-offline/ollama_models/ 2>/dev/null || true

echo "📝 创建完全离线安装脚本..."
cat > rag-pro-max-complete-offline/install_complete_offline.sh << 'EOF'
#!/bin/bash
echo "🚀 RAG Pro Max 完全离线安装 (包含所有模型)"

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

# 创建启动脚本
echo "📝 创建启动脚本..."
cat > start_complete_offline.sh << 'STARTEOF'
#!/bin/bash
echo "🚀 启动RAG Pro Max完全离线版..."
echo "✅ 所有模型已预装，无需网络连接"

export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
sleep 5

echo "🎯 验证模型..."
ollama list

echo "🌟 启动应用..."
streamlit run src/apppro.py --server.address=0.0.0.0 --server.port=8501
STARTEOF
chmod +x start_complete_offline.sh

echo "✅ 完全离线安装完成！"
echo "🚀 运行 ./start_complete_offline.sh 启动应用"
echo "🌐 访问: http://localhost:8501"
EOF

chmod +x rag-pro-max-complete-offline/install_complete_offline.sh

echo "📄 创建README..."
cat > rag-pro-max-complete-offline/README_COMPLETE_OFFLINE.md << 'EOF'
# RAG Pro Max 完全离线版

## 特点
- ✅ 完全离线，无需任何网络连接
- ✅ 包含所有Python依赖包
- ✅ 包含HuggingFace嵌入模型
- ✅ 包含Ollama + gemma2:2b大语言模型
- ✅ 一键安装，一键启动

## 安装步骤
1. 解压: `tar -xzf rag-pro-max-complete-offline.tar.gz`
2. 安装: `cd rag-pro-max-complete-offline && sudo bash install_complete_offline.sh`
3. 启动: `./start_complete_offline.sh`
4. 访问: http://localhost:8501

## 系统要求
- Linux AMD64 (x86_64)
- Python 3.8+
- 8GB+ 内存
- 25GB+ 磁盘空间

## 完全离线
此版本包含所有必需组件，部署后无需任何网络连接即可正常使用。
EOF

echo "🗜️ 打包..."
tar -czf rag-pro-max-complete-offline.tar.gz rag-pro-max-complete-offline/

echo "✅ 完全离线包构建完成"
echo "📦 文件: rag-pro-max-complete-offline.tar.gz"
ls -lh rag-pro-max-complete-offline.tar.gz
echo ""
echo "🎯 这是真正的完全离线版本，包含:"
echo "  - 所有Python依赖"
echo "  - HuggingFace模型"
echo "  - Ollama + gemma2:2b模型"
echo "  - 无需任何网络连接"
