# 场景2：只有表结构和字段定义，但无数据

## 表名：customer_orders

### 业务说明
客户订单表，记录所有客户的订单信息，用于分析订单趋势和客户购买行为。

### 字段定义

| 字段名 | 类型 | 说明 |
|--------|------|------|
| order_id | TEXT | 订单ID，唯一标识 |
| customer_id | TEXT | 客户ID |
| customer_name | TEXT | 客户姓名 |
| product_name | TEXT | 产品名称 |
| order_amount | REAL | 订单金额（元） |
| order_date | TEXT | 下单日期 YYYY-MM-DD |
| status | TEXT | 订单状态：待支付、已支付、已发货、已完成 |
| region | TEXT | 客户所在地区 |

### 数据说明
- 本表当前无实际数据
- 系统将根据字段定义自动生成虚拟数据用于分析
