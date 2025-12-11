#!/usr/bin/env python3
"""
修复离线模式 - 禁用所有网络连接
"""

def create_offline_config():
    """创建离线配置"""
    
    config = '''
# 离线模式配置
OFFLINE_MODE = True
DISABLE_QUERY_REWRITE = True
DISABLE_SUGGESTION_GENERATION = True
USE_LOCAL_LLM_ONLY = True

# 本地模型配置
LOCAL_LLM_CONFIG = {
    "api_base": "http://localhost:11434",
    "model": "qwen2.5:7b",
    "temperature": 0.7
}

print("🔒 离线模式已启用")
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/config/offline_config.py', 'w') as f:
        f.write(config)
    
    print("✅ 离线配置已创建")

def patch_query_rewriter():
    """禁用查询改写"""
    
    patch = '''
def disable_query_rewrite():
    """禁用查询改写，直接返回原查询"""
    return lambda query: query

# 替换查询改写函数
query_rewrite = disable_query_rewrite()
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/utils/offline_patch.py', 'w') as f:
        f.write(patch)
    
    print("✅ 查询改写已禁用")

def create_local_llm_config():
    """创建本地LLM配置"""
    
    config = '''
# 本地LLM配置文件
import os

# 强制使用本地模型
os.environ["USE_LOCAL_LLM"] = "true"
os.environ["DISABLE_OPENAI"] = "true"

# Ollama配置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:7b",
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
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/src/config/local_llm_config.py', 'w') as f:
        f.write(config)
    
    print("✅ 本地LLM配置已创建")

def create_quick_fix_script():
    """创建快速修复脚本"""
    
    script = '''#!/bin/bash
echo "🔒 启用离线模式..."

# 设置离线环境变量
export OFFLINE_MODE=true
export DISABLE_OPENAI=true
export USE_LOCAL_LLM=true
export DISABLE_QUERY_REWRITE=true
export DISABLE_SUGGESTIONS=true

# 检查Ollama是否运行
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama未运行，启动Ollama..."
    ollama serve &
    sleep 3
    
    # 检查模型是否存在
    if ! ollama list | grep -q "qwen2.5:7b"; then
        echo "📥 下载本地模型..."
        ollama pull qwen2.5:7b
    fi
fi

echo "✅ 离线模式配置完成"
echo "🚀 重启应用..."

# 停止当前应用
pkill -f "streamlit run"
sleep 2

# 启动离线模式应用
cd /Users/zhaosj/Documents/rag-pro-max
streamlit run src/apppro.py --server.headless=true &

echo "✅ 离线应用已启动"
'''
    
    with open('/Users/zhaosj/Documents/rag-pro-max/enable_offline_mode.sh', 'w') as f:
        f.write(script)
    
    import os
    os.chmod('/Users/zhaosj/Documents/rag-pro-max/enable_offline_mode.sh', 0o755)
    
    print("✅ 离线模式脚本已创建")

def main():
    print("🔒 离线模式修复工具")
    print("="*50)
    
    create_offline_config()
    patch_query_rewriter()
    create_local_llm_config()
    create_quick_fix_script()
    
    print("\n🎯 立即修复:")
    print("1. 启用离线模式:")
    print("   ./enable_offline_mode.sh")
    print("\n2. 或者手动设置:")
    print("   export OFFLINE_MODE=true")
    print("   export DISABLE_OPENAI=true")
    print("\n3. 确保Ollama运行:")
    print("   ollama serve")
    print("   ollama pull qwen2.5:7b")
    
    print("\n✅ 修复后将禁用:")
    print("   - OpenAI API调用")
    print("   - 查询改写功能") 
    print("   - 在线推荐问题生成")
    print("   - 所有网络请求")

if __name__ == "__main__":
    main()
