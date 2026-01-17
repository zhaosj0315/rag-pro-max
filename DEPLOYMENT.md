# RAG Pro Max v6.7.0 企业级部署指南 (Governance & Unification Edition)

**版本**: v6.7.0  
**更新日期**: 2026-01-17  
**适用范围**: 生产环境部署、高保真附件解析、macOS/Linux 高可用版

RAG Pro Max v6.7.0 引入了归一化解析管线与终端自愈诊断，建议在部署时同步配置 `app_logs/` 权限以支持终端审计。

**🔥 v6.7.0 企业级特性**:
- 🛡️ **资源治理矩阵**: Manifest 与文件系统双重透视，支持资产全生命周期管理。
- 💻 **终端自愈诊断**: 端口级存活监测，解决 WebSSH 服务死锁问题。
- 📎 **万能附件解析**: 归一化核心解析流，支持 20+ 种格式即时解析。
- 🔋 **数据持久化加固**: 隔离 RAG 索引与 SQL 数据库，确保业务数据物理安全性。
- 🛡️ **工业级容错**: 内置 SQL 自动修复引擎与显式异常诊断 UI。
- 🚀 **真数采样技术**: 提升 AI 对 2025+ 未来年度数据的感知精度。

## 🏢 企业环境要求

### 🔒 安全要求
- **网络隔离**: 支持完全离线部署。
- **数据主权**: 所有 CSV/DB 均存储在 `vector_db_storage` 的子目录中，支持物理迁移。

### 💻 硬件配置
- **最低配置**: 8GB RAM, 20GB 存储, Python 3.10+ (推荐)。
- **依赖库更新**: 必须安装 `plotly`, `pandas`, `sqlite3`。

## 🚀 快速部署

### 1. 一键部署脚本
```bash
# 安装核心依赖
pip install -r requirements.txt

# 验证可视化引擎
python -c "import plotly; print(plotly.__version__)"
```

#### Windows
```cmd
# 克隆项目
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max

# 自动部署
scripts\deploy_windows.bat
```

### 2. 启动应用

#### 推荐方式 (包含测试)
```bash
./start.sh
```

#### 直接启动
```bash
streamlit run src/apppro.py
```

#### 指定端口启动
```bash
streamlit run src/apppro.py --server.port 8501
```

## 🐳 Docker 部署

### 1. 使用预构建镜像
```bash
# 拉取镜像
docker pull ragpromax/rag-pro-max:v5.5.8

# 运行容器
docker run -d \
  --name rag-pro-max \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  ragpromax/rag-pro-max:v5.5.8
```

### 2. 本地构建镜像
```bash
# 构建镜像
./scripts/docker-build.sh

# 或手动构建
docker build -t rag-pro-max:local .
```

### 3. Docker Compose 部署
```bash
# 启动完整服务栈
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### docker-compose.yml 配置
```yaml
version: '3.8'
services:
  rag-pro-max:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app
      - STREAMLIT_SERVER_PORT=8501
    restart: unless-stopped
    
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

## ⚙️ 环境配置

### 1. Python 环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境变量配置
```bash
# 创建 .env 文件
cat > .env << EOF
# 应用配置
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 日志配置
PADDLE_LOG_LEVEL=50
GLOG_minloglevel=3
OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1

# GPU配置 (可选)
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# API配置 (可选)
OPENAI_API_KEY=your-api-key
OLLAMA_BASE_URL=http://localhost:11434
EOF
```

### 3. 配置文件设置
```bash
# 复制配置模板
cp config/app_config.json.template config/app_config.json
cp config/rag_config.json.template config/rag_config.json

# 编辑配置文件
nano config/app_config.json
```

## 🔧 生产环境部署

### 1. 系统服务配置

#### systemd 服务 (Linux)
```bash
# 创建服务文件
sudo tee /etc/systemd/system/rag-pro-max.service << EOF
[Unit]
Description=RAG Pro Max Service
After=network.target

[Service]
Type=simple
User=raguser
WorkingDirectory=/opt/rag-pro-max
Environment=PATH=/opt/rag-pro-max/venv/bin
ExecStart=/opt/rag-pro-max/venv/bin/streamlit run src/apppro.py --server.port 8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable rag-pro-max
sudo systemctl start rag-pro-max
```

#### launchd 服务 (macOS)
```bash
# 创建 plist 文件
cat > ~/Library/LaunchAgents/com.ragpromax.service.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ragpromax.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/streamlit</string>
        <string>run</string>
        <string>src/apppro.py</string>
        <string>--server.port</string>
        <string>8501</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/rag-pro-max</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# 加载服务
launchctl load ~/Library/LaunchAgents/com.ragpromax.service.plist
```

