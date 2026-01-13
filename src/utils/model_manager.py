"""
模型管理模块 - 统一管理嵌入模型和 LLM 模型的加载
"""
import os
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from ..custom_embeddings import create_custom_embedding
from src.app_logging import LogManager
logger = LogManager()


def clean_proxy():
    """清理代理设置，避免本地服务连接问题"""
    for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if key in os.environ:
            del os.environ[key]


def load_embedding_model(provider: str, model_name: str, api_key: str = "", api_url: str = ""):
    """
    加载嵌入模型
    """
    # --- 核心底层补丁：强制拦截 Unknown 模型名 ---
    if not model_name or model_name == "Unknown":
        from src.core.app_config import load_config
        config = load_config()
        model_name = config.get('embed_model') or "sentence-transformers/all-MiniLM-L6-v2"
        provider = config.get('embed_provider') or "HuggingFace (本地/极速)"
        logger.warning(f"🛡️ 底层检测到损坏的模型请求(Unknown)，已强制纠正为系统默认: {model_name}")

    try:
        if provider.startswith("HuggingFace"):
            # HuggingFace 本地模型
            cache_dir = "./hf_cache"
            local_paths = [
                os.path.join(cache_dir, model_name.replace('/', '--')),
                model_name,
            ]
            
            local_model_path = None
            for path in local_paths:
                if os.path.exists(os.path.join(path, "config.json")):
                    local_model_path = path
                    break
            
            if not local_model_path:
                local_model_path = model_name
            
            logger.info("📥 正在加载模型...")
            
            # 前端用户提醒
            try:
                import streamlit as st
                model_status = st.empty()
                model_status.info(f"🤖 **模型加载**: 正在加载 {model_name}，请稍候...")
            except:
                model_status = None
            
            # 检测GPU支持
            device = "cpu"
            try:
                import torch
                
                # 清理环境变量
                for key in ['PYTORCH_MPS_HIGH_WATERMARK_RATIO', 'PYTORCH_MPS_LOW_WATERMARK_RATIO']:
                    if key in os.environ:
                        del os.environ[key]
                
                if torch.backends.mps.is_available():
                    device = "mps"
                    try:
                        torch.set_num_threads(10)
                        torch.set_num_interop_threads(3)
                    except:
                        pass
                    
                    os.environ['OMP_NUM_THREADS'] = '10'
                    os.environ['MKL_NUM_THREADS'] = '10'
                    logger.success("🚀 Apple M4 Max GPU (MPS) + CPU 加速已启用")
                    if model_status:
                        model_status.success("✅ **GPU加速**: Apple M4 Max GPU (MPS) 已启用")
                    
                elif torch.cuda.is_available():
                    device = "cuda"
                    try:
                        torch.set_num_threads(10)
                    except:
                        pass
                    torch.cuda.set_per_process_memory_fraction(0.9)
                    logger.success("✅ CUDA GPU + 多核CPU 加速已启用 (限制90%)")
                    
                else:
                    try:
                        torch.set_num_threads(10)
                    except:
                        pass
                    logger.warning("⚠️  未检测到GPU，使用 10核CPU 并行")
                    
            except Exception as e:
                device = "cpu"
                try:
                    import torch
                    torch.set_num_threads(12)
                except:
                    pass
                logger.error(f"❌ GPU检测异常: {e}，使用 CPU")
            
            # 动态计算batch_size
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            total_memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if device == "mps":
                usable_memory = available_memory_gb * 0.9
                if usable_memory > 20:
                    batch_size = 4096
                elif usable_memory > 10:
                    batch_size = 2048
                elif usable_memory > 5:
                    batch_size = 1024
                else:
                    batch_size = 512
                logger.info(f"🔥 M4 Max GPU: batch_size={batch_size}, 可用内存={usable_memory:.1f}GB (目标 GPU <90%)")
            elif device == "cuda":
                batch_size = min(4096, max(1024, int(available_memory_gb * 50)))
            else:
                batch_size = 64
            
            logger.info(f"动态batch_size: {batch_size} (总内存: {total_memory_gb:.1f}GB, 可用: {available_memory_gb:.1f}GB)")
            
            import torch
            torch.set_default_device(device)
            
            result = create_custom_embedding(
                model_name=local_model_path,
                cache_folder="./hf_cache",
                batch_size=batch_size,
                device=device
            )
            logger.success("✅ 模型加载成功")
            return result
            
        elif provider.startswith("Ollama"):
            clean_proxy()
            logger.success("✅ 模型加载成功")
            return OllamaEmbedding(model_name=model_name, base_url=api_url)
            
        elif provider.startswith("OpenAI"):
            logger.success("✅ 模型加载成功")
            return OpenAIEmbedding(model=model_name, api_key=api_key, api_base=api_url)
            
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {str(e)[:200]}")
        
    return None


