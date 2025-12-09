# apppro.py 迁移计划

## 目标
将 apppro.py 从旧接口迁移到新模块接口

## 迁移内容

### 1. 日志模块迁移
**旧接口**:
```python
from src.logger import logger
from src.terminal_logger import terminal_logger
```

**新接口**:
```python
from src.logging import LogManager
logger = LogManager()
```

**影响范围**: 所有 logger.info/error/warning 调用

---

### 2. 配置模块迁移
**旧接口**:
```python
from src.utils.config_manager import load_config, save_config
config = load_config()
```

**新接口**:
```python
from src.config import AppConfig, RAGConfig
app_config = AppConfig()
rag_config = RAGConfig()
```

**影响范围**: 配置读写操作

---

### 3. 聊天模块迁移
**旧接口**:
```python
from src.utils.chat_manager import load_chat_history, save_chat_history
from src.chat_utils_improved import generate_follow_up_questions
```

**新接口**:
```python
from src.chat import ChatEngine, HistoryManager, SuggestionManager
history_mgr = HistoryManager()
suggestion_mgr = SuggestionManager()
```

**影响范围**: 聊天历史、建议生成

---

### 4. 知识库模块迁移
**旧接口**:
```python
from src.utils.kb_manager import get_existing_kbs, delete_kb, rename_kb
```

**新接口**:
```python
from src.kb import KBManager
kb_mgr = KBManager()
```

**影响范围**: 知识库管理操作

---

## 迁移步骤

### Phase 1: 日志模块（优先级：高）
- [ ] 替换 logger 导入
- [ ] 测试日志功能
- [ ] 验证日志文件生成

### Phase 2: 配置模块（优先级：高）
- [ ] 替换 config_manager 导入
- [ ] 更新配置读写逻辑
- [ ] 测试配置加载

### Phase 3: 聊天模块（优先级：中）
- [ ] 替换 chat_manager 导入
- [ ] 更新聊天历史逻辑
- [ ] 测试对话功能

### Phase 4: 知识库模块（优先级：中）
- [ ] 替换 kb_manager 导入
- [ ] 更新知识库操作
- [ ] 测试知识库管理

### Phase 5: 集成测试（优先级：高）
- [ ] 运行出厂测试
- [ ] 端到端测试
- [ ] 性能测试

---

## 风险评估

### 高风险
- 日志格式变化可能影响日志分析工具
- 配置文件结构变化可能导致兼容性问题

### 中风险
- 聊天历史格式变化
- 知识库元数据格式变化

### 低风险
- 导入路径变化（编译时可检测）

---

## 回滚计划

1. 保留 apppro.py 备份
2. 保留旧模块（标记为 deprecated）
3. 分阶段迁移，每阶段独立测试

---

## 时间估算

- Phase 1: 30 分钟
- Phase 2: 30 分钟
- Phase 3: 20 分钟
- Phase 4: 20 分钟
- Phase 5: 30 分钟

**总计**: ~2.5 小时
