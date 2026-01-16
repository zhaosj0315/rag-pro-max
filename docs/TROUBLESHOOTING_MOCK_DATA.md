# 虚拟数据生成故障排查指南

## 🔍 问题诊断

如果虚拟数据生成失败，查看日志中的关键信息：

### 1. LLM 调用检查

**正常日志**：
```
🎲 [虚拟数据] 正在为表 'customer_orders' 生成测试数据...
   📝 LLM 返回长度: 518 字符
✅ [虚拟数据] 表 'customer_orders' 成功生成 5 条记录
```

**异常情况A - LLM 调用失败**：
```
🎲 [虚拟数据] 正在为表 'customer_orders' 生成测试数据...
   ❌ LLM 调用失败: Connection timeout
   🔄 直接使用备用方案...
```
**解决方案**：检查 LLM 配置（API Key、URL、网络连接）

**异常情况B - LLM 返回空**：
```
🎲 [虚拟数据] 正在为表 'customer_orders' 生成测试数据...
   📝 LLM 返回长度: 0 字符
⚠️ [虚拟数据] 表 'customer_orders' LLM 生成失败（0条），尝试备用方案...
```
**解决方案**：LLM 模型可能不支持或理解提示词，会自动使用备用方案

### 2. 备用方案检查

**正常日志**：
```
   🔄 [备用方案] 开始为表 'customer_orders' 生成占位数据...
✅ [虚拟数据] 表 'customer_orders' 使用备用方案生成 20 条记录
```

**异常情况 - 备用方案失败**：
```
   🔄 [备用方案] 开始为表 'customer_orders' 生成占位数据...
   ⚠️ 第 1 行插入失败: table customer_orders has no column named xxx
❌ [虚拟数据] 表 'customer_orders' 备用方案失败，0条记录
```
**解决方案**：表结构定义有问题，检查 schema 中的字段定义

### 3. 数据查询检查

**正常日志**：
```
📜 [SQL] SELECT * FROM customer_orders LIMIT 10
✅ [结果] 成功命中 5 行记录
```

**异常情况 - 查询无数据**：
```
📜 [SQL] SELECT * FROM customer_orders WHERE status = 'xxx'
⚠️ [空值] 未匹配到任何记录
```
**解决方案**：SQL 条件过滤掉了所有数据，检查 WHERE 条件

## 🛠️ 常见问题

### Q1: 显示"该阶段执行了逻辑加工，未产生回显数据"

**原因**：
1. SQL 创建了临时表但没有数据
2. SQL 的 WHERE 条件过滤掉了所有数据
3. 虚拟数据生成失败

**解决方案**：
1. 查看上方的日志，确认是否有"✅ 成功生成 X 条记录"
2. 如果没有，检查 LLM 配置
3. 如果有，检查 SQL 的 WHERE 条件

### Q2: LLM 返回长度为 0

**原因**：
- LLM 模型不支持或不理解提示词
- API 配置错误
- 网络问题

**解决方案**：
- 系统会自动使用备用方案
- 备用方案会生成 20 条占位数据
- 数据可能不够真实，但能保证查询有结果

### Q3: 备用方案也失败

**原因**：
- 表结构定义错误
- 字段数量不匹配
- 数据类型不兼容

**解决方案**：
1. 检查 business_schema.json 中的字段定义
2. 确保字段名、类型正确
3. 查看详细错误日志

## 📊 诊断步骤

### 步骤1: 检查知识库目录

```bash
ls -la /path/to/knowledge_base/
```

应该看到：
- `business_schema.json` - 表结构定义
- `business_data.db` - SQLite 数据库

### 步骤2: 检查数据库

```bash
sqlite3 /path/to/knowledge_base/business_data.db

# 查看所有表
.tables

# 查看表结构
.schema customer_orders

# 查看数据
SELECT COUNT(*) FROM customer_orders;
SELECT * FROM customer_orders LIMIT 5;
```

### 步骤3: 查看日志

在 Streamlit 应用中，查看控制台输出，寻找：
- 🎲 虚拟数据生成的日志
- ✅ 成功或 ❌ 失败的标记
- 📝 LLM 返回长度
- ⚠️ 错误提示

## 🔧 手动修复

如果自动生成失败，可以手动插入数据：

```bash
sqlite3 /path/to/knowledge_base/business_data.db

INSERT INTO customer_orders VALUES 
  ('ORD001', 'C001', '张三', '笔记本电脑', 5999.00, '2025-01-15', '已完成', '北京'),
  ('ORD002', 'C002', '李四', '手机', 3999.00, '2025-01-16', '已发货', '上海'),
  ('ORD003', 'C003', '王五', '平板电脑', 2999.00, '2025-01-17', '已支付', '广州');

.quit
```

然后重新提问，系统会使用这些数据。

## 📞 获取帮助

如果以上方法都无法解决，请提供：
1. 完整的日志输出
2. business_schema.json 内容
3. LLM 配置信息
4. 具体的错误提示

---

**更新日期**: 2026-01-16  
**版本**: v6.6.5
