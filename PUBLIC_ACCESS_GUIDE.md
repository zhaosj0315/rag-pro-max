# RAG Pro Max 公网访问指南

**版本**: v3.2.2  
**更新日期**: 2026-01-03  
**适用范围**: 公网演示与试用

---

## 🌐 公网访问方案

为了让其他人可以访问和试用 RAG Pro Max，我们提供了多种公网访问方案，**无需修改任何现有代码**。

### 🚀 快速开始

#### 方案1: ngrok 隧道 (推荐)
```bash
# 一键启动 (推荐)
./scripts/start-ngrok.sh
```

#### 方案2: SSH 隧道 (无需安装)
```bash
# 完全免费，无需安装任何软件
./scripts/start-ssh-tunnel.sh
```

#### 方案3: 完整选择菜单
```bash
# 查看所有方案并选择
./scripts/start-public.sh
```

---

## 📋 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **ngrok** | 稳定、HTTPS、功能丰富 | 需要注册、免费版有限制 | 正式演示、长期使用 |
| **SSH隧道** | 完全免费、无需安装 | 依赖第三方服务 | 快速演示、临时分享 |
| **localtunnel** | 简单、无需注册 | 需要Node.js、稳定性一般 | 快速测试 |
| **自定义配置** | 完全控制、无第三方依赖 | 需要网络知识、安全风险 | 企业内网 |

---

## 🔥 推荐方案详解

### 方案1: ngrok (最推荐)

**安装 ngrok:**
```bash
# macOS
brew install ngrok/ngrok/ngrok

# Linux
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc
echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Windows
# 下载: https://ngrok.com/download
```

**配置 ngrok:**
```bash
# 1. 注册账号: https://ngrok.com
# 2. 获取 authtoken
# 3. 配置 token
ngrok authtoken YOUR_TOKEN
```

**启动:**
```bash
./scripts/start-ngrok.sh
```

**效果:**
- 🌐 获得类似 `https://abc123.ngrok.io` 的公网地址
- 🔒 自动 HTTPS 支持
- 📊 Web 控制台: `http://localhost:4040`
- ⚡ 稳定可靠

### 方案2: SSH 隧道 (最简单)

**无需安装，直接使用:**
```bash
./scripts/start-ssh-tunnel.sh
```

**效果:**
- 🌐 获得类似 `https://rag-pro-max-123456.serveo.net` 的公网地址
- 🔒 自动 HTTPS 支持
- 💰 完全免费
- 🚀 无需注册

---

## 📱 使用流程

### 1. 选择方案并启动
```bash
# 推荐使用 ngrok
./scripts/start-ngrok.sh

# 或使用 SSH 隧道
./scripts/start-ssh-tunnel.sh
```

### 2. 获取公网地址
脚本会自动显示公网访问地址，例如：
```
🎉 公网访问已就绪！
==================

🌐 公网地址: https://abc123.ngrok.io
🏠 本地地址: http://localhost:8501
```

### 3. 分享给其他人
将公网地址分享给其他人，他们就可以直接访问和试用 RAG Pro Max。

### 4. 停止服务
按 `Ctrl+C` 停止服务。

---

## 🛡️ 安全注意事项

### ⚠️ 重要提醒
- **数据安全**: 公网访问意味着任何人都可以访问，请注意数据安全
- **临时使用**: 建议仅在演示和试用时开启公网访问
- **访问控制**: 考虑在应用层添加访问密码或IP白名单
- **监控访问**: 注意监控访问日志，防止恶意使用

### 🔒 安全建议
1. **限时开放**: 仅在需要时开启公网访问
2. **监控流量**: 注意观察访问流量和用户行为
3. **备份数据**: 在开放公网访问前备份重要数据
4. **定期检查**: 定期检查系统安全状态

---

## 🚨 故障排除

### 常见问题

**Q: ngrok 提示 "authtoken" 错误**
A: 需要注册 ngrok 账号并配置 authtoken
```bash
# 1. 注册: https://ngrok.com
# 2. 获取 token 并配置
ngrok authtoken YOUR_TOKEN
```

**Q: SSH 隧道连接失败**
A: 检查网络连接，或尝试重新运行脚本
```bash
# 重新运行
./scripts/start-ssh-tunnel.sh
```

**Q: 应用启动失败**
A: 检查依赖和端口占用
```bash
# 检查端口
lsof -i :8501

# 运行测试
python tests/factory_test.py
```

**Q: 公网地址无法访问**
A: 等待几秒钟，或检查防火墙设置

---

## 💡 使用技巧

### 演示技巧
1. **提前测试**: 在正式演示前先测试公网访问
2. **备用方案**: 准备多个方案以防某个服务不可用
3. **网络检查**: 确保网络连接稳定
4. **功能演示**: 准备好演示用的文档和问题

### 优化建议
1. **选择合适方案**: 根据使用场景选择最适合的方案
2. **监控性能**: 注意观察系统性能和响应速度
3. **用户引导**: 为试用用户提供简单的使用指导
4. **收集反馈**: 收集用户反馈以改进产品

---

## 📞 技术支持

如果在使用过程中遇到问题：

1. **查看日志**: 检查控制台输出的错误信息
2. **重新启动**: 尝试重新运行启动脚本
3. **检查网络**: 确保网络连接正常
4. **更换方案**: 尝试其他公网访问方案

---

**🎯 目标**: 让任何人都能轻松访问和试用 RAG Pro Max，展示企业级AI知识库的强大功能！

---

*本指南提供的所有方案都不会修改现有代码，确保系统安全性和稳定性*
