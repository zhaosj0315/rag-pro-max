#!/usr/bin/env python3
"""
彻底禁用所有LLM调用
"""

import os

# 设置环境变量
env_vars = {
    'DISABLE_OPENAI': 'true',
    'DISABLE_LLM': 'true', 
    'OFFLINE_MODE': 'true',
    'NO_NETWORK': 'true',
    'SKIP_LLM_CALLS': 'true'
}

for key, value in env_vars.items():
    os.environ[key] = value

print("🔒 已设置离线环境变量")

# 重启应用
os.system("pkill -f 'streamlit run'")
os.system("sleep 2")

# 启动完全离线模式
cmd = "cd /Users/zhaosj/Documents/rag-pro-max && " + " ".join([f"{k}={v}" for k, v in env_vars.items()]) + " streamlit run src/apppro.py --server.headless=true &"
os.system(cmd)

print("✅ 应用已重启，所有LLM调用已禁用")
