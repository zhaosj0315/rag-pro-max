
# 离线模式配置
OFFLINE_MODE = True
DISABLE_QUERY_REWRITE = True
DISABLE_SUGGESTION_GENERATION = True
USE_LOCAL_LLM_ONLY = True

# 本地模型配置
LOCAL_LLM_CONFIG = {
    "api_base": "http://localhost:11434",
    "model": "gpt-oss:20b",
    "temperature": 0.7
}

print("🔒 离线模式已启用")
