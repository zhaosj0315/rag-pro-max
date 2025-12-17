#!/bin/bash

echo "🐳 RAG Pro Max Docker离线包构建"
echo "================================"

# 清理旧包
rm -rf rag-pro-max-docker-offline
rm -f rag-pro-max-docker-offline.tar.gz

# 创建目录
mkdir -p rag-pro-max-docker-offline/{app,models,wheels}

echo "📋 复制应用代码..."
cp -r src/ rag-pro-max-docker-offline/app/ 2>/dev/null || cp -r . rag-pro-max-docker-offline/app/
cp requirements.txt rag-pro-max-docker-offline/app/
cp -r config/ rag-pro-max-docker-offline/app/ 2>/dev/null || true

echo "📦 下载多架构Python依赖..."
# 下载Linux x86_64和ARM64依赖
pip download -r requirements.txt -d rag-pro-max-docker-offline/wheels/ --platform linux_x86_64 --only-binary=:all: --python-version 3.10
pip download -r requirements.txt -d rag-pro-max-docker-offline/wheels/ --platform linux_aarch64 --only-binary=:all: --python-version 3.10

echo "🧠 复制HuggingFace模型..."
python3 -c "
from sentence_transformers import SentenceTransformer
import shutil
import os
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
target_dir = 'rag-pro-max-docker-offline/models/hf_models'
if os.path.exists(cache_dir):
    shutil.copytree(cache_dir, target_dir, dirs_exist_ok=True)
print('✅ HF模型复制完成')
"

echo "🎯 复制Ollama模型..."
mkdir -p rag-pro-max-docker-offline/models/ollama_models
cp -r ~/.ollama/models/* rag-pro-max-docker-offline/models/ollama_models/ 2>/dev/null || echo "⚠️ Ollama模型复制失败，需要手动处理"

echo "🐳 创建Dockerfile..."
cat > rag-pro-max-docker-offline/Dockerfile << 'EOF'
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制应用代码
COPY app/ /app/

# 复制Python依赖
COPY wheels/ /tmp/wheels/

# 安装Python依赖 (离线)
RUN pip install --no-index --find-links /tmp/wheels/ -r requirements.txt

# 复制模型
COPY models/hf_models/ /root/.cache/huggingface/hub/
COPY models/ollama_models/ /root/.ollama/models/

# 安装Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh || echo "Ollama安装失败，容器内手动处理"

# 暴露端口
EXPOSE 8501 11434

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "🚀 启动RAG Pro Max Docker版..."\n\
\n\
# 启动Ollama服务\n\
ollama serve &\n\
sleep 10\n\
\n\
# 验证模型\n\
ollama list\n\
\n\
# 启动Streamlit应用\n\
streamlit run apppro.py --server.address=0.0.0.0 --server.port=8501\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
EOF

echo "🐳 创建docker-compose.yml..."
cat > rag-pro-max-docker-offline/docker-compose.yml << 'EOF'
version: '3.8'

services:
  rag-pro-max:
    build: .
    ports:
      - "8501:8501"
      - "11434:11434"
    volumes:
      - ./vector_db_storage:/app/vector_db_storage
      - ./chat_histories:/app/chat_histories
      - ./app_logs:/app/app_logs
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
EOF

echo "📝 创建Docker部署说明..."
cat > rag-pro-max-docker-offline/README_DOCKER.md << 'EOF'
# RAG Pro Max Docker离线版

## 🐳 Docker部署

### 构建镜像
```bash
docker build -t rag-pro-max .
```

### 启动服务
```bash
# 方式1: docker-compose (推荐)
docker-compose up -d

# 方式2: 直接运行
docker run -d \
  -p 8501:8501 \
  -p 11434:11434 \
  -v $(pwd)/data:/app/data \
  --name rag-pro-max \
  rag-pro-max
```

### 访问应用
- Web界面: http://localhost:8501
- Ollama API: http://localhost:11434

## 📦 离线特性
- ✅ 所有Python依赖已打包
- ✅ HuggingFace模型已包含
- ✅ Ollama模型已包含 (如果复制成功)
- ✅ 无需网络连接运行

## 🔧 故障排除
如果Ollama模型未正确复制，容器启动后手动下载:
```bash
docker exec -it rag-pro-max bash
ollama pull gemma2:2b
```
EOF

echo "🗜️ 打包Docker离线版..."
tar -czf rag-pro-max-docker-offline.tar.gz rag-pro-max-docker-offline/

echo "✅ Docker离线包构建完成"
echo "📦 文件: rag-pro-max-docker-offline.tar.gz"
ls -lh rag-pro-max-docker-offline.tar.gz

echo ""
echo "🐳 Docker部署步骤:"
echo "1. 解压: tar -xzf rag-pro-max-docker-offline.tar.gz"
echo "2. 进入: cd rag-pro-max-docker-offline"
echo "3. 构建: docker build -t rag-pro-max ."
echo "4. 启动: docker-compose up -d"
echo "5. 访问: http://localhost:8501"
