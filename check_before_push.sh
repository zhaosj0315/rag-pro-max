#!/bin/bash
# 推送前检查脚本

echo "🔍 推送前检查..."

# 1. 检查是否有敏感文件
echo "1️⃣ 检查敏感文件..."
sensitive_files=$(find . -name "*.key" -o -name "*.secret" -o -name ".env" -o -name "api_key*" | grep -v ".gitignore")
if [ -n "$sensitive_files" ]; then
    echo "❌ 发现敏感文件:"
    echo "$sensitive_files"
    exit 1
fi

# 2. 检查大文件
echo "2️⃣ 检查大文件..."
large_files=$(find . -size +50M -not -path "./vector_db_storage/*" -not -path "./hf_cache/*" -not -path "./temp_uploads/*" -not -path "./chat_histories/*" -not -path "./app_logs/*" -not -path "./.git/*" -not -name "demo.mp4" -not -name "demo_compressed.mp4")
if [ -n "$large_files" ]; then
    echo "❌ 发现大文件 (>50MB):"
    echo "$large_files"
    exit 1
fi

# 3. 检查必要文件
echo "3️⃣ 检查必要文件..."
required_files=("README.md" "requirements.txt" "src/apppro_final.py" "CHANGELOG.md" "LICENSE")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done

# 4. 检查运行时文件是否被误加入
echo "4️⃣ 检查运行时文件..."
runtime_files=$(git status --porcelain | grep -E "(vector_db_storage|chat_histories|temp_uploads|app_logs|hf_cache|__pycache__|\.pyc|\.DS_Store)")
if [ -n "$runtime_files" ]; then
    echo "❌ 发现运行时文件被加入版本控制:"
    echo "$runtime_files"
    echo "请运行: git reset HEAD <文件名> 来移除"
    exit 1
fi

# 5. 检查代码语法
echo "5️⃣ 检查Python语法..."
python_files=$(find src -name "*.py")
for file in $python_files; do
    python -m py_compile "$file" 2>/dev/null || {
        echo "❌ 语法错误: $file"
        exit 1
    }
done

echo "✅ 推送前检查通过"
