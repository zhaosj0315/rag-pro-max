# RAG Pro Max v2.3.1 安装指南

## 🎯 版本说明

v2.3.1 引入了三大智能化功能，需要额外的依赖包支持。本指南将帮助您完整安装所有功能。

## 📋 系统要求

### 基础要求
- **操作系统**: macOS 10.15+, Linux (Ubuntu 18.04+), Windows 10+
- **Python**: 3.8+ (推荐 3.9+)
- **内存**: 8GB+ (推荐 16GB+)
- **存储**: 15GB+ 可用空间
- **网络**: 首次安装需要下载模型

### GPU要求 (可选)
- **NVIDIA GPU**: CUDA 11.0+ 支持
- **Apple Silicon**: M1/M2/M3/M4 系列
- **GPU内存**: 4GB+ (推荐 8GB+)

## 🚀 快速安装

### 一键安装 (推荐)
```bash
# 1. 克隆项目
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max

# 2. 运行v2.1安装脚本
python install_v2.1_features.py

# 3. 启动应用
./start.sh
```

### 手动安装
```bash
# 1. 基础依赖
pip install -r requirements.txt

# 2. GPU依赖 (根据设备选择)
# NVIDIA GPU用户
pip install paddlepaddle-gpu paddleocr torch torchvision

# Apple Silicon用户
pip install paddlepaddle paddleocr torch torchvision

# CPU用户
pip install paddlepaddle paddleocr torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 3. 创建配置目录
mkdir -p config

# 4. 启动应用
streamlit run src/apppro.py
```

## 🔧 分步安装指南

### Step 1: 基础环境
```bash
# 检查Python版本
python --version  # 应该 >= 3.8

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 升级pip
pip install --upgrade pip
```

### Step 2: 基础依赖
```bash
# 安装基础依赖
pip install streamlit llama-index chromadb
pip install sentence-transformers torch torchvision
pip install pdf2image pytesseract pillow
pip install psutil requests ollama
```

### Step 3: v2.1新功能依赖
```bash
# 根据您的设备选择合适的版本

# === NVIDIA GPU用户 ===
pip install paddlepaddle-gpu
pip install paddleocr

# === Apple Silicon用户 ===
pip install paddlepaddle
pip install paddleocr

# === CPU用户 ===
pip install paddlepaddle
pip install paddleocr
```

### Step 4: 验证安装
```bash
# 运行安装验证
python install_v2.1_features.py

# 或手动验证
python -c "
import torch
import paddleocr
from src.utils.adaptive_scheduler import adaptive_scheduler
print('✅ v2.1功能安装成功')
"
```

## 🎮 GPU配置指南

### NVIDIA GPU配置
```bash
# 1. 检查CUDA版本
nvidia-smi

# 2. 安装对应的PyTorch版本
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. 安装PaddlePaddle GPU版本
pip install paddlepaddle-gpu

# 4. 验证GPU可用性
python -c "
import torch
print(f'CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU设备: {torch.cuda.get_device_name(0)}')
    print(f'GPU内存: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f}GB')
"
```

### Apple Silicon配置
```bash
# 1. 安装MPS支持的PyTorch
pip install torch torchvision

# 2. 安装PaddlePaddle
pip install paddlepaddle

# 3. 验证MPS可用性
python -c "
import torch
print(f'MPS可用: {torch.backends.mps.is_available()}')
print(f'MPS构建: {torch.backends.mps.is_built()}')
"
```

## 📦 Docker安装

### 使用预构建镜像
```bash
# 1. 拉取镜像
docker pull ragpromax/v2.1:latest

# 2. 运行容器
docker run -p 8501:8501 -v $(pwd)/data:/app/data ragpromax/v2.1:latest

# 3. 访问应用
# http://localhost:8501
```

### 自构建镜像
```bash
# 1. 构建镜像
docker build -t rag-pro-max:v2.1 .

# 2. 运行容器
docker-compose up -d

# 3. 查看日志
docker logs -f rag-pro-max
```

## 🔍 安装验证

### 功能测试
```bash
# 运行完整功能测试
python -c "
from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer

# 测试自适应调度
from src.utils.adaptive_scheduler import adaptive_scheduler
workers, strategy, confidence = adaptive_scheduler.get_optimal_strategy(10)
print(f'✅ 自适应调度: {strategy}')

# 测试GPU加速
from src.utils.gpu_ocr_accelerator import gpu_ocr_accelerator
device_info = gpu_ocr_accelerator.get_device_info()
print(f'✅ GPU加速: {device_info[\"device\"]}')

# 测试进度监控
from src.ui.progress_monitor import progress_monitor
progress_monitor.start_task('test', '测试', 10)
print('✅ 进度监控: 正常')

print('🎉 所有v2.1功能正常！')
"
```

### 性能基准测试
```bash
# 运行性能基准测试
python -c "
from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer
results = enhanced_ocr_optimizer.benchmark_performance()
print('📊 性能基准测试结果:')
for key, value in results.items():
    print(f'  {key}: {value}')
"
```

## ⚠️ 故障排除

### 常见安装问题

**问题 1**: `ImportError: No module named 'paddleocr'`
```bash
# 解决方案
pip install paddleocr
# 如果仍然失败
pip install paddleocr --no-cache-dir
```

**问题 2**: `CUDA out of memory`
```bash
# 解决方案：降低批量大小
python -c "
from src.utils.gpu_ocr_accelerator import gpu_ocr_accelerator
gpu_ocr_accelerator.batch_size = 2  # 降低批量大小
"
```

**问题 3**: `MPS backend not available`
```bash
# 解决方案：更新PyTorch
pip install --upgrade torch torchvision
```

**问题 4**: 依赖冲突
```bash
# 解决方案：使用虚拟环境
python -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements.txt
python install_v2.1_features.py
```

### 性能优化建议

**GPU内存优化**:
```python
# 在 src/utils/gpu_ocr_accelerator.py 中调整
batch_size = 2  # 降低批量大小
```

**CPU保护调整**:
```python
# 在 src/utils/ocr_optimizer.py 中调整
max_cpu_usage = 80.0  # 降低CPU限制
```

**学习速度调整**:
```python
# 在 src/utils/adaptive_scheduler.py 中调整
learning_rate = 0.2  # 提高学习速度
```

## 📊 安装验证清单

安装完成后，请确认以下功能正常：

- [ ] ✅ 基础应用启动正常
- [ ] ✅ 文档上传和处理正常
- [ ] ✅ 自适应调度器工作正常
- [ ] ✅ 实时进度监控显示正常
- [ ] ✅ GPU加速器初始化成功
- [ ] ✅ 性能统计面板显示数据
- [ ] ✅ 基准测试运行成功

## 🎯 下一步

安装完成后，建议：

1. **运行基准测试** - 了解系统性能基线
2. **上传测试文档** - 让系统开始学习
3. **查看性能统计** - 监控系统学习进度
4. **阅读功能文档** - 了解新功能详细用法

## 📞 获取帮助

如果安装过程中遇到问题：

1. **查看日志** - 检查 `app_logs/` 目录
2. **运行诊断** - `python install_v2.1_features.py`
3. **查看文档** - 阅读 `docs/TROUBLESHOOTING.md`
4. **提交Issue** - 在GitHub上报告问题

祝您使用愉快！🚀
