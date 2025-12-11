#!/usr/bin/env python3
"""
强制使用本地LLM，禁用OpenAI
"""

def patch_llm_config():
    """修补LLM配置，强制使用本地模型"""
    
    # 创建本地LLM配置
    local_config = '''
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
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/config/force_local_llm.py', 'w') as f:
        f.write(local_config)
    
    print("✅ 本地LLM配置已创建")

def increase_ocr_timeout():
    """增加OCR超时时间"""
    
    # 修改批量OCR处理器的超时
    import fileinput
    import sys
    
    file_path = '/Users/zhaosj/Documents/rag-pro-max/src/utils/batch_ocr_processor.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 将300秒改为1200秒（20分钟）
    content = content.replace('timeout=300', 'timeout=1200')
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ OCR超时时间已增加到20分钟")

def main():
    print("🔧 修复本地LLM和OCR超时")
    print("="*40)
    
    patch_llm_config()
    increase_ocr_timeout()
    
    # 重启应用
    import os
    os.system("pkill -f 'streamlit run'")
    os.system("sleep 2")
    
    # 启动时强制使用本地配置
    cmd = '''cd /Users/zhaosj/Documents/rag-pro-max && \
OPENAI_API_KEY="" \
DISABLE_OPENAI=true \
USE_LOCAL_LLM=true \
streamlit run src/apppro.py --server.headless=true &'''
    
    os.system(cmd)
    
    print("✅ 应用已重启")
    print("📋 本地可用模型:")
    print("   - gpt-oss:20b")
    print("   - qwen3:32b") 
    print("   - qwen3-coder:latest")
    print("💡 应用会自动选择可用的本地模型")

if __name__ == "__main__":
    main()
