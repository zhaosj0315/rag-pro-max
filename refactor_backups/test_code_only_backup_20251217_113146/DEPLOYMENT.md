# 🚀 部署指南

## 系统要求

### 最低配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **Python**: 3.8+

### 推荐配置
- **CPU**: 8核心+
- **内存**: 16GB+ RAM
- **GPU**: NVIDIA GPU (可选，用于OCR加速)
- **存储**: 50GB+ SSD

## 平台支持

- ✅ **macOS** (M1/M2/M3/M4, Intel)
- ✅ **Linux** (Ubuntu 20.04+, CentOS 8+)
- ✅ **Windows** (10/11)
- ✅ **Docker** (跨平台)

## 快速部署

### 1. 自动部署（推荐）

#### macOS/Linux
```bash
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max
chmod +x scripts/deploy_linux.sh
./scripts/deploy_linux.sh
```

#### Windows
```cmd
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max
scripts\deploy_windows.bat
```

### 2. Docker 部署

```bash
# 构建镜像
./scripts/docker-build.sh

# 启动服务
docker-compose up -d

# 访问应用
open http://localhost:8501
```

### 3. 手动部署

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir -p vector_db_storage chat_histories temp_uploads hf_cache app_logs

# 5. 启动应用
streamlit run src/apppro.py
```

## 生产环境部署

### 1. 使用 Nginx 反向代理

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

### 2. 使用 systemd 服务

```ini
# /etc/systemd/system/rag-pro-max.service
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

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable rag-pro-max
sudo systemctl start rag-pro-max
```

### 3. 环境变量配置

```bash
# .env 文件
OPENAI_API_KEY=your_openai_key
OLLAMA_BASE_URL=http://localhost:11434
HF_HOME=/path/to/hf_cache
CUDA_VISIBLE_DEVICES=0
```

## 性能优化

### 1. GPU 加速配置

```bash
# 安装CUDA版本的依赖
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证GPU可用性
python -c "import torch; print(torch.cuda.is_available())"
```

### 2. 内存优化

```python
# config/app_config.json
{
  "chunk_size": 512,
  "chunk_overlap": 50,
  "max_concurrent_tasks": 4,
  "enable_gpu_acceleration": true
}
```

### 3. 缓存配置

```bash
# 设置模型缓存目录
export HF_HOME=/data/hf_cache
export TRANSFORMERS_CACHE=/data/hf_cache
```

## 监控和日志

### 1. 应用日志

```bash
# 查看实时日志
tail -f app_logs/log_$(date +%Y%m%d).jsonl

# 日志分析
python view_logs.py --stats
```

### 2. 系统监控

```bash
# 启动监控
python src/system_monitor.py

# 查看资源使用
htop
nvidia-smi  # GPU监控
```

## 故障排除

### 常见问题

1. **端口被占用**
```bash
# 查找占用进程
lsof -i :8501
# 杀死进程
kill -9 <PID>
```

2. **内存不足**
```bash
# 清理缓存
rm -rf hf_cache/*
rm -rf temp_uploads/*
```

3. **GPU不可用**
```bash
# 检查CUDA
nvidia-smi
# 重装GPU版本PyTorch
pip install torch --upgrade --force-reinstall
```

### 日志分析

```bash
# 查看错误日志
grep "ERROR" app_logs/*.jsonl

# 性能分析
python tools/performance_analyzer.py
```

## 安全配置

### 1. 防火墙设置

```bash
# Ubuntu/Debian
sudo ufw allow 8501
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

### 2. SSL/TLS 配置

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

## 备份和恢复

### 1. 数据备份

```bash
# 备份脚本
#!/bin/bash
tar -czf backup_$(date +%Y%m%d).tar.gz   vector_db_storage/   chat_histories/   config/   app_logs/
```

### 2. 恢复数据

```bash
# 恢复脚本
tar -xzf backup_20251213.tar.gz
```

---

更多部署问题请参考 [FAQ文档](./FAQ.md) 或提交 [Issue](https://github.com/yourusername/rag-pro-max/issues)
