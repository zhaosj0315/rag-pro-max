# 阶段2：合并重复函数

## 🎯 目标
处理130个重复函数中的高优先级项目，减少代码重复

## 🔥 高优先级重复函数

### P0 - 核心业务逻辑重复
1. **update_status** - 5个副本
2. **process_knowledge_base_logic** - 3个副本
3. **generate_smart_kb_name** - 4个副本
4. **cleanup_temp_files** - 3个副本

### P1 - 基础工具函数重复  
1. **cleanup_memory** - 3个副本
2. **get_llm** - 4个副本
3. **sanitize_filename** - 3个副本
4. **format_bytes** - 2个副本

### P2 - 配置管理重复
1. **load_config/save_config** - 多个副本
2. **get_memory_stats** - 2个副本

## 🚀 执行计划

### 第一步：创建公共工具模块
```bash
# 创建 src/common/utils.py
# 合并: cleanup_memory, sanitize_filename, format_bytes
```

### 第二步：创建业务逻辑模块  
```bash
# 创建 src/common/business.py
# 合并: update_status, process_knowledge_base_logic
```

### 第三步：创建配置管理模块
```bash
# 创建 src/common/config.py  
# 合并: load_config, save_config
```

## ⏱️ 预计时间：2-3小时

---
**状态**: 🔄 准备执行
**开始时间**: 2025-12-17 11:51
