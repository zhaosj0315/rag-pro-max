#!/usr/bin/env python3
"""
API端点功能测试
测试REST API的核心端点和接口
"""

import os
import sys
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAPIEndpoints(unittest.TestCase):
    """API端点功能测试"""
    
    def test_fastapi_server(self):
        """测试FastAPI服务器"""
        from src.api.fastapi_server import app
        
        # 验证应用对象
        self.assertIsNotNone(app)
        
        # 检查路由
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        self.assertGreater(len(routes), 0)
        
        # 检查关键路由
        expected_routes = ["/health", "/api/v1"]
        for route in expected_routes:
            route_exists = any(route in r for r in routes)
            if not route_exists:
                print(f"警告: 路由 {route} 可能不存在")
    
    def test_api_server(self):
        """测试API服务器"""
        try:
            from src.api.api_server import APIServer
            
            # 验证类存在
            self.assertTrue(callable(APIServer))
        except ImportError:
            self.skipTest("APIServer模块不存在")
    
    def test_api_routes_structure(self):
        """测试API路由结构"""
        from src.api.fastapi_server import app
        
        # 获取所有路由
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if route.methods else []
                })
        
        # 验证至少有基础路由
        self.assertGreater(len(routes), 0)
        
        # 检查健康检查端点
        health_routes = [r for r in routes if 'health' in r['path'].lower()]
        if not health_routes:
            print("警告: 缺少健康检查端点")

def run_api_endpoint_tests():
    """运行API端点测试"""
    print("=" * 60)
    print("  API端点功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIEndpoints)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_api_endpoint_tests()
    sys.exit(0 if success else 1)