### 2. 反向代理配置

#### Nginx 配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
```

#### Apache 配置
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    ProxyPass / http://localhost:8501/
    ProxyPassReverse / http://localhost:8501/
    
    # WebSocket 支持
    RewriteEngine on
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:8501/$1" [P,L]
</VirtualHost>
```

### 3. SSL/HTTPS 配置
```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com

# 或使用自签名证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## 🔄 集群部署

### 1. Kubernetes 部署
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-pro-max
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-pro-max
  template:
    metadata:
      labels:
        app: rag-pro-max
    spec:
      containers:
      - name: rag-pro-max
        image: ragpromax/rag-pro-max:v5.5.8
        ports:
        - containerPort: 8501
        env:
        - name: STREAMLIT_SERVER_PORT
          value: "8501"
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

---
apiVersion: v1
kind: Service
metadata:
  name: rag-pro-max-service
spec:
  selector:
    app: rag-pro-max
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

### 2. Docker Swarm 部署
```yaml
# docker-stack.yml
version: '3.8'
services:
  rag-pro-max:
    image: ragpromax/rag-pro-max:v5.5.8
    ports:
      - "8501:8501"
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    networks:
      - rag-network

networks:
  rag-network:
    driver: overlay
```

## 📊 监控和日志

### 1. 应用监控
```bash
# 启用监控
export ENABLE_MONITORING=true
export METRICS_PORT=9090

# Prometheus 配置
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rag-pro-max'
    static_configs:
      - targets: ['localhost:9090']
EOF
```

### 2. 日志管理
```bash
# 配置日志轮转
sudo tee /etc/logrotate.d/rag-pro-max << EOF
/var/log/rag-pro-max/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 raguser raguser
}
EOF
```

### 3. 健康检查
```bash
# 健康检查脚本
cat > health_check.sh << EOF
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/health)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy"
    exit 1
fi
EOF

chmod +x health_check.sh
```

## 🛡️ 安全配置

### 1. 防火墙设置
```bash
# Ubuntu/Debian
sudo ufw allow 8501/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

### 2. 用户权限
```bash
# 创建专用用户
sudo useradd -r -s /bin/false raguser
sudo chown -R raguser:raguser /opt/rag-pro-max
```

### 3. 数据备份
```bash
# 备份脚本
cat > backup.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/rag-pro-max_$DATE.tar.gz \
    /opt/rag-pro-max/vector_db_storage \
    /opt/rag-pro-max/config \
    /opt/rag-pro-max/chat_histories
EOF

# 定时备份
echo "0 2 * * * /opt/rag-pro-max/backup.sh" | sudo crontab -
```

## 🔧 故障排除

### 1. 常见问题
```bash
# 端口占用
sudo lsof -i :8501
sudo kill -9 <PID>

# 权限问题
sudo chown -R $USER:$USER /opt/rag-pro-max
chmod +x scripts/*.sh

# 依赖问题
pip install --upgrade -r requirements.txt
```

### 2. 性能优化
```bash
# 系统优化
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max=134217728' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 3. 日志分析
```bash
# 查看应用日志
tail -f app_logs/log_$(date +%Y%m%d).jsonl

# 查看系统日志
sudo journalctl -u rag-pro-max -f
```

## 📈 扩展部署

### 1. 多实例部署
```bash
# 启动多个实例
for port in 8501 8502 8503; do
    streamlit run src/apppro.py --server.port $port &
done
```

### 2. 负载均衡
```nginx
upstream rag_backend {
    server localhost:8501;
    server localhost:8502;
    server localhost:8503;
}

server {
    listen 80;
    location / {
        proxy_pass http://rag_backend;
    }
}
```

### 3. 数据库集群
```bash
# ChromaDB 集群配置
export CHROMA_SERVER_HOST=0.0.0.0
export CHROMA_SERVER_HTTP_PORT=8000
chroma run --host 0.0.0.0 --port 8000
```

## 🔧 维护和监控

### 文档同步检查
```bash
# 检查文档是否与代码同步
python scripts/check_documentation_sync.py
```

### 推送前安全检查
```bash
# 确保遵守非必要不推送原则
./scripts/pre_push_safety_check.sh
```

### 出厂测试验证
```bash
# 运行完整出厂测试
python tests/factory_test.py

# 快速测试
python tests/factory_test.py --quick
```

