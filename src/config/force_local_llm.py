
# 强制本地LLM配置
import os
from llama_index.llms.ollama import Ollama

def get_local_llm():
    """获取本地LLM"""
    try:
        # 使用你本地的模型
        llm = Ollama(
            model="gpt-oss:20b",  # 使用你本地已有的模型
            base_url="http://localhost:11434",
            request_timeout=30
        )
        print("✅ 使用本地模型: gpt-oss:20b")
        return llm
    except:
        try:
            # 备选模型
            llm = Ollama(
                model="qwen3:32b", 
                base_url="http://localhost:11434",
                request_timeout=30
            )
            print("✅ 使用本地模型: qwen3:32b")
            return llm
        except:
            print("❌ 本地模型不可用")
            return None

# 强制禁用OpenAI
os.environ["OPENAI_API_KEY"] = ""
os.environ["DISABLE_OPENAI"] = "true"

# 导出本地LLM
LOCAL_LLM = get_local_llm()
