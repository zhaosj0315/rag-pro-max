#!/bin/bash
# RAG Pro Max Linux离线部署脚本

set -e

echo "🐧 RAG Pro Max Linux离线部署"
echo "=================================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root权限运行此脚本"
    echo "   sudo $0"
    exit 1
fi

# 检查系统
if ! command -v docker &> /dev/null; then
    echo "📦 安装Docker..."
    
    # 更新包管理器
    apt-get update
    
    # 安装Docker依赖
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # 添加Docker仓库
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 启动Docker服务
    systemctl start docker
    systemctl enable docker
    
    echo "✅ Docker安装完成"
else
    echo "✅ Docker已安装"
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose安装完成"
else
    echo "✅ Docker Compose已安装"
fi

# 创建应用目录
APP_DIR="/opt/rag-pro-max"
echo "📁 创建应用目录: ${APP_DIR}"
mkdir -p "${APP_DIR}"
cd "${APP_DIR}"

# 创建数据目录
mkdir -p data/{vector_db,chat_histories,app_logs}
mkdir -p config

# 检查镜像文件
IMAGE_FILE="rag-pro-max-offline-v2.4.1.tar.gz"
if [ -f "${IMAGE_FILE}" ]; then
    echo "📦 加载Docker镜像..."
    docker load < "${IMAGE_FILE}"
    echo "✅ 镜像加载完成"
else
    echo "❌ 未找到镜像文件: ${IMAGE_FILE}"
    echo "   请将镜像文件复制到当前目录"
    exit 1
fi

# 创建docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  rag-pro-max:
    image: rag-pro-max-offline:v2.4.1
    container_name: rag-pro-max-offline
    ports:
      - "8501:8501"
      - "11434:11434"
    volumes:
      - ./data/vector_db:/app/vector_db_storage
      - ./data/chat_histories:/app/chat_histories
      - ./data/app_logs:/app/app_logs
      - ./config:/app/config
    environment:
      - HF_HUB_OFFLINE=1
      - TRANSFORMERS_OFFLINE=1
    deploy:
      resources:
        limits:
          memory: 16G
    restart: unless-stopped
EOF

# 创建管理脚本
cat > manage.sh << 'EOF'
#!/bin/bash
# RAG Pro Max 管理脚本

case "$1" in
    start)
        echo "🚀 启动RAG Pro Max..."
        docker-compose up -d
        echo "✅ 服务已启动"
        echo "   访问地址: http://localhost:8501"
        ;;
    stop)
        echo "⏹️ 停止RAG Pro Max..."
        docker-compose down
        echo "✅ 服务已停止"
        ;;
    restart)
        echo "🔄 重启RAG Pro Max..."
        docker-compose restart
        echo "✅ 服务已重启"
        ;;
    logs)
        echo "📋 查看日志..."
        docker-compose logs -f
        ;;
    status)
        echo "📊 服务状态:"
        docker-compose ps
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|logs|status}"
        exit 1
        ;;
esac
EOF

chmod +x manage.sh

# 设置权限
chown -R 1000:1000 data/
chmod -R 755 data/

echo ""
echo "🎉 部署完成!"
echo ""
echo "📋 管理命令:"
echo "  启动服务: ./manage.sh start"
echo "  停止服务: ./manage.sh stop"
echo "  重启服务: ./manage.sh restart"
echo "  查看日志: ./manage.sh logs"
echo "  查看状态: ./manage.sh status"
echo ""
echo "🌐 访问地址: http://localhost:8501"
echo ""
echo "💡 提示:"
echo "  - 首次启动需要2-3分钟初始化"
echo "  - 所有数据保存在 ${APP_DIR}/data/ 目录"
echo "  - 配置文件在 ${APP_DIR}/config/ 目录"
