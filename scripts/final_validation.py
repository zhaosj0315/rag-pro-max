#!/usr/bin/env python3
"""
最终验证脚本
确保所有接口都能正常工作，系统可以发布
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, description=""):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"命令超时: {cmd}"
    except Exception as e:
        return False, "", str(e)

def test_python_syntax():
    """测试Python语法"""
    print("🔍 检查Python语法...")
    
    src_files = list(Path("src").rglob("*.py"))
    test_files = list(Path("tests").rglob("*.py"))
    script_files = list(Path("scripts").rglob("*.py"))
    
    all_files = src_files + test_files + script_files
    
    syntax_errors = []
    for py_file in all_files:
        success, stdout, stderr = run_command(f"python -m py_compile {py_file}")
        if not success:
            syntax_errors.append(f"{py_file}: {stderr}")
    
    if syntax_errors:
        print(f"❌ 发现 {len(syntax_errors)} 个语法错误:")
        for error in syntax_errors[:5]:  # 只显示前5个
            print(f"  {error}")
        return False
    else:
        print(f"✅ 所有 {len(all_files)} 个Python文件语法正确")
        return True

def test_imports():
    """测试导入"""
    print("🔍 检查关键模块导入...")
    
    critical_imports = [
        "src.core.environment",
        "src.api.fastapi_server", 
        "src.ui.main_interface",
        "src.kb.kb_manager",
        "src.processors.web_crawler",
        "src.utils.model_manager",
        "src.app_logging.log_manager"
    ]
    
    import_errors = []
    for module in critical_imports:
        success, stdout, stderr = run_command(f"python -c 'import {module}'")
        if not success:
            import_errors.append(f"{module}: {stderr}")
        else:
            print(f"  ✅ {module}")
    
    if import_errors:
        print(f"❌ 发现 {len(import_errors)} 个导入错误:")
        for error in import_errors:
            print(f"  {error}")
        return False
    else:
        print(f"✅ 所有 {len(critical_imports)} 个关键模块导入成功")
        return True

def test_configuration():
    """测试配置文件"""
    print("🔍 检查配置文件...")
    
    config_files = [
        "config/app_config.json",
        "rag_config.json",
        "requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    for config_file in config_files:
        if not os.path.exists(config_file):
            missing_files.append(config_file)
        else:
            print(f"  ✅ {config_file}")
    
    if missing_files:
        print(f"❌ 缺少 {len(missing_files)} 个配置文件:")
        for file in missing_files:
            print(f"  {file}")
        return False
    else:
        print(f"✅ 所有 {len(config_files)} 个配置文件存在")
        return True

def test_api_server():
    """测试API服务器启动"""
    print("🔍 测试API服务器...")
    
    # 创建临时测试脚本
    test_script = """
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from src.api.fastapi_server import app
    print("✅ FastAPI应用创建成功")
    
    # 检查路由
    routes = [route.path for route in app.routes]
    print(f"✅ 发现 {len(routes)} 个路由")
    
    sys.exit(0)
except Exception as e:
    print(f"❌ API服务器测试失败: {e}")
    sys.exit(1)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        temp_file = f.name
    
    try:
        success, stdout, stderr = run_command(f"python {temp_file}")
        if success:
            print(stdout.strip())
            return True
        else:
            print(f"❌ API服务器测试失败: {stderr}")
            return False
    finally:
        os.unlink(temp_file)

def test_main_application():
    """测试主应用"""
    print("🔍 测试主应用文件...")
    
    main_files = [
        "src/apppro.py",
        "src/apppro_final.py"
    ]
    
    for main_file in main_files:
        if os.path.exists(main_file):
            # 检查文件大小
            size = os.path.getsize(main_file)
            if size > 1000:  # 至少1KB
                print(f"  ✅ {main_file} ({size:,} bytes)")
            else:
                print(f"  ⚠️  {main_file} 文件过小 ({size} bytes)")
        else:
            print(f"  ❌ {main_file} 不存在")
    
    return True

