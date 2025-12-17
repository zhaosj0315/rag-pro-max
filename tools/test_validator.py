#!/usr/bin/env python3
"""
测试验证工具 - 确保重构不破坏功能
"""

import subprocess
import time
import json
from pathlib import Path

class TestValidator:
    def __init__(self):
        self.baseline_results = None
        self.current_results = None
        
    def run_factory_test(self):
        """运行出厂测试"""
        print("🧪 运行出厂测试...")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['python', 'tests/factory_test.py'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            duration = time.time() - start_time
            
            # 解析测试结果
            output = result.stdout
            passed = output.count('✅ 通过:')
            failed = output.count('❌ 失败:')
            skipped = output.count('⏭️  跳过:')
            
            # 提取数字
            import re
            pass_match = re.search(r'✅ 通过: (\d+)/(\d+)', output)
            fail_match = re.search(r'❌ 失败: (\d+)/(\d+)', output)
            skip_match = re.search(r'⏭️  跳过: (\d+)/(\d+)', output)
            
            results = {
                'timestamp': time.time(),
                'duration': duration,
                'return_code': result.returncode,
                'passed': int(pass_match.group(1)) if pass_match else 0,
                'failed': int(fail_match.group(1)) if fail_match else 0,
                'skipped': int(skip_match.group(1)) if skip_match else 0,
                'total': int(pass_match.group(2)) if pass_match else 0,
                'success': result.returncode == 0,
                'output': output
            }
            
            return results
            
        except subprocess.TimeoutExpired:
            return {
                'timestamp': time.time(),
                'duration': 300,
                'return_code': -1,
                'error': 'Test timeout',
                'success': False
            }
        except Exception as e:
            return {
                'timestamp': time.time(),
                'duration': 0,
                'return_code': -1,
                'error': str(e),
                'success': False
            }
            
    def set_baseline(self):
        """设置基准测试结果"""
        print("📊 设置测试基准...")
        self.baseline_results = self.run_factory_test()
        
        if self.baseline_results['success']:
            print(f"✅ 基准设置成功: {self.baseline_results['passed']}/{self.baseline_results['total']} 通过")
        else:
            print(f"❌ 基准设置失败: {self.baseline_results.get('error', '未知错误')}")
            
        return self.baseline_results
        
    def validate_current(self):
        """验证当前状态"""
        print("🔍 验证当前状态...")
        self.current_results = self.run_factory_test()
        
        if not self.baseline_results:
            print("⚠️ 未设置基准，无法对比")
            return self.current_results
            
        # 对比结果
        baseline = self.baseline_results
        current = self.current_results
        
        print("\n📈 测试结果对比:")
        print(f"基准: {baseline['passed']}/{baseline['total']} 通过")
        print(f"当前: {current['passed']}/{current['total']} 通过")
        
        if current['passed'] >= baseline['passed']:
            print("✅ 测试通过率未下降")
            status = "PASS"
        else:
            print("❌ 测试通过率下降")
            status = "FAIL"
            
        if current['failed'] > baseline['failed']:
            print("⚠️ 新增失败测试")
            status = "WARN"
            
        return {
            'status': status,
            'baseline': baseline,
            'current': current,
            'regression': current['passed'] < baseline['passed']
        }
        
    def save_results(self, filename="test_results.json"):
        """保存测试结果"""
        results = {
            'baseline': self.baseline_results,
            'current': self.current_results,
            'timestamp': time.time()
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"💾 结果已保存: {filename}")
        
    def load_baseline(self, filename="test_results.json"):
        """加载基准结果"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.baseline_results = data.get('baseline')
                print("📂 基准结果已加载")
                return True
        except FileNotFoundError:
            print("📂 未找到基准文件")
            return False

def main():
    validator = TestValidator()
    
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python test_validator.py baseline  # 设置基准")
        print("  python test_validator.py validate  # 验证当前")
        print("  python test_validator.py test      # 仅运行测试")
        return
        
    command = sys.argv[1]
    
    if command == "baseline":
        validator.set_baseline()
        validator.save_results()
    elif command == "validate":
        validator.load_baseline()
        result = validator.validate_current()
        validator.save_results()
        
        if result['status'] == "FAIL":
            exit(1)
    elif command == "test":
        result = validator.run_factory_test()
        if result['success']:
            print(f"✅ 测试通过: {result['passed']}/{result['total']}")
        else:
            print(f"❌ 测试失败: {result.get('error', '未知错误')}")
            exit(1)

if __name__ == "__main__":
    main()
