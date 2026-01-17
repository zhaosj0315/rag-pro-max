#!/usr/bin/env python3
"""
虚拟数据生成功能使用示例

演示如何在只有表结构的情况下，自动生成数据并进行分析
"""

def example_1_empty_table():
    """示例1: 处理空表"""
    print("="*60)
    print("示例1: 处理只有结构的空表")
    print("="*60)
    
    print("""
# 假设你有一个知识库路径
kb_path = "/path/to/your/knowledge_base"

# 创建数据分析引擎
from processors.data_analyst import DataAnalystEngine
engine = DataAnalystEngine(kb_path)

# 定义表结构（只有结构，没有数据）
schema = {
    "macro_context": "企业销售数据分析系统",
    "tables": {
        "sales_data": {
            "desc": "销售数据表",
            "cols": [
                {"name": "product_id", "type": "TEXT", "comment": "产品ID"},
                {"name": "product_name", "type": "TEXT", "comment": "产品名称"},
                {"name": "category", "type": "TEXT", "comment": "产品类别"},
                {"name": "sales_amount", "type": "REAL", "comment": "销售额"},
                {"name": "sales_date", "type": "TEXT", "comment": "销售日期"}
            ]
        }
    }
}

# 执行分析（系统会自动检测空表并生成数据）
query = "统计各产品类别的总销售额，按销售额降序排列"
result = engine.execute_analysis(query, model_client)
    """)
    
    print("\n✅ 系统会自动:")
    print("   1. 检测到 sales_data 表为空")
    print("   2. 根据表结构和业务背景生成虚拟数据")
    print("   3. 执行 SQL 查询")
    print("   4. 返回分析结果")

def example_2_multiple_tables():
    """示例2: 处理多个空表"""
    print("\n" + "="*60)
    print("示例2: 处理多个关联的空表")
    print("="*60)
    
    print("""
schema = {
    "macro_context": "电商订单管理系统",
    "tables": {
        "customers": {
            "desc": "客户信息表",
            "cols": [
                {"name": "customer_id", "type": "TEXT", "comment": "客户ID"},
                {"name": "customer_name", "type": "TEXT", "comment": "客户姓名"},
                {"name": "city", "type": "TEXT", "comment": "所在城市"},
                {"name": "register_date", "type": "TEXT", "comment": "注册日期"}
            ]
        },
        "orders": {
            "desc": "订单信息表",
            "cols": [
                {"name": "order_id", "type": "TEXT", "comment": "订单ID"},
                {"name": "customer_id", "type": "TEXT", "comment": "客户ID"},
                {"name": "order_amount", "type": "REAL", "comment": "订单金额"},
                {"name": "order_date", "type": "TEXT", "comment": "下单日期"},
                {"name": "status", "type": "TEXT", "comment": "订单状态"}
            ]
        }
    }
}
    """)
    
    print("\n✅ 系统会自动:")
    print("   1. 为 customers 表生成客户数据")
    print("   2. 为 orders 表生成订单数据")
    print("   3. 确保 customer_id 在两个表中保持关联")
    print("   4. 支持跨表查询和分析")

def example_3_custom_generation():
    """示例3: 自定义数据生成策略"""
    print("\n" + "="*60)
    print("示例3: 自定义数据生成策略")
    print("="*60)
    
    print("\n如果需要更精确的数据生成，可以:")
    print("\n1. 在 schema 中提供更详细的字段说明:")
    
    print("""
schema = {
    "tables": {
        "products": {
            "desc": "产品信息表，包含电子产品和家居用品",
            "cols": [
                {
                    "name": "category",
                    "type": "TEXT",
                    "comment": "产品类别，可选值: 手机、电脑、家电、家具"
                },
                {
                    "name": "price",
                    "type": "REAL",
                    "comment": "产品价格，范围: 100-50000 元"
                }
            ]
        }
    }
}
    """)
    
    print("\n2. 或者修改 _generate_simple_mock_data 方法添加自定义规则")

def example_4_disable_generation():
    """示例4: 禁用虚拟数据生成"""
    print("\n" + "="*60)
    print("示例4: 禁用虚拟数据生成")
    print("="*60)
    
    print("\n如果不希望自动生成数据，可以:")
    print("\n方法1: 传入 model_client=None")
    print("""
mapping = engine._ensure_sandbox_ready(
    schemas,
    model_client=None,  # 禁用生成
    conn=conn
)
    """)
    
    print("\n方法2: 在调用前确保表已有数据")
    print("""
# 先导入真实数据
import pandas as pd
df = pd.read_csv('real_data.csv')
df.to_sql('table_name', conn, if_exists='replace')

# 然后执行分析
result = engine.execute_analysis(query, model_client)
    """)

if __name__ == "__main__":
    print("\n" + "🎓 虚拟数据生成功能使用示例\n")
    
    example_1_empty_table()
    example_2_multiple_tables()
    example_3_custom_generation()
    example_4_disable_generation()
    
    print("\n" + "="*60)
    print("📚 更多信息请参考: docs/MOCK_DATA_GENERATION.md")
    print("="*60 + "\n")