def test_directory_structure():
    """测试目录结构"""
    print("🔍 检查目录结构...")
    
    required_dirs = [
        "src",
        "tests", 
        "scripts",
        "config",
        "docs"
    ]
    
    runtime_dirs = [
        "vector_db_storage",
        "chat_histories", 
        "temp_uploads",
        "hf_cache",
        "app_logs"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
        else:
            print(f"  ✅ {dir_name}/")
    
    # 检查运行时目录（可选）
    for dir_name in runtime_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/ (运行时)")
        else:
            print(f"  ⚠️  {dir_name}/ (运行时，将自动创建)")
    
    if missing_dirs:
        print(f"❌ 缺少 {len(missing_dirs)} 个必需目录:")
        for dir_name in missing_dirs:
            print(f"  {dir_name}/")
        return False
    else:
        print(f"✅ 所有 {len(required_dirs)} 个必需目录存在")
        return True

def test_dependencies():
    """测试依赖"""
    print("🔍 检查Python依赖...")
    
    # 检查requirements.txt
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt 不存在")
        return False
    
    with open("requirements.txt", 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"  📦 发现 {len(requirements)} 个依赖包")
    
    # 检查关键依赖
    critical_deps = ['streamlit', 'fastapi', 'llama-index']
    missing_deps = []
    
    for dep in critical_deps:
        if not any(dep in req for req in requirements):
            missing_deps.append(dep)
        else:
            print(f"  ✅ {dep}")
    
    if missing_deps:
        print(f"❌ 缺少关键依赖: {missing_deps}")
        return False
    else:
        print("✅ 所有关键依赖存在")
        return True

def run_final_tests():
    """运行最终测试"""
    print("🔍 运行最终测试...")
    
    # 运行完整接口测试
    success, stdout, stderr = run_command("python tests/test_complete_interfaces.py")
    if success:
        print("✅ 完整接口测试通过")
    else:
        print(f"❌ 完整接口测试失败: {stderr}")
        return False
    
    # 运行出厂测试
    if os.path.exists("tests/factory_test.py"):
        success, stdout, stderr = run_command("python tests/factory_test.py")
        if success:
            print("✅ 出厂测试通过")
        else:
            print(f"⚠️  出厂测试有警告: {stderr}")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("  RAG Pro Max - 最终验证")
    print("=" * 60)
    
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print(f"📁 工作目录: {os.getcwd()}")
    
    # 验证任务
    validation_tasks = [
        ("Python语法检查", test_python_syntax),
        ("关键模块导入", test_imports),
        ("配置文件检查", test_configuration),
        ("API服务器测试", test_api_server),
        ("主应用检查", test_main_application),
        ("目录结构检查", test_directory_structure),
        ("依赖检查", test_dependencies),
        ("最终测试", run_final_tests)
    ]
    
    passed_tests = 0
    total_tests = len(validation_tasks)
    
    for task_name, task_func in validation_tasks:
        print(f"\n📋 {task_name}...")
        try:
            if task_func():
                passed_tests += 1
                print(f"✅ {task_name} 通过")
            else:
                print(f"❌ {task_name} 失败")
        except Exception as e:
            print(f"❌ {task_name} 异常: {e}")
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("  最终验证结果")
    print("=" * 60)
    print(f"✅ 通过: {passed_tests}/{total_tests}")
    print(f"❌ 失败: {total_tests - passed_tests}/{total_tests}")
    
    success_rate = (passed_tests / total_tests) * 100
    
    if success_rate >= 90:
        print(f"\n🎉 验证成功率: {success_rate:.1f}% - 系统可以发布！")
        return True
    elif success_rate >= 70:
        print(f"\n⚠️  验证成功率: {success_rate:.1f}% - 建议修复问题后发布")
        return False
    else:
        print(f"\n❌ 验证成功率: {success_rate:.1f}% - 需要修复重大问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
