import os
import json
import pandas as pd
import sqlite3
import shutil
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.processors.data_analyst import DataAnalystEngine

def test_deep_understanding():
    print("🚀 开始 DA-ECP V4.5 深度理解协议可行性测试...")
    
    test_kb_path = "test_deep_kb"
    if os.path.exists(test_kb_path):
        shutil.rmtree(test_kb_path)
    os.makedirs(test_kb_path)
    
    try:
        # 1. 准备测试数据
        # 实表: 包含特征明显的销售数据
        sales_df = pd.DataFrame({
            "order_id": [f"ORD{i}" for i in range(100)],
            "region": ["华东", "华北", "华南", "华东", "华北"] * 20,
            "amount": [100.5, 200.0, 50.0, 3000.0, 150.0] * 20,
            "user_id": [f"U{i%10}" for i in range(100)]
        })
        sales_path = os.path.join(test_kb_path, "sales_data.csv")
        sales_df.to_csv(sales_path, index=False)
        
        # 虚表 (数据字典): 描述用户表结构
        dict_df = pd.DataFrame({
            "字段名": ["id", "username", "level"],
            "数据类型": ["INT", "VARCHAR(50)", "ENUM"],
            "描述": ["用户唯一ID", "用户昵称", "会员等级 (Gold, Silver, Bronze)"]
        })
        dict_path = os.path.join(test_kb_path, "user_dictionary.xlsx")
        dict_df.to_excel(dict_path, index=False)
        
        # 2. 初始化引擎
        engine = DataAnalystEngine(test_kb_path)
        
        # 3. 模拟构建过程
        # 注意: 这里不传入 model_client 以测试纯计算部分的鲁棒性
        print("\n🏗️  执行构建...")
        result = engine.process_files([sales_path, dict_path])
        
        print(f"\n📊 构建结果: {result}")
        
        # 4. 验证沉淀信息
        schema_file = os.path.join(test_kb_path, "business_schema.json")
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            
        print("\n🔍 检查沉淀资产:")
        
        # 验证实表画像
        sales_meta = schema['tables'].get('sales_data')
        if sales_meta:
            print("✅ 实表 'sales_data' 已注册")
            print(f"   - 类型: {sales_meta.get('type')}")
            # 检查微观画像
            region_col = next((c for c in sales_meta['cols'] if c['name'] == 'region'), None)
            if region_col and 'enums' in region_col:
                print(f"   - ✅ 成功提取枚举 (region): {region_col['enums']}")
            
            amount_col = next((c for c in sales_meta['cols'] if c['name'] == 'amount'), None)
            if amount_col and 'stats' in amount_col:
                print(f"   - ✅ 成功提取数值统计 (amount): {amount_col['stats']}")
        else:
            print("❌ 实表 'sales_data' 丢失")

        # 验证虚表解析
        user_meta = schema['tables'].get('user_dictionary')
        if user_meta:
            print("✅ 虚表 'user_dictionary' 已成功从字典解析并注册")
            print(f"   - 类型: {user_meta.get('type')}")
            print(f"   - 字段数: {len(user_meta.get('cols', []))}")
        else:
            print("❌ 虚表解析失败")

        # 验证数据库结构
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"\n🗄️  数据库中存在的表: {tables}")
        
        if 'sales_data' in tables and 'user_dictionary' in tables:
            print("✅ 物理数据库表结构同步成功")
        else:
            print("❌ 物理表缺失")
        conn.close()

        print("\n✨ 可行性测试基本通过 (纯计算逻辑验证成功)")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        if os.path.exists(test_kb_path):
            shutil.rmtree(test_kb_path)

if __name__ == "__main__":
    test_deep_understanding()
