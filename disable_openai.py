#!/usr/bin/env python3
"""
禁用OpenAI连接 - 使用本地模型
"""

import os

# 设置环境变量禁用OpenAI
os.environ['DISABLE_OPENAI'] = 'true'
os.environ['USE_LOCAL_LLM'] = 'true'
os.environ['OFFLINE_MODE'] = 'true'

print("🔒 已禁用OpenAI连接")
print("✅ 强制使用本地模型")

# 重启应用
os.system("pkill -f 'streamlit run'")
os.system("sleep 2")
os.system("cd /Users/zhaosj/Documents/rag-pro-max && DISABLE_OPENAI=true USE_LOCAL_LLM=true streamlit run src/apppro.py --server.headless=true &")

print("🚀 应用已重启，OpenAI连接已禁用")
