#!/usr/bin/env python3
"""
为现有知识库创建 business_schema.json
"""

import os
import sys
import json

def create_schema_for_customer_orders(kb_path):
    """为 customer_orders 知识库创建 schema"""
    schema = {
        "macro_context": "客户订单管理系统",
        "tables": {
            "customer_orders": {
                "desc": "客户订单表，记录所有客户的订单信息",
                "cols": [
                    {"name": "order_id", "type": "TEXT", "comment": "订单ID"},
                    {"name": "customer_id", "type": "TEXT", "comment": "客户ID"},
                    {"name": "customer_name", "type": "TEXT", "comment": "客户姓名"},
                    {"name": "product_name", "type": "TEXT", "comment": "产品名称"},
                    {"name": "order_amount", "type": "REAL", "comment": "订单金额"},
                    {"name": "order_date", "type": "TEXT", "comment": "下单日期"},
                    {"name": "status", "type": "TEXT", "comment": "订单状态"},
                    {"name": "region", "type": "TEXT", "comment": "客户所在地区"}
                ]
            }
        }
    }
    
    schema_path = os.path.join(kb_path, "business_schema.json")
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=4, ensure_ascii=False)
    
    print(f"✅ 已创建 schema: {schema_path}")
    return schema_path

def create_schema_for_sales_performance(kb_path):
    """为 sales_performance 知识库创建 schema"""
    schema = {
        "macro_context": "销售业绩管理系统",
        "tables": {
            "sales_performance": {
                "desc": "销售业绩表",
                "cols": [
                    {"name": "salesperson_id", "type": "TEXT", "comment": "销售人员ID"},
                    {"name": "salesperson_name", "type": "TEXT", "comment": "销售人员姓名"},
                    {"name": "region", "type": "TEXT", "comment": "销售地区"},
                    {"name": "product_line", "type": "TEXT", "comment": "产品线"},
                    {"name": "sales_amount", "type": "REAL", "comment": "销售金额"},
                    {"name": "sales_quantity", "type": "INTEGER", "comment": "销售数量"},
                    {"name": "month", "type": "TEXT", "comment": "月份"},
                    {"name": "target_status", "type": "TEXT", "comment": "达标状态"}
                ]
            }
        }
    }
    
    schema_path = os.path.join(kb_path, "business_schema.json")
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=4, ensure_ascii=False)
    
    print(f"✅ 已创建 schema: {schema_path}")
    return schema_path

if __name__ == "__main__":
    print("="*70)
    print("🔧 为现有知识库创建 Schema")
    print("="*70)
    
    # 查找知识库目录
    kb_base = os.path.expanduser("~/Documents/rag-pro-max/knowledge_bases")
    
    if not os.path.exists(kb_base):
        print(f"❌ 知识库目录不存在: {kb_base}")
        sys.exit(1)
    
    # 查找相关知识库
    for kb_name in os.listdir(kb_base):
        kb_path = os.path.join(kb_base, kb_name)
        
        if not os.path.isdir(kb_path):
            continue
        
        schema_path = os.path.join(kb_path, "business_schema.json")
        
        # 如果已有 schema，检查是否为空
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            if schema.get('tables'):
                print(f"✅ {kb_name}: 已有 schema ({len(schema['tables'])} 个表)")
                continue
        
        # 根据知识库名称创建对应的 schema
        if 'customer_orders' in kb_name.lower():
            print(f"\n📋 处理: {kb_name}")
            create_schema_for_customer_orders(kb_path)
        
        elif 'sales_performance' in kb_name.lower():
            print(f"\n📋 处理: {kb_name}")
            create_schema_for_sales_performance(kb_path)
        
        else:
            print(f"⚠️ {kb_name}: 未知类型，跳过")
    
    print("\n" + "="*70)
    print("✅ 处理完成")
    print("="*70)
    print("\n💡 现在重新启动应用并提问，应该能看到虚拟数据生成了")
