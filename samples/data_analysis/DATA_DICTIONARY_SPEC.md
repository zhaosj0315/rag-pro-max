# 企业级核心业务数据字典 (v5.0 战略仿真样板)

本档定义了零售业务系统的核心表结构，用于指导数据中台的建设与宏观经营分析。

## 1. 订单主表 (fact_orders)
**业务定义**: 记录全渠道销售订单的宏观数据。
| 字段名 | 类型 | 注释 | 宏观意义 |
| :--- | :--- | :--- | :--- |
| order_id | STRING | 订单唯一标识 | 交易频次统计基数 |
| user_id | STRING | 用户ID | 用户渗透率分析 |
| total_amount | DOUBLE | 订单总金额 | 营收核心指标 |
| order_date | DATETIME | 下单时间 | 时序增长趋势分析 |
| region | STRING | 所属区域 | 地理维度盈亏分析 |
| ds | STRING | 分区字段 (yyyymmdd) | DataWorks 调度与离线计算基准 |

## 2. 促销活动表 (dim_promotions)
**业务定义**: 记录各类营销活动的策略与预算。
| 字段名 | 类型 | 注释 | 宏观意义 |
| :--- | :--- | :--- | :--- |
| promo_id | STRING | 活动ID | 活动覆盖度分析 |
| promo_name | STRING | 活动名称 | 品牌认知度关联 |
| discount_cost | DOUBLE | 促销折让成本 | ROI 投入产出比分析 |
| start_date | DATETIME | 开始时间 | 活动生命周期 |

## 3. 用户画像表 (dim_users)
**业务定义**: 记录消费者的宏观分布特征。
| 字段名 | 类型 | 注释 | 宏观意义 |
| :--- | :--- | :--- | :--- |
| user_id | STRING | 用户ID | 唯一实体标识 |
| user_level | STRING | 会员等级 (Gold/Silver/Bronze) | 存量资产质量评估 |
| source_channel | STRING | 获客渠道 | 获客效率与渠道权重分析 |

---
**业务关联逻辑**:
1. `fact_orders` 通过 `user_id` 与 `dim_users` 关联，用于分析不同会员等级的营收贡献。
2. `fact_orders` 通过 `promo_id` 与 `dim_promotions` 关联，用于评估营销活动的宏观拉动效果。
