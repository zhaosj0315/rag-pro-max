#!/bin/bash

echo "📦 RAG Pro Max 精简离线包构建"
echo "================================"

# 清理旧包
rm -rf rag-pro-max-minimal-offline
rm -f rag-pro-max-minimal-offline.tar.gz

# 创建目录
mkdir -p rag-pro-max-minimal-offline/{offline_packages,hf_models}

echo "📋 复制核心代码..."
cp -r src/ rag-pro-max-minimal-offline/
cp requirements.txt rag-pro-max-minimal-offline/
cp -r config/ rag-pro-max-minimal-offline/ 2>/dev/null || true

echo "📦 下载核心Python依赖..."
# 只下载核心依赖，排除大型包
pip download streamlit requests ollama sentence-transformers chromadb llama-index-core -d rag-pro-max-minimal-offline/offline_packages/ --platform linux_x86_64 --only-binary=:all: --python-version 3.10

echo "🧠 复制HF嵌入模型..."
python3 -c "
from sentence_transformers import SentenceTransformer
import shutil
import os
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
# 只复制嵌入模型，不包含整个缓存
model_path = model._modules['0'].auto_model.config._name_or_path
cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
target_dir = 'rag-pro-max-minimal-offline/hf_models'
# 查找并复制特定模型
for item in os.listdir(cache_dir):
    if 'bge-small-zh' in item:
        shutil.copytree(os.path.join(cache_dir, item), os.path.join(target_dir, item), dirs_exist_ok=True)
print('✅ 嵌入模型复制完成')
"

echo "📝 创建精简安装脚本..."
cat > rag-pro-max-minimal-offline/install_minimal.sh << 'EOF'
#!/bin/bash
echo "🚀 RAG Pro Max 精简离线安装"

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install --no-index --find-links offline_packages/ streamlit requests ollama sentence-transformers chromadb llama-index-core

# 复制HF模型
echo "🧠 复制HuggingFace模型..."
mkdir -p ~/.cache/huggingface/hub/
cp -r hf_models/* ~/.cache/huggingface/hub/ 2>/dev/null || true

echo "✅ 精简安装完成！"
echo "📋 下一步："
echo "1. 安装Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
echo "2. 下载模型: ollama pull gemma2:2b"
echo "3. 启动应用: streamlit run src/apppro.py"
EOF

chmod +x rag-pro-max-minimal-offline/install_minimal.sh

echo "🗜️ 打包..."
tar -czf rag-pro-max-minimal-offline.tar.gz rag-pro-max-minimal-offline/

echo "✅ 精简离线包构建完成"
echo "📦 文件: rag-pro-max-minimal-offline.tar.gz"
ls -lh rag-pro-max-minimal-offline.tar.gz
echo ""
echo "🎯 精简版本包含:"
echo "  - 核心Python依赖 (~500MB)"
echo "  - HuggingFace嵌入模型 (~200MB)"
echo "  - 需要在线下载Ollama和LLM模型"
