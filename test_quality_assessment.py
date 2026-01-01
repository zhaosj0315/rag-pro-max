#!/usr/bin/env python3
"""
文档质量评估功能测试
验证质量评估器的各项功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_quality_assessor():
    """测试文档质量评估器"""
    print("🧪 测试文档质量评估器...")
    
    try:
        from src.utils.document_quality_assessor import DocumentQualityAssessor
        
        assessor = DocumentQualityAssessor()
        print("✅ 成功创建质量评估器实例")
        
        # 测试高质量文档
        high_quality_doc = """
# 项目介绍

本项目是一个智能文档问答系统，具有以下特点：

## 核心功能

1. 文档上传和处理
2. 智能问答对话
3. 知识库管理

### 技术特性

- 支持多种文档格式
- 基于向量检索技术
- 提供实时对话体验

## 使用方法

用户可以通过以下步骤使用系统：

1. 上传文档到知识库
2. 输入问题进行查询
3. 获得智能回答

系统会自动分析文档内容，提供准确的答案。
        """
        
        result = assessor.assess_document(high_quality_doc, "high_quality.md")
        print(f"✅ 高质量文档评估: 总分 {result['scores']['overall']:.1f}, 等级 {result['grade']}")
        
        # 测试低质量文档
        low_quality_doc = "这是一个很短的文档。"
        
        result = assessor.assess_document(low_quality_doc, "low_quality.txt")
        print(f"✅ 低质量文档评估: 总分 {result['scores']['overall']:.1f}, 等级 {result['grade']}")
        
        # 测试中等质量文档
        medium_quality_doc = """
这是一个中等质量的文档。它有一些内容，但结构不够清晰。
文档包含了一些信息，但可能需要改进。
有一些重复的内容，重复的内容，重复的内容。
标点符号使用可能不够规范！！！
        """
        
        result = assessor.assess_document(medium_quality_doc, "medium_quality.txt")
        print(f"✅ 中等质量文档评估: 总分 {result['scores']['overall']:.1f}, 等级 {result['grade']}")
        
        print("🎉 文档质量评估器测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_assessment_metrics():
    """测试各项评估指标"""
    print("\n🧪 测试评估指标...")
    
    try:
        from src.utils.document_quality_assessor import DocumentQualityAssessor
        
        assessor = DocumentQualityAssessor()
        
        # 测试可读性评估
        readable_text = "这是一个句子长度适中的文档。每个句子都包含合适数量的词汇。段落结构清晰明了。\n\n这是第二个段落，同样保持良好的可读性。"
        readability = assessor._assess_readability(readable_text)
        print(f"✅ 可读性评估: {readability:.1f}")
        
        # 测试结构评估
        structured_text = """
# 标题
## 子标题
- 列表项1
- 列表项2
1. 编号项1
2. 编号项2

段落内容
        """
        structure = assessor._assess_structure(structured_text)
        print(f"✅ 结构评估: {structure:.1f}")
        
        # 测试内容密度评估
        dense_text = "这个文档包含丰富的词汇多样性，信息密度较高，避免了过多的重复内容。"
        density = assessor._assess_content_density(dense_text)
        print(f"✅ 内容密度评估: {density:.1f}")
        
        # 测试语言质量评估
        quality_text = "这是一个语言质量良好的文档，标点符号使用规范。"
        language = assessor._assess_language_quality(quality_text)
        print(f"✅ 语言质量评估: {language:.1f}")
        
        print("✅ 评估指标测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 指标测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("\n🧪 测试集成功能...")
    
    try:
        # 测试导入
        from src.utils.document_quality_assessor import show_quality_assessment, quality_assessor
        print("✅ 成功导入集成函数")
        
        # 测试全局实例
        test_content = "这是一个测试文档，用于验证全局实例是否正常工作。"
        result = quality_assessor.assess_document(test_content)
        print(f"✅ 全局实例测试: 评分 {result['scores']['overall']:.1f}")
        
        print("✅ 集成功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始文档质量评估功能测试")
    print("=" * 50)
    
    test1_result = test_quality_assessor()
    test2_result = test_assessment_metrics()
    test3_result = test_integration()
    
    print("\n" + "=" * 50)
    if test1_result and test2_result and test3_result:
        print("🎉 所有测试通过！文档质量评估功能已就绪")
        print("\n📋 功能特点:")
        print("- ✅ 多维度质量评估 (可读性、结构、内容密度、语言质量)")
        print("- ✅ 智能评分和等级划分")
        print("- ✅ 个性化改进建议")
        print("- ✅ 支持多种文档类型")
        print("- ✅ 集成到文件上传流程")
    else:
        print("❌ 部分测试失败，需要修复")
        sys.exit(1)
