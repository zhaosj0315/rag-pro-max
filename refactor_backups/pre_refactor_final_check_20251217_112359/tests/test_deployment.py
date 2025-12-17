"""
部署验证测试
验证跨平台部署的可行性
"""

import sys
import os
import platform
import subprocess

def test_python_version():
    """测试 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python 版本过低: {version.major}.{version.minor}.{version.micro} (需要 >= 3.8)")
        return False


def test_required_modules():
    """测试必需模块"""
    required = [
        'streamlit',
        'llama_index',
        'torch',
        'sentence_transformers',
    ]
    
    all_pass = True
    for module in required:
        try:
            __import__(module)
            print(f"✅ {module}: 已安装")
        except ImportError:
            print(f"❌ {module}: 未安装")
            all_pass = False
    
    return all_pass


def test_directories():
    """测试必要目录"""
    required_dirs = [
        'vector_db_storage',
        'chat_histories',
        'temp_uploads',
        'hf_cache',
        'app_logs',
        'suggestion_history',
    ]
    
    all_pass = True
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}: 存在")
        else:
            print(f"⚠️  {dir_name}: 不存在（将自动创建）")
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"   ✅ 已创建")
            except:
                print(f"   ❌ 创建失败")
                all_pass = False
    
    return all_pass


def test_scripts():
    """测试脚本文件"""
    scripts = {
        'Linux': 'scripts/deploy_linux.sh',
        'Windows': 'scripts/deploy_windows.bat',
        'Darwin': 'start.sh',  # macOS
    }
    
    system = platform.system()
    script = scripts.get(system)
    
    if script and os.path.exists(script):
        print(f"✅ {system} 部署脚本: {script}")
        return True
    else:
        print(f"⚠️  {system} 部署脚本: 未找到")
        return True  # 不是致命错误


def test_port_availability():
    """测试端口可用性"""
    import socket
    
    port = 8501
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result != 0:
        print(f"✅ 端口 {port}: 可用")
        return True
    else:
        print(f"⚠️  端口 {port}: 已被占用（可使用其他端口）")
        return True  # 不是致命错误


def test_platform_specific():
    """测试平台特定功能"""
    system = platform.system()
    print(f"✅ 操作系统: {system} {platform.release()}")
    
    if system == 'Linux':
        # 检查 tkinter
        try:
            import tkinter
            print("✅ tkinter: 已安装")
        except ImportError:
            print("⚠️  tkinter: 未安装（某些功能可能受限）")
    
    elif system == 'Windows':
        # 检查编码
        encoding = sys.getdefaultencoding()
        print(f"✅ 默认编码: {encoding}")
    
    return True


def main():
    print("\n" + "="*60)
    print("  RAG Pro Max 部署验证测试")
    print("="*60 + "\n")
    
    tests = [
        ("1. Python 版本", test_python_version),
        ("2. 必需模块", test_required_modules),
        ("3. 必要目录", test_directories),
        ("4. 部署脚本", test_scripts),
        ("5. 端口可用性", test_port_availability),
        ("6. 平台特定", test_platform_specific),
    ]
    
    results = []
    for name, test_func in tests:
        print("\n" + "="*60)
        print(f"  {name}")
        print("="*60)
        results.append(test_func())
    
    # 汇总
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ 部署验证通过！可以正常使用。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查并修复。")
        return 1


if __name__ == "__main__":
    exit(main())