def load_llm_model(provider: str, model_name: str, api_key: str = "", api_url: str = "", temperature: float = 0.7, system_prompt: str = None, **kwargs):
    """
    加载 LLM 模型
    
    Args:
        provider: 供应商 (Ollama/OpenAI/Azure OpenAI/Anthropic/Gemini/Moonshot/Groq)
        model_name: 模型名称
        api_key: API密钥
        api_url: API地址 (Base URL 或 Endpoint)
        temperature: 温度参数
        system_prompt: 系统提示词
        **kwargs: 其他参数 (如 api_version)
    
    Returns:
        LLM 模型实例，失败返回 None
    """
    try:
        # 1. Ollama
        if provider.startswith("Ollama"):
            clean_proxy()
            base_url = api_url.rstrip('/')
            if base_url.endswith('/api'):
                base_url = base_url[:-4]
            
            return Ollama(
                model=model_name,
                base_url=base_url,
                request_timeout=1200.0,
                temperature=temperature,
                system_prompt=system_prompt
            )
            
        # 2. OpenAI / Moonshot / Groq (OpenAI-Compatible)
        elif provider in ["OpenAI", "Moonshot", "Groq"] or provider.startswith("OpenAI-Compatible"):
            # Monkey-patch: 注册自定义模型以绕过 LlamaIndex 的严格验证
            try:
                import llama_index.llms.openai.utils as openai_utils
                
                # 注册上下文窗口大小 (默认 128k)
                if hasattr(openai_utils, 'openai_modelname_to_contextsize'):
                    # 检查是否为字典，某些版本可能是函数
                    if isinstance(openai_utils.openai_modelname_to_contextsize, dict):
                        if model_name not in openai_utils.openai_modelname_to_contextsize:
                            openai_utils.openai_modelname_to_contextsize[model_name] = 128000
                
                # 注册到可用模型列表
                if hasattr(openai_utils, 'ALL_AVAILABLE_MODELS'):
                    # 检查是否为 Set，如果是则 add，否则 append
                    if isinstance(openai_utils.ALL_AVAILABLE_MODELS, set):
                        openai_utils.ALL_AVAILABLE_MODELS.add(model_name)
                    elif isinstance(openai_utils.ALL_AVAILABLE_MODELS, list):
                        if model_name not in openai_utils.ALL_AVAILABLE_MODELS:
                            openai_utils.ALL_AVAILABLE_MODELS.append(model_name)
                            
                # 注册到聊天模型列表 (关键验证点)
                if hasattr(openai_utils, 'CHAT_MODELS'):
                    if isinstance(openai_utils.CHAT_MODELS, dict):
                        openai_utils.CHAT_MODELS[model_name] = 128000
                    elif isinstance(openai_utils.CHAT_MODELS, set):
                        openai_utils.CHAT_MODELS.add(model_name)
                    elif isinstance(openai_utils.CHAT_MODELS, list):
                         if model_name not in openai_utils.CHAT_MODELS:
                            openai_utils.CHAT_MODELS.append(model_name)
                            
            except Exception as e:
                logger.warning(f"⚠️ 注册自定义模型失败 (可能导致验证错误): {e}")

            return OpenAI(
                model=model_name,
                api_key=api_key if api_key else "EMPTY",
                api_base=api_url,
                temperature=temperature,
                request_timeout=1200.0,
                system_prompt=system_prompt
            )
            
        # 3. Azure OpenAI
        elif provider == "Azure OpenAI":
            try:
                from llama_index.llms.azure_openai import AzureOpenAI
                return AzureOpenAI(
                    engine=model_name,  # Deployment name
                    model=model_name,
                    api_key=api_key,
                    azure_endpoint=api_url,
                    api_version=kwargs.get("api_version", "2023-05-15"),
                    temperature=temperature,
                    system_prompt=system_prompt
                )
            except ImportError:
                logger.error("❌ 未安装 Azure 支持: pip install llama-index-llms-azure-openai")
                return None
                
        # 4. Anthropic (Claude)
        elif provider == "Anthropic":
            try:
                from llama_index.llms.anthropic import Anthropic
                return Anthropic(
                    model=model_name,
                    api_key=api_key,
                    temperature=temperature,
                    system_prompt=system_prompt
                )
            except ImportError:
                logger.error("❌ 未安装 Anthropic 支持: pip install llama-index-llms-anthropic")
                return None
                
        # 5. Gemini (Google)
        elif provider == "Gemini":
            try:
                from llama_index.llms.gemini import Gemini
                # Gemini 通常需要 models/ 前缀
                if not model_name.startswith("models/"):
                    model_name = f"models/{model_name}"
                return Gemini(
                    model=model_name,
                    api_key=api_key,
                    temperature=temperature,
                    system_prompt=system_prompt
                )
            except ImportError:
                logger.error("❌ 未安装 Gemini 支持: pip install llama-index-llms-gemini")
                return None
            
    except Exception as e:
        logger.error(f"LLM 加载失败 ({provider}): {e}")
        
    return None


def set_global_embedding_model(provider: str, model_name: str, api_key: str = "", api_url: str = ""):
    """
    设置全局嵌入模型（Settings.embed_model）
    
    Returns:
        bool: 是否设置成功
    """
    embed_model = load_embedding_model(provider, model_name, api_key, api_url)
    if embed_model:
        Settings.embed_model = embed_model
        try:
            dim = len(embed_model._get_text_embedding("test"))
            logger.success(f"✅ 全局嵌入模型已设置: {model_name} ({dim}维)")
        except:
            logger.success(f"✅ 全局嵌入模型已设置: {model_name}")
        return True
    else:
        logger.error(f"❌ 全局嵌入模型设置失败: {model_name}")
        return False


def set_global_llm_model(provider: str, model_name: str, api_key: str = "", api_url: str = "", temperature: float = 0.7, system_prompt: str = None, **kwargs):
    """
    设置全局 LLM 模型（Settings.llm）
    
    Returns:
        bool: 是否设置成功
    """
    llm_model = load_llm_model(provider, model_name, api_key, api_url, temperature, system_prompt=system_prompt, **kwargs)
    if llm_model:
        Settings.llm = llm_model
        logger.success(f"✅ 全局 LLM 已设置: {model_name} ({provider})")
        return True
    else:
        logger.error(f"❌ 全局 LLM 设置失败: {model_name}")
        return False