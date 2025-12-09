# 🚀 安全启动指南

## ✅ 推荐方式（自动测试）

**以后每次启动都用这个命令：**

```bash
./scripts/start.sh
```

这个脚本会：
1. 🔍 自动运行出厂测试（64 项）
2. ✅ 测试通过 → 启动应用
3. ❌ 测试失败 → 阻止启动，提示修复

## 📋 启动流程

```bash
$ ./scripts/start.sh

🔍 启动前检测...

============================================================
  RAG Pro Max 出厂测试
============================================================
✅ 通过: 64/67

✅ 测试通过！正在启动应用...

  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

## ⚠️ 不推荐的方式

```bash
# ❌ 直接启动（跳过测试，可能运行有问题的代码）
streamlit run src/apppro.py
```

## 🔧 其他命令

```bash
# 只测试不启动
./scripts/test.sh

# 手动测试
python3 tests/factory_test.py
```

## 💡 工作流程

```bash
# 1. 修改代码
vim src/apppro.py

# 2. 安全启动（自动测试）
./scripts/start.sh

# 如果测试失败：
# ❌ 出厂测试失败！应用未启动
# 💡 请修复问题后再启动

# 3. 修复问题后重新启动
./scripts/start.sh
```

---

**记住：以后启动就用 `./scripts/start.sh`，不要用 `streamlit run src/apppro.py`**
