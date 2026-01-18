
# 用户画像接口定义 (User Profile API)

## 接口说明
该接口用于返回 CRM 系统中的用户基础画像信息。

## 响应结构 (Response Body)

该数据对应数据库中的 `crm_user_profile` 表。

| 字段 (Key) | 类型 (Type) | 含义 (Meaning) | 备注 |
| :--- | :--- | :--- | :--- |
| uid | Long | 用户ID | 主键 |
| nick_name | String | 昵称 | |
| real_name | String | 真实姓名 | 脱敏显示 |
| gender | Int | 性别 | 0:未知, 1:男, 2:女 |
| birthday | Date | 出生日期 | YYYY-MM-DD |
| vip_level | Int | 会员等级 | 1-5级 |
| total_spend | Double | 历史总消费 | 累计金额 |
| last_login | DateTime | 最后登录时间 | |
| tags | String | 用户标签 | 逗号分隔 (如: 高价值, 易流失) |

