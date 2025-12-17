
# 本地LLM配置文件
import os

# 强制使用本地模型
os.environ["USE_LOCAL_LLM"] = "true"
os.environ["DISABLE_OPENAI"] = "true"

# Ollama配置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "gpt-oss:20b",
    "timeout": 30
}

def get_local_llm():
    """获取本地LLM实例"""
    try:
        from llama_index.llms.ollama import Ollama
        
        llm = Ollama(
            model=OLLAMA_CONFIG["model"],
            base_url=OLLAMA_CONFIG["base_url"],
            request_timeout=OLLAMA_CONFIG["timeout"]
        )
        
        print(f"✅ 本地LLM已连接: {OLLAMA_CONFIG['model']}")
        return llm
        
    except Exception as e:
        print(f"❌ 本地LLM连接失败: {e}")
        return None

# 禁用网络功能的配置
DISABLE_FEATURES = {
    "query_rewrite": True,
    "suggestion_generation": True,
    "openai_calls": True,
    "network_requests": True
}
