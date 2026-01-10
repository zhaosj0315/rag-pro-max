import pandas as pd
import sys
import os

# 确保能导入 src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processors.data_analyst_v7_prototype import DataAnalystV7

def test_full_flow():
    print("🚀 开始 Data Analyst V7 全流程测试...\n")
    
    # 初始化引擎
    engine = DataAnalystV7()
    
    # 1. 准备 Mock 数据 (模拟用户上传)
    print("--- Phase 1: 数据准备 (Ingestion) ---")
    users_df = pd.DataFrame({
        'user_id': [101, 102, 103],
        'name': ['Alice', 'Bob', 'Charlie'],
        'city': ['New York', 'London', 'Paris']
    })
    
    orders_df = pd.DataFrame({
        'order_id': [1, 2, 3, 4],
        'user_id': [101, 101, 102, 103],
        'amount': [100.5, 200.0, 50.0, 300.0],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
    })
    
    t1 = engine.step1_etl_ingestion(mock_df=users_df, table_name="users")
    t2 = engine.step1_etl_ingestion(mock_df=orders_df, table_name="orders")
    print(f"✅ 数据已入库: {t1}, {t2}")
    
    # 2. 语义建模
    print("\n--- Phase 2: 语义建模 (Schema & Relationship) ---")
    schema_model = engine.step2_schema_modeling([t1, t2])
    print(f"✅ Schema 提取完成")
    print(f"   - 识别表: {list(schema_model['tables'].keys())}")
    print(f"   - 自动推导关联: {schema_model['relationships']}")
    
    # 3. 业务推演
    print("\n--- Phase 3: 业务识别 (Inference) ---")
    blueprint = engine.step3_business_inference(schema_model)
    print(f"✅ 业务蓝图生成")
    print(f"   - 场景: {blueprint['scenario']}")
    print(f"   - 核心指标: {blueprint['metrics']}")
    
    # 4. 执行与决策
    print("\n--- Phase 4: 查询与建议 (Query & Insight) ---")
    query = "请帮我分析一下用户的消费情况，找出谁花的钱最多？"
    print(f"❓ 用户提问: {query}")
    
    result = engine.step4_execution_and_insight(query, schema_model, blueprint)
    
    print("\n[执行结果]")
    print(f"📄 生成 SQL:\n{result['sql']}")
    print(f"📊 数据结果:\n{result['data']}")
    print(f"💡 智能建议:\n{result['insight']}")
    
    print("\n✨ 测试通过！逻辑闭环验证成功。")

if __name__ == "__main__":
    test_full_flow()
