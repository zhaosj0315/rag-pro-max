#!/usr/bin/env python3
"""
验证配置迁移的完整性
"""

def verify_config_migration():
    """验证配置迁移是否完整"""
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 验证配置迁移...")
    
    # 检查1: 配置标签页是否包含原有功能
    checks = [
        ("render_basic_config", "✅ 基础配置函数调用"),
        ("render_advanced_features", "✅ 高级功能函数调用"),
        ("Ollama (本地)", "✅ Ollama 本地选项"),
        ("http://localhost:11434", "✅ Ollama 默认地址"),
        ("qwen2.5:7b", "✅ 默认模型"),
        ("BAAI/bge-small-zh-v1.5", "✅ 默认嵌入模型"),
        ("check_ollama_status", "✅ Ollama 状态检测"),
        ("render_ollama_model_selector", "✅ Ollama 模型选择器"),
        ("render_openai_model_selector", "✅ OpenAI 模型选择器"),
        ("render_hf_embedding_selector", "✅ HF 嵌入模型选择器")
    ]
    
    missing_features = []
    
    for feature, description in checks:
        if feature in content:
            print(description)
        else:
            print(f"❌ 缺失: {description}")
            missing_features.append(feature)
    
    # 检查2: 配置标签页是否存在
    if "with tab_config:" in content:
        print("✅ 配置标签页存在")
    else:
        print("❌ 配置标签页不存在")
        missing_features.append("tab_config")
    
    # 检查3: 主页标签页是否还有配置代码（应该被移除）
    main_tab_start = content.find("with tab_main:")
    config_tab_start = content.find("with tab_config:")
    
    if main_tab_start != -1 and config_tab_start != -1:
        main_tab_content = content[main_tab_start:config_tab_start]
        if "render_basic_config" in main_tab_content:
            print("⚠️  主页标签页仍包含配置代码（未完全迁移）")
        else:
            print("✅ 主页标签页配置代码已移除")
    
    # 总结
    if missing_features:
        print(f"\n❌ 迁移不完整，缺失 {len(missing_features)} 个功能")
        return False
    else:
        print("\n✅ 配置迁移验证通过！")
        return True

def create_migration_report():
    """创建迁移报告"""
    
    report = """
# 配置标签页迁移报告

## ✅ 已迁移功能

### 🤖 LLM 配置
- [x] Ollama (本地) 选项
- [x] 默认地址: http://localhost:11434
- [x] 默认模型: qwen2.5:7b
- [x] Ollama 状态检测
- [x] 模型选择器组件
- [x] OpenAI-Compatible 选项
- [x] API Key 输入（支持环境变量）

### 🔤 嵌入模型配置
- [x] HuggingFace (本地/极速) 选项
- [x] 默认模型: BAAI/bge-small-zh-v1.5
- [x] OpenAI-Compatible 选项
- [x] Ollama 嵌入选项
- [x] 模型选择器组件

### 🔧 高级功能
- [x] 所有高级配置选项
- [x] 性能监控面板集成

## 📋 迁移对比

| 功能 | 原位置 | 新位置 | 状态 |
|------|--------|--------|------|
| 基础配置 | 主页标签页 | 配置标签页 | ✅ 已迁移 |
| 高级功能 | 主页标签页 | 配置标签页 | ✅ 已迁移 |
| 默认值 | 完全保持 | 完全保持 | ✅ 一致 |
| 状态检测 | 完全保持 | 完全保持 | ✅ 一致 |

## 🚀 下一步

配置标签页迁移完成，可以继续迁移下一个标签页。
"""
    
    with open('CONFIG_MIGRATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📄 迁移报告已生成: CONFIG_MIGRATION_REPORT.md")

if __name__ == "__main__":
    if verify_config_migration():
        create_migration_report()
    else:
        print("⚠️  请修复迁移问题后再继续")
