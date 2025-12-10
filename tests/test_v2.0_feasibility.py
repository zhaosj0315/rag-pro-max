"""
RAG Pro Max v2.0 可行性测试
测试增量更新、多模态支持、API扩展等新功能
"""

import os
import sys
import tempfile
import shutil
import json
from datetime import datetime

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def print_test(name, status, details=""):
    """打印测试结果"""
    status_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}
    print(f"{status_icon.get(status, '❓')} {name}: {status}")
    if details:
        print(f"   └─ {details}")

def print_header(title):
    """打印测试分组标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("="*60)

def test_incremental_update():
    """测试增量更新功能"""
    print_header("增量更新功能测试")
    
    try:
        from src.kb.incremental_updater import IncrementalUpdater
        print_test("增量更新模块导入", "PASS", "IncrementalUpdater")
        
        # 创建临时测试环境
        temp_dir = tempfile.mkdtemp()
        updater = IncrementalUpdater(temp_dir)
        
        # 测试1: 文件哈希计算
        test_file = os.path.join(temp_dir, "test_doc.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文档内容")
        
        hash1 = updater._calculate_file_hash(test_file)
        hash2 = updater._calculate_file_hash(test_file)
        
        if hash1 == hash2 and len(hash1) == 32:
            print_test("文件哈希一致性", "PASS", f"MD5: {hash1[:8]}...")
        else:
            print_test("文件哈希一致性", "FAIL", "哈希值不一致或格式错误")
        
        # 测试2: 新文件检测
        changes = updater.get_changed_files([test_file])
        if test_file in changes['new']:
            print_test("新文件检测", "PASS", "正确识别新文件")
        else:
            print_test("新文件检测", "FAIL", f"检测结果: {changes}")
        
        # 测试3: 文件标记和状态保持
        updater.mark_files_processed([test_file])
        changes_after = updater.get_changed_files([test_file])
        
        if test_file in changes_after['unchanged']:
            print_test("文件状态保持", "PASS", "已处理文件正确标记")
        else:
            print_test("文件状态保持", "FAIL", f"状态: {changes_after}")
        
        # 测试4: 文件修改检测
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("修改后的文档内容")
        
        changes_modified = updater.get_changed_files([test_file])
        if test_file in changes_modified['modified']:
            print_test("文件修改检测", "PASS", "正确检测文件修改")
        else:
            print_test("文件修改检测", "FAIL", f"检测结果: {changes_modified}")
        
        # 测试5: 元数据持久化
        new_updater = IncrementalUpdater(temp_dir)
        loaded_changes = new_updater.get_changed_files([test_file])
        
        if test_file in loaded_changes['modified']:
            print_test("元数据持久化", "PASS", "元数据正确加载")
        else:
            print_test("元数据持久化", "FAIL", "元数据加载失败")
        
        # 测试6: 统计信息
        stats = updater.get_stats()
        if 'total_files' in stats and 'last_update' in stats:
            print_test("统计信息", "PASS", f"跟踪 {stats['total_files']} 个文件")
        else:
            print_test("统计信息", "FAIL", "统计信息不完整")
        
        # 清理
        shutil.rmtree(temp_dir)
        
    except ImportError:
        print_test("增量更新模块", "SKIP", "模块不存在（v1.8版本）")
    except Exception as e:
        print_test("增量更新功能", "FAIL", str(e))

def test_multimodal_support():
    """测试多模态支持功能"""
    print_header("多模态支持功能测试")
    
    try:
        from src.processors.multimodal_processor import MultimodalProcessor
        print_test("多模态处理器导入", "PASS", "MultimodalProcessor")
        
        processor = MultimodalProcessor()
        
        # 测试1: 文件类型检测
        test_cases = [
            ('document.pdf', 'pdf_multimodal'),
            ('image.jpg', 'image'),
            ('image.png', 'image'),
            ('table.xlsx', 'table'),
            ('data.csv', 'table'),
            ('text.txt', 'text')
        ]
        
        detection_results = []
        for filename, expected in test_cases:
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as f:
                detected = processor.detect_file_type(f.name)
                detection_results.append((filename, expected, detected))
                os.unlink(f.name)
        
        correct_detections = sum(1 for _, expected, detected in detection_results if expected == detected)
        total_detections = len(detection_results)
        
        if correct_detections == total_detections:
            print_test("文件类型检测", "PASS", f"{correct_detections}/{total_detections} 正确")
        else:
            print_test("文件类型检测", "FAIL", f"只有 {correct_detections}/{total_detections} 正确")
            for filename, expected, detected in detection_results:
                if expected != detected:
                    print(f"      {filename}: 期望 {expected}, 实际 {detected}")
        
        # 测试2: 支持格式查询
        formats = processor.get_supported_formats()
        required_keys = ['images', 'tables', 'ocr_available', 'table_extraction_available']
        
        if all(key in formats for key in required_keys):
            print_test("支持格式查询", "PASS", 
                      f"图片: {len(formats['images'])}种, 表格: {len(formats['tables'])}种")
        else:
            print_test("支持格式查询", "FAIL", "格式信息不完整")
        
        # 测试3: OCR功能检查
        if formats['ocr_available']:
            print_test("OCR功能", "PASS", "Tesseract OCR 可用")
        else:
            print_test("OCR功能", "SKIP", "Tesseract OCR 不可用")
        
        # 测试4: 表格提取功能检查
        if formats['table_extraction_available']:
            print_test("表格提取功能", "PASS", "Pandas + Tabula 可用")
        else:
            print_test("表格提取功能", "SKIP", "表格提取库不可用")
        
        # 测试5: 多模态文件处理
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content for multimodal processing")
            temp_path = f.name
        
        try:
            result = processor.process_multimodal_file(temp_path)
            required_fields = ['file_path', 'file_type', 'text_content', 'images', 'tables', 'metadata']
            
            if all(field in result for field in required_fields):
                print_test("多模态文件处理", "PASS", f"文件类型: {result['file_type']}")
            else:
                print_test("多模态文件处理", "FAIL", "返回结果不完整")
        finally:
            os.unlink(temp_path)
        
    except ImportError:
        print_test("多模态处理器", "SKIP", "模块不存在（v1.8版本）")
    except Exception as e:
        print_test("多模态支持功能", "FAIL", str(e))

def test_api_extensions():
    """测试API扩展功能"""
    print_header("API扩展功能测试")
    
    try:
        from src.api.fastapi_server import app
        print_test("FastAPI应用导入", "PASS", "app")
        
        # 测试1: API版本检查
        if hasattr(app, 'version') and app.version == "2.0.0":
            print_test("API版本", "PASS", f"v{app.version}")
        else:
            print_test("API版本", "FAIL", f"版本: {getattr(app, 'version', 'unknown')}")
        
        # 测试2: v2.0路由检查
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        v2_routes = [
            '/incremental-update',
            '/upload-multimodal', 
            '/query-multimodal',
            '/multimodal/formats'
        ]
        
        found_routes = [route for route in v2_routes if route in routes]
        
        if len(found_routes) == len(v2_routes):
            print_test("v2.0 API路由", "PASS", f"发现所有 {len(v2_routes)} 个新路由")
        else:
            print_test("v2.0 API路由", "FAIL", f"只发现 {len(found_routes)}/{len(v2_routes)} 个路由")
            print(f"      缺失: {set(v2_routes) - set(found_routes)}")
        
        # 测试3: 数据模型检查
        try:
            from src.api.fastapi_server import IncrementalUpdateRequest, MultimodalQueryRequest
            print_test("v2.0 数据模型", "PASS", "IncrementalUpdateRequest, MultimodalQueryRequest")
        except ImportError:
            print_test("v2.0 数据模型", "FAIL", "数据模型导入失败")
        
        # 测试4: 管理器初始化
        try:
            from src.api.fastapi_server import kb_manager, multimodal_processor
            print_test("管理器初始化", "PASS", "kb_manager, multimodal_processor")
        except ImportError:
            print_test("管理器初始化", "FAIL", "管理器导入失败")
        
    except ImportError:
        print_test("FastAPI应用", "SKIP", "API模块不存在")
    except Exception as e:
        print_test("API扩展功能", "FAIL", str(e))

def test_integration():
    """测试v2.0集成功能"""
    print_header("v2.0集成功能测试")
    
    try:
        from src.core.v2_integration import V2Integration
        print_test("v2.0集成模块导入", "PASS", "V2Integration")
        
        # 测试1: 集成器初始化
        integration = V2Integration()
        
        if hasattr(integration, 'kb_manager') and hasattr(integration, 'multimodal_processor'):
            print_test("集成器初始化", "PASS", "管理器组件正常")
        else:
            print_test("集成器初始化", "FAIL", "管理器组件缺失")
        
        # 测试2: 方法检查
        required_methods = [
            'render_incremental_update_ui',
            'render_multimodal_ui', 
            'render_v2_features'
        ]
        
        missing_methods = [method for method in required_methods if not hasattr(integration, method)]
        
        if not missing_methods:
            print_test("集成方法", "PASS", f"所有 {len(required_methods)} 个方法存在")
        else:
            print_test("集成方法", "FAIL", f"缺失方法: {missing_methods}")
        
    except ImportError:
        print_test("v2.0集成模块", "SKIP", "模块不存在（v1.8版本）")
    except Exception as e:
        print_test("v2.0集成功能", "FAIL", str(e))

def test_smart_startup():
    """测试智能启动功能"""
    print_header("智能启动功能测试")
    
    try:
        start_script = "scripts/start.sh"
        
        if not os.path.exists(start_script):
            print_test("启动脚本存在", "FAIL", "scripts/start.sh 不存在")
            return
        
        with open(start_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 测试1: v2.0检测逻辑
        if 'V2_AVAILABLE' in content:
            print_test("v2.0检测逻辑", "PASS", "包含 V2_AVAILABLE 变量")
        else:
            print_test("v2.0检测逻辑", "FAIL", "缺少 V2_AVAILABLE 检测")
        
        # 测试2: 模块检测
        required_checks = [
            'IncrementalUpdater',
            'MultimodalProcessor'
        ]
        
        found_checks = [check for check in required_checks if check in content]
        
        if len(found_checks) == len(required_checks):
            print_test("模块检测", "PASS", f"检测 {len(required_checks)} 个关键模块")
        else:
            print_test("模块检测", "FAIL", f"只检测 {len(found_checks)}/{len(required_checks)} 个模块")
        
        # 测试3: 条件启动
        if 'if [ "$V2_AVAILABLE" = true ]' in content:
            print_test("条件启动", "PASS", "包含条件启动逻辑")
        else:
            print_test("条件启动", "FAIL", "缺少条件启动逻辑")
        
        # 测试4: API服务启动
        if 'fastapi_server.py' in content:
            print_test("API服务启动", "PASS", "包含API服务启动")
        else:
            print_test("API服务启动", "FAIL", "缺少API服务启动")
        
    except Exception as e:
        print_test("智能启动功能", "FAIL", str(e))

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  RAG Pro Max v2.0 可行性测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 执行所有v2.0测试
    test_incremental_update()
    test_multimodal_support()
    test_api_extensions()
    test_integration()
    test_smart_startup()
    
    print_header("测试总结")
    print("🎉 v2.0 可行性测试完成！")
    print("")
    print("📋 功能状态:")
    print("   ✨ 增量更新 - 智能文件变化检测")
    print("   🎨 多模态支持 - 图片OCR + 表格提取")
    print("   🔌 API扩展 - RESTful接口")
    print("   🚀 智能启动 - 自动检测和兼容")
    print("")
    print("💡 如果看到SKIP状态，说明运行的是v1.8版本")
    print("   运行 ./scripts/deploy_v2.sh 可安装v2.0功能")

if __name__ == "__main__":
    main()
