# 部署指南

本文档介绍 RAG Pro Max 的各种部署方式。

## 📋 目录

- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [macOS 应用](#macos-应用)
- [云端部署](#云端部署)
- [生产环境](#生产环境)

---

## 本地部署

### 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8GB | 16GB+ |
| 磁盘 | 20GB | 50GB+ |
| GPU | 无 | 支持 CUDA |
| Python | 3.8+ | 3.10/3.12 |

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行测试
./scripts/test.sh

# 4. 启动应用
./scripts/start.sh
```

### 配置优化

#### 1. 环境变量

创建 `.env` 文件：

```bash
# LLM 配置
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# 系统配置
MAX_WORKERS=80
CHUNK_SIZE=500
TOP_K=5
```

#### 2. 配置文件

编辑 `app_config.json`:

```json
{
  "output_path": "./vector_db_storage",
  "llm_url_ollama": "http://127.0.0.1:11434",
  "embed_model_hf": "BAAI/bge-small-zh-v1.5"
}
```

#### 3. RAG 参数

编辑 `rag_config.json`:

```json
{
  "chunk_size": 500,
  "chunk_overlap": 50,
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

### 性能调优

#### CPU 优化

```python
# src/apppro.py 中调整线程数
max_workers = min(80, os.cpu_count() * 4)
```

#### 内存优化

```bash
# 限制 Python 内存使用
export PYTHONMALLOC=malloc
ulimit -v 16000000  # 限制 16GB
```

#### GPU 加速

确保 PyTorch 支持 GPU：

```python
import torch
print(torch.cuda.is_available())  # 应返回 True
```

---

## Docker 部署

### 快速部署

```bash
# 1. 构建镜像
./scripts/docker-build.sh

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker logs -f rag-pro-max

# 4. 访问应用
open http://localhost:8501
```

### Docker Compose 配置

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  rag-pro-max:
    build: .
    container_name: rag-pro-max
    ports:
      - "8501:8501"
    volumes:
      - ./vector_db_storage:/app/vector_db_storage
      - ./chat_histories:/app/chat_histories
      - ./hf_cache:/app/hf_cache
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    deploy:
      resources:
        limits:
          cpus: '12'
          memory: 48G
    restart: unless-stopped
```

### 资源限制

根据服务器配置调整：

```yaml
deploy:
  resources:
    limits:
      cpus: '8'      # CPU 核心数
      memory: 32G    # 内存限制
    reservations:
      cpus: '4'
      memory: 16G
```

### 数据持久化

确保挂载以下目录：

```yaml
volumes:
  - ./vector_db_storage:/app/vector_db_storage  # 向量数据库
  - ./chat_histories:/app/chat_histories        # 对话历史
  - ./hf_cache:/app/hf_cache                    # 模型缓存
  - ./app_logs:/app/app_logs                    # 应用日志
```

### Docker 管理

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看日志
docker-compose logs -f

# 进入容器
docker exec -it rag-pro-max bash

# 更新镜像
docker-compose pull
docker-compose up -d
```

---

## macOS 应用

### 打包应用

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 执行打包
./scripts/build_mac.sh

# 3. 测试应用
open dist/RAG_Pro_Max.app
```

### 打包配置

`RAG_Pro_Max.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/apppro.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('hf_cache', 'hf_cache'),
        ('*.json', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'llama_index',
        # ... 其他依赖
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
```

### 签名和公证

```bash
# 代码签名
codesign --force --deep --sign "Developer ID" dist/RAG_Pro_Max.app

# 公证
xcrun notarytool submit dist/RAG_Pro_Max.app.zip \
  --apple-id "your@email.com" \
  --password "app-specific-password" \
  --team-id "TEAM_ID"
```

### 分发

```bash
# 创建 DMG
hdiutil create -volname "RAG Pro Max" \
  -srcfolder dist/RAG_Pro_Max.app \
  -ov -format UDZO \
  RAG_Pro_Max.dmg
```

---

## 云端部署

### AWS 部署

#### EC2 实例

**推荐配置**:
- 实例类型: `t3.xlarge` (4 vCPU, 16GB RAM)
- 存储: 50GB EBS
- 操作系统: Ubuntu 22.04 LTS

**部署步骤**:

```bash
# 1. 连接实例
ssh -i key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# 2. 安装依赖
sudo apt update
sudo apt install python3-pip git

# 3. 克隆项目
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max

# 4. 安装依赖
pip3 install -r requirements.txt

# 5. 配置环境
export OPENAI_API_KEY="your-key"

# 6. 启动服务
nohup streamlit run src/apppro.py --server.port 8501 &
```

#### 使用 Docker

```bash
# 1. 安装 Docker
sudo apt install docker.io docker-compose

# 2. 构建和启动
docker-compose up -d

# 3. 配置安全组
# 开放端口 8501
```

### Google Cloud Platform

#### Cloud Run 部署

```bash
# 1. 构建镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/rag-pro-max

# 2. 部署服务
gcloud run deploy rag-pro-max \
  --image gcr.io/PROJECT_ID/rag-pro-max \
  --platform managed \
  --region us-central1 \
  --memory 16Gi \
  --cpu 4
```

### Azure 部署

#### Container Instances

```bash
# 1. 创建资源组
az group create --name rag-pro-max-rg --location eastus

# 2. 部署容器
az container create \
  --resource-group rag-pro-max-rg \
  --name rag-pro-max \
  --image your-registry/rag-pro-max:latest \
  --cpu 4 \
  --memory 16 \
  --ports 8501
```

---

## 生产环境

### 反向代理

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
    }
}
```

#### HTTPS 配置

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 进程管理

#### Systemd 服务

创建 `/etc/systemd/system/rag-pro-max.service`:

```ini
[Unit]
Description=RAG Pro Max
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/rag-pro-max
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin"
Environment="PYTHONPATH=/home/ubuntu/rag-pro-max"
ExecStart=/usr/bin/streamlit run src/apppro.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable rag-pro-max
sudo systemctl start rag-pro-max
sudo systemctl status rag-pro-max
```

### 监控和日志

#### 日志管理

```bash
# 查看应用日志
tail -f app_logs/log_$(date +%Y%m%d).jsonl

# 查看系统日志
sudo journalctl -u rag-pro-max -f
```

#### 监控指标

使用 Prometheus + Grafana：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rag-pro-max'
    static_configs:
      - targets: ['localhost:8501']
```

### 备份策略

#### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/rag-pro-max"

# 备份向量数据库
tar -czf $BACKUP_DIR/vector_db_$DATE.tar.gz vector_db_storage/

# 备份对话历史
tar -czf $BACKUP_DIR/chat_histories_$DATE.tar.gz chat_histories/

# 备份配置
cp app_config.json $BACKUP_DIR/app_config_$DATE.json

# 清理旧备份（保留 7 天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

设置定时任务：

```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh
```

### 安全加固

#### 1. 防火墙配置

```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### 2. 环境变量保护

```bash
# 使用密钥管理服务
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id openai-key --query SecretString --output text)
```

#### 3. 访问控制

在 Nginx 中添加基本认证：

```nginx
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8501;
}
```

---

## 故障排除

### 常见问题

#### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8501

# 杀死进程
kill -9 PID
```

#### 内存不足

```bash
# 增加 swap
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER .
chmod -R 755 .
```

---

## 性能基准

### 测试环境

- **CPU**: 8 核
- **内存**: 32GB
- **GPU**: 无
- **网络**: 1Gbps

### 性能指标

| 指标 | 数值 |
|------|------|
| 并发用户 | 10 |
| 查询延迟 | 2-3 秒 |
| 文档处理 | ~3 页/秒 |
| 内存占用 | 10-15GB |
| CPU 使用 | 30-40% |

---

**最后更新**: 2025-12-07
