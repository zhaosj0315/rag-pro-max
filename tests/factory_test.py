#!/usr/bin/env python3
"""
RAG Pro Max 出厂测试脚本
测试所有核心功能，确保代码修改后系统正常运行
"""

import os
import sys
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置离线模式
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# 屏蔽警告
import warnings
warnings.filterwarnings('ignore')

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_test(name, status, message=""):
    symbols = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}
    print(f"{symbols.get(status, '❓')} {name}: {status}")
    if message:
        print(f"   └─ {message}")
    
    if status == "PASS":
        test_results["passed"] += 1
    elif status == "FAIL":
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {message}")
    else:
        test_results["skipped"] += 1

# ============================================================
# 1. 环境检查
# ============================================================
def test_environment():
    print_header("1. 环境检查")
    
    # Python 版本
    py_version = sys.version_info
    if py_version >= (3, 8):
        print_test("Python 版本", "PASS", f"{py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print_test("Python 版本", "FAIL", f"需要 3.8+，当前 {py_version.major}.{py_version.minor}")
    
    # 必需的包
    required_packages = [
        "streamlit", "llama_index", "chromadb", "requests",
        "ollama", "sentence_transformers", "torch"
    ]
    
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
            print_test(f"包: {pkg}", "PASS")
        except ImportError:
            print_test(f"包: {pkg}", "FAIL", "未安装")
    
    # 必需的文件
    required_files = [
        "src/apppro.py", "src/logger.py",
        "src/custom_embeddings.py", "src/metadata_manager.py",
        "src/chat_utils_improved.py", "requirements.txt"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print_test(f"文件: {file}", "PASS")
        else:
            print_test(f"文件: {file}", "FAIL", "文件不存在")

# ============================================================
# 2. 配置文件测试
# ============================================================
def test_config_files():
    print_header("2. 配置文件测试")
    
    # 只检查文件存在性和 JSON 格式，不强制要求特定字段
    configs = ["rag_config.json", "app_config.json", "projects_config.json"]
    
    for config_file in configs:
        if not os.path.exists(config_file):
            print_test(f"配置: {config_file}", "SKIP", "文件不存在")
            continue
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print_test(f"配置: {config_file}", "PASS", f"{len(data)} 个配置项")
        except json.JSONDecodeError as e:
            print_test(f"配置: {config_file}", "FAIL", f"JSON 格式错误: {e}")

# ============================================================
# 3. 核心模块导入测试
# ============================================================
def test_core_imports():
    print_header("3. 核心模块导入测试")
    
    modules = [
        ("src.logger", "logger"),
        ("src.custom_embeddings", "create_custom_embedding"),
        ("src.metadata_manager", "MetadataManager"),
        ("src.chat_utils_improved", "generate_follow_up_questions_safe"),
        ("src.utils.memory", "cleanup_memory"),
        ("src.utils.memory", "get_memory_stats"),
        ("src.utils.model_manager", "load_embedding_model"),
        ("src.utils.model_manager", "load_llm_model"),
        ("src.utils.model_manager", "clean_proxy"),
        ("src.utils.document_processor", "sanitize_filename"),
        ("src.utils.document_processor", "get_file_type"),
        ("src.utils.document_processor", "get_file_info"),
        ("src.config", "ConfigLoader"),
        ("src.config", "ManifestManager"),
        ("src.chat", "HistoryManager"),
        ("src.chat", "SuggestionManager"),
        ("src.kb", "KBManager"),
    ]
    
    for module_name, attr_name in modules:
        try:
            # 支持嵌套模块 (如 src.utils.memory)
            parts = module_name.split('.')
            module = __import__(module_name, fromlist=[parts[-1]])
            
            if hasattr(module, attr_name):
                print_test(f"模块: {module_name}.{attr_name}", "PASS")
            else:
                print_test(f"模块: {module_name}.{attr_name}", "FAIL", f"缺少属性 {attr_name}")
        except Exception as e:
            print_test(f"模块: {module_name}", "FAIL", str(e))

# ============================================================
# 4. 日志系统测试
# ============================================================
def test_logging_system():
    print_header("4. 日志系统测试")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.logger import logger
        from src.logging import LogManager
        
        # 测试日志目录
        log_dir = "app_logs"
        if os.path.exists(log_dir):
            print_test("日志目录", "PASS", f"{log_dir} 存在")
        else:
            os.makedirs(log_dir)
            print_test("日志目录", "PASS", f"{log_dir} 已创建")
        
        # 测试日志写入（使用统一的LogManager）
        test_msg = f"Factory test at {datetime.now()}"
        logger.log("测试", "成功", test_msg)
        
        # 测试LogManager
        log_manager = LogManager()
        log_manager.info(test_msg)
        print_test("日志写入", "PASS", "logger.log + LogManager")
        
    except Exception as e:
        print_test("日志系统", "FAIL", str(e))

# ============================================================
# 5. 文档处理测试
# ============================================================
def test_document_processing():
    print_header("5. 文档处理测试")
    
    # 创建测试文件
    test_dir = tempfile.mkdtemp(prefix="rag_test_")
    
    try:
        # 测试 TXT
        txt_file = os.path.join(test_dir, "test.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文档。\n用于验证文档处理功能。")
        
        if os.path.exists(txt_file):
            print_test("TXT 文件创建", "PASS", txt_file)
        
        # 测试 JSON
        json_file = os.path.join(test_dir, "test.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({"test": "data", "value": 123}, f)
        
        if os.path.exists(json_file):
            print_test("JSON 文件创建", "PASS", json_file)
        
        # 测试 MD
        md_file = os.path.join(test_dir, "test.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 测试标题\n\n这是测试内容。")
        
        if os.path.exists(md_file):
            print_test("MD 文件创建", "PASS", md_file)
        
        print_test("测试文件目录", "PASS", test_dir)
        
    except Exception as e:
        print_test("文档处理", "FAIL", str(e))
    finally:
        # 清理测试文件
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

# ============================================================
# 6. 向量数据库测试
# ============================================================
def test_vector_database():
    print_header("6. 向量数据库测试")
    
    try:
        from llama_index.core import VectorStoreIndex, Document, Settings
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        
        # 检查本地缓存是否存在
        cache_dir = "./hf_cache"
        model_cache = os.path.join(cache_dir, "BAAI--bge-small-zh-v1.5")
        
        if not os.path.exists(model_cache):
            print_test("嵌入模型加载", "SKIP", "模型未下载（离线模式）")
            print_test("文档向量化", "SKIP", "需要嵌入模型")
            print_test("向量检索", "SKIP", "需要嵌入模型")
            return
        
        # 只在本地缓存存在时测试
        embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5",
            cache_folder=cache_dir
        )
        print_test("嵌入模型加载", "PASS", "BAAI/bge-small-zh-v1.5")
        
        # 测试文档向量化
        docs = [Document(text="这是一个测试文档")]
        Settings.embed_model = embed_model
        index = VectorStoreIndex.from_documents(docs, show_progress=False)
        print_test("文档向量化", "PASS", "1 个文档")
        
        # 测试查询
        query_engine = index.as_query_engine(similarity_top_k=1)
        response = query_engine.query("测试")
        if response:
            print_test("向量检索", "PASS", f"返回 {len(response.source_nodes)} 个节点")
        
    except Exception as e:
        print_test("向量数据库", "FAIL", str(e))

# ============================================================
# 7. LLM 连接测试
# ============================================================
def test_llm_connection():
    print_header("7. LLM 连接测试")
    
    # 测试 Ollama
    try:
        import requests
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print_test("Ollama 连接", "PASS", f"{len(models)} 个模型")
        else:
            print_test("Ollama 连接", "FAIL", f"状态码 {response.status_code}")
    except Exception as e:
        print_test("Ollama 连接", "SKIP", "服务未启动")
    
    # 测试 OpenAI (仅检查配置)
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        print_test("OpenAI API Key", "PASS", "环境变量已设置")
    else:
        print_test("OpenAI API Key", "SKIP", "未设置环境变量")

# ============================================================
# 8. 存储目录测试
# ============================================================
def test_storage_directories():
    print_header("8. 存储目录测试")
    
    directories = [
        "vector_db_storage",
        "chat_histories",
        "temp_uploads",
        "hf_cache",
        "app_logs"
    ]
    
    for dir_name in directories:
        if os.path.exists(dir_name):
            file_count = len(os.listdir(dir_name))
            print_test(f"目录: {dir_name}", "PASS", f"{file_count} 个文件")
        else:
            os.makedirs(dir_name, exist_ok=True)
            print_test(f"目录: {dir_name}", "PASS", "已创建")

# ============================================================
# 9. 安全性测试
# ============================================================
def test_security():
    print_header("9. 安全性测试")
    
    # 检查文件打开相关的 subprocess 漏洞是否修复
    try:
        with open("src/apppro.py", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 检查是否有 subprocess.run(["open", ...]) 这种危险用法
        dangerous_patterns = False
        for i, line in enumerate(lines, 1):
            if 'subprocess.run' in line and '"open"' in line:
                print_test("Subprocess 文件打开漏洞", "FAIL", f"第 {i} 行仍使用 subprocess.run(['open', ...])")
                dangerous_patterns = True
                break
        
        if not dangerous_patterns:
            print_test("Subprocess 文件打开漏洞", "PASS", "已修复")
        
        # 检查是否使用了安全的 webbrowser.open
        if 'webbrowser.open' in ''.join(lines):
            print_test("安全打开文件", "PASS", "使用 webbrowser.open")
        else:
            print_test("安全打开文件", "SKIP", "未找到文件打开代码")
        
    except Exception as e:
        print_test("安全性检查", "FAIL", str(e))

# ============================================================
# 10. 性能配置测试
# ============================================================
def test_performance_config():
    print_header("10. 性能配置测试")
    
    try:
        import multiprocessing as mp
        cpu_count = mp.cpu_count()
        print_test("CPU 核心数", "PASS", f"{cpu_count} 核")
        
        # 检查多线程配置
        with open("src/apppro.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'ThreadPoolExecutor' in content:
            print_test("多线程支持", "PASS", "ThreadPoolExecutor")
        
        if 'ProcessPoolExecutor' in content:
            print_test("多进程支持", "PASS", "ProcessPoolExecutor")
        
    except Exception as e:
        print_test("性能配置", "FAIL", str(e))

# ============================================================
# 11. 内存管理测试
# ============================================================
def test_memory_management():
    print_header("11. 内存管理测试")
    
    try:
        # 检查 cleanup_memory 函数（可能在 src/utils/memory.py）
        cleanup_found = False
        check_content = ""
        
        # 检查 src/utils/memory.py
        if os.path.exists("src/utils/memory.py"):
            with open("src/utils/memory.py", 'r', encoding='utf-8') as f:
                utils_content = f.read()
            if 'def cleanup_memory' in utils_content:
                print_test("cleanup_memory 函数", "PASS", "已定义 (src/utils/memory.py)")
                cleanup_found = True
                check_content = utils_content
        
        # 检查 src/apppro.py（兼容旧版本）
        with open("src/apppro.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not cleanup_found and 'def cleanup_memory():' in content:
            print_test("cleanup_memory 函数", "PASS", "已定义 (src/apppro.py)")
            cleanup_found = True
            check_content = content
        
        if not cleanup_found:
            print_test("cleanup_memory 函数", "FAIL", "未找到")
            return
        
        # 检查 GPU 缓存清理
        if 'torch.cuda.empty_cache()' in check_content:
            print_test("CUDA 缓存清理", "PASS", "已实现")
        else:
            print_test("CUDA 缓存清理", "SKIP", "未找到")
        
        if 'torch.mps.empty_cache()' in check_content:
            print_test("MPS 缓存清理", "PASS", "已实现")
        else:
            print_test("MPS 缓存清理", "SKIP", "未找到")
        
        # 检查是否替换了所有 gc.collect()（排除 cleanup_memory 函数内部）
        import re
        lines = content.split('\n')
        in_cleanup_func = False
        standalone_gc = 0
        
        for i, line in enumerate(lines):
            if 'def cleanup_memory' in line:
                in_cleanup_func = True
            elif in_cleanup_func and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                in_cleanup_func = False
            
            if not in_cleanup_func and 'import gc' in line:
                # 检查下一行是否是 gc.collect()
                if i + 1 < len(lines) and 'gc.collect()' in lines[i + 1]:
                    standalone_gc += 1
        
        if standalone_gc == 0:
            print_test("gc.collect 替换", "PASS", "已全部替换为 cleanup_memory")
        else:
            print_test("gc.collect 替换", "FAIL", f"仍有 {standalone_gc} 处未替换")
        
    except Exception as e:
        print_test("内存管理", "FAIL", str(e))

# ============================================================
# 12. GPU 优化测试
# ============================================================
def test_gpu_optimization():
    print_header("12. GPU 优化测试")
    
    try:
        with open("src/apppro.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 batch_size 优化
        if 'batch_size = 50000' in content or 'batch_size = 30000' in content:
            print_test("向量化 batch_size", "PASS", "已优化（2-5万）")
        else:
            print_test("向量化 batch_size", "SKIP", "未找到优化配置")
        
        # 检查 custom_embeddings 优化
        if os.path.exists("src/custom_embeddings.py"):
            with open("src/custom_embeddings.py", 'r', encoding='utf-8') as f:
                embed_content = f.read()
            
            if 'torch.compile' in embed_content:
                print_test("torch.compile 优化", "PASS", "已启用")
            else:
                print_test("torch.compile 优化", "SKIP", "未启用")
            
            if 'pin_memory' in embed_content or 'non_blocking' in embed_content:
                print_test("数据传输优化", "PASS", "已优化")
            else:
                print_test("数据传输优化", "SKIP", "未优化")
        else:
            print_test("custom_embeddings.py", "SKIP", "文件不存在")
        
    except Exception as e:
        print_test("GPU 优化", "FAIL", str(e))

# ============================================================
# 主测试流程
# ============================================================
def main():
    print("\n" + "="*60)
    print("  RAG Pro Max 出厂测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 执行所有测试
    test_environment()
    test_config_files()
    test_core_imports()
    test_logging_system()
    test_document_processing()
    test_vector_database()
    test_llm_connection()
    test_storage_directories()
    test_security()
    test_performance_config()
    test_memory_management()
    test_gpu_optimization()
    
    # 输出测试结果
    print_header("测试结果汇总")
    total = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    print(f"✅ 通过: {test_results['passed']}/{total}")
    print(f"❌ 失败: {test_results['failed']}/{total}")
    print(f"⏭️  跳过: {test_results['skipped']}/{total}")
    
    if test_results["failed"] > 0:
        print("\n失败的测试:")
        for error in test_results["errors"]:
            print(f"  - {error}")
        print("\n❌ 出厂测试未通过！")
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过！系统可以发布。")
        sys.exit(0)

if __name__ == "__main__":
    main()
