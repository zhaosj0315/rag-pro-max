#!/usr/bin/env python3
"""
诊断知识库的数据分析配置
"""

import os
import sys
import json
import sqlite3

def diagnose_kb(kb_path):
    """诊断知识库"""
    print("="*70)
    print(f"🔍 诊断知识库: {kb_path}")
    print("="*70)
    
    if not os.path.exists(kb_path):
        print(f"❌ 知识库目录不存在: {kb_path}")
        return False
    
    # 检查 schema 文件
    schema_path = os.path.join(kb_path, "business_schema.json")
    print(f"\n📄 检查 Schema 文件...")
    
    if not os.path.exists(schema_path):
        print(f"   ❌ business_schema.json 不存在")
        print(f"   💡 这是问题所在！需要创建 schema 文件")
        return False
    else:
        print(f"   ✅ business_schema.json 存在")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            tables = schema.get('tables', {})
            print(f"   📊 表数量: {len(tables)}")
            
            if not tables:
                print(f"   ❌ Schema 中没有表定义！")
                print(f"   💡 这是问题所在！Schema 是空的")
                return False
            
            for table_name, table_info in tables.items():
                cols = table_info.get('cols', table_info.get('columns', []))
                print(f"   ✅ 表 '{table_name}': {len(cols)} 个字段")
        
        except Exception as e:
            print(f"   ❌ Schema 文件格式错误: {e}")
            return False
    
    # 检查数据库
    db_path = os.path.join(kb_path, "business_data.db")
    print(f"\n📂 检查数据库...")
    
    if not os.path.exists(db_path):
        print(f"   ⚠️ business_data.db 不存在（首次查询时会创建）")
    else:
        print(f"   ✅ business_data.db 存在")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            db_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"   📊 数据库中的表: {len(db_tables)}")
            
            for table in db_tables:
                if table in ('dual', 'sqlite_sequence'):
                    continue
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = "✅" if count > 0 else "⚠️"
                print(f"   {status} 表 '{table}': {count} 条数据")
            
            conn.close()
        
        except Exception as e:
            print(f"   ❌ 数据库检查失败: {e}")
    
    print("\n" + "="*70)
    print("✅ 诊断完成")
    print("="*70)
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python diagnose_kb.py <知识库路径>")
        print("\n示例:")
        print("  python diagnose_kb.py /path/to/knowledge_base")
        print("  python diagnose_kb.py ~/Documents/rag-pro-max/knowledge_bases/admin_customer_orders_schema_20260116")
        sys.exit(1)
    
    kb_path = sys.argv[1]
    diagnose_kb(kb_path)
