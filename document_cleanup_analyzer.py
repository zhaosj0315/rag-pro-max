#!/usr/bin/env python3
"""
RAG Pro Max 文档清理分析器
识别可清理的过程文档和需要保留的核心文档
"""

import os
from pathlib import Path
from datetime import datetime

class DocumentCleanupAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def analyze_documents(self):
        """分析所有文档，分类为核心文档和过程文档"""
        
        # 永久保护列表 - 这些文档绝对不能删除
        PROTECTED_DOCS = [
            'post_development_sync_standard.md',
            'development_cleanup_standard.md', 
            'sync_audit_report',
            'documentation_maintenance_standard.md',
            'non_essential_push_standard.md',
            'readme.md',
            'changelog.md',
            'faq.md',
            'deployment.md',
            'user_manual.md',
            'api_documentation.md',
            'architecture.md',
            'development_standard.md',
            'single_feature_iteration_standard.md',
            'testing.md',
            'contributing.md'
        ]
        
        # 获取所有markdown文档
        all_docs = list(self.project_root.rglob("*.md"))
        
        # 分类文档
        core_docs = []      # 核心功能文档 - 必须保留
        process_docs = []   # 过程文档 - 可以清理
        temp_docs = []      # 临时文档 - 应该清理
        
        for doc in all_docs:
            doc_name = doc.name.lower()
            doc_path = str(doc.relative_to(self.project_root))
            
            # 检查是否在保护列表中
            is_protected = any(protected in doc_name for protected in PROTECTED_DOCS)
            
            if is_protected:
                core_docs.append({
                    "path": doc_path,
                    "name": doc.name,
                    "reason": "🔒 永久保护文档 - 禁止删除",
                    "size_kb": doc.stat().st_size / 1024
                })
                continue
                core_docs.append({
                    "path": doc_path,
                    "name": doc.name,
                    "reason": "用户或开发者核心文档",
                    "size_kb": doc.stat().st_size / 1024
                })
            
            # 临时工作计划 - 可以清理
            elif "work_plans/" in doc_path:
                temp_docs.append({
                    "path": doc_path,
                    "name": doc.name,
                    "reason": "临时工作计划，已完成可删除",
                    "size_kb": doc.stat().st_size / 1024
                })
            
            # 其他标准文档 - 谨慎处理
            elif any(keyword in doc_name for keyword in [
                'standard', 'cleanup', 'sync', 'audit', 'maintenance',
                'push', 'development', 'logging', 'notification',
                'enterprise', 'kanban', 'template', 'sop'
            ]):
                # 只有明确可删除的才放入process_docs
                if any(deletable in doc_name for deletable in [
                    'non_essential_push', 'logging_notification', 
                    'enterprise_document', 'kanban_template'
                ]):
                    process_docs.append({
                        "path": doc_path,
                        "name": doc.name,
                        "reason": "非核心标准文档，可删除",
                        "size_kb": doc.stat().st_size / 1024
                    })
                else:
                    # 其他标准文档默认保留
                    core_docs.append({
                        "path": doc_path,
                        "name": doc.name,
                        "reason": "重要标准文档 - 保留",
                        "size_kb": doc.stat().st_size / 1024
                    })
            
            # 其他文档
            else:
                # 检查内容判断重要性
                try:
                    content = doc.read_text(encoding='utf-8')
                    if len(content) < 1000:  # 小文档可能是临时的
                        temp_docs.append({
                            "path": doc_path,
                            "name": doc.name,
                            "reason": "内容较少，可能是临时文档",
                            "size_kb": doc.stat().st_size / 1024
                        })
                    else:
                        core_docs.append({
                            "path": doc_path,
                            "name": doc.name,
                            "reason": "内容丰富，暂时保留",
                            "size_kb": doc.stat().st_size / 1024
                        })
                except:
                    process_docs.append({
                        "path": doc_path,
                        "name": doc.name,
                        "reason": "无法读取，建议检查",
                        "size_kb": doc.stat().st_size / 1024
                    })
        
        return {
            "core_docs": core_docs,
            "process_docs": process_docs,
            "temp_docs": temp_docs,
            "total_docs": len(all_docs)
        }
    
    def generate_cleanup_plan(self, analysis):
        """生成清理计划"""
        
        # 计算可节省的空间
        process_size = sum(doc["size_kb"] for doc in analysis["process_docs"])
        temp_size = sum(doc["size_kb"] for doc in analysis["temp_docs"])
        total_cleanup_size = process_size + temp_size
        
        cleanup_plan = f"""# RAG Pro Max 文档清理计划

## 📊 分析结果

- **总文档数**: {analysis['total_docs']} 个
- **核心文档**: {len(analysis['core_docs'])} 个 (必须保留)
- **过程文档**: {len(analysis['process_docs'])} 个 (可以清理)
- **临时文档**: {len(analysis['temp_docs'])} 个 (应该清理)
- **可节省空间**: {total_cleanup_size:.1f} KB

---

## ✅ 核心文档 (保留)

这些文档对项目功能和用户使用至关重要：

"""
        
        for doc in sorted(analysis["core_docs"], key=lambda x: x["name"]):
            cleanup_plan += f"- **{doc['name']}** - {doc['reason']} ({doc['size_kb']:.1f}KB)\n"
        
        cleanup_plan += f"""

---

## 🗑️ 建议清理的文档

### 过程文档 ({len(analysis['process_docs'])} 个)
这些是开发过程中产生的标准文档，可以整合或删除：

"""
        
        for doc in sorted(analysis["process_docs"], key=lambda x: x["size_kb"], reverse=True):
            cleanup_plan += f"- `{doc['path']}` - {doc['reason']} ({doc['size_kb']:.1f}KB)\n"
        
        cleanup_plan += f"""

### 临时文档 ({len(analysis['temp_docs'])} 个)
这些是临时生成的工作文档，完成后可以删除：

"""
        
        for doc in sorted(analysis["temp_docs"], key=lambda x: x["size_kb"], reverse=True):
            cleanup_plan += f"- `{doc['path']}` - {doc['reason']} ({doc['size_kb']:.1f}KB)\n"
        
        cleanup_plan += f"""

---

## 🎯 清理建议

### 立即删除
```bash
# 删除临时工作计划
rm -rf work_plans/

# 删除过程标准文档
rm DEVELOPMENT_CLEANUP_STANDARD.md
rm POST_DEVELOPMENT_SYNC_STANDARD.md
rm DOCUMENTATION_MAINTENANCE_STANDARD.md
rm NON_ESSENTIAL_PUSH_STANDARD.md
rm LOGGING_AND_NOTIFICATION_STANDARD.md
rm ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md
rm CONTINUOUS_QUALITY_SOP.md
rm PROJECT_KANBAN_TEMPLATE.md
rm SYNC_AUDIT_REPORT_v3.2.2.md
```

### 整合建议
1. **开发规范整合**: 将多个STANDARD文档整合到`DEVELOPMENT_STANDARD.md`
2. **接口文档整合**: 将`INTERFACE_SUMMARY.md`和`INTERNAL_API.md`整合到`API_DOCUMENTATION.md`
3. **指南文档整合**: 将`CONTINUOUS_OPTIMIZATION_GUIDE.md`整合到`README.md`

### 保留的核心文档结构
```
docs/
├── README.md              # 项目介绍和快速开始
├── CHANGELOG.md           # 版本更新记录
├── FAQ.md                 # 常见问题
├── USER_MANUAL.md         # 用户使用手册
├── DEPLOYMENT.md          # 部署指南
├── API_DOCUMENTATION.md   # API文档
├── ARCHITECTURE.md        # 架构说明
├── DEVELOPMENT_STANDARD.md # 开发规范
├── SINGLE_FEATURE_ITERATION_STANDARD.md # 迭代规范
├── TESTING.md             # 测试指南
├── CONTRIBUTING.md        # 贡献指南
└── FIRST_TIME_GUIDE.md    # 新手指南
```

---

## 📈 清理效果

- **文档数量**: {analysis['total_docs']} → {len(analysis['core_docs'])} (-{len(analysis['process_docs']) + len(analysis['temp_docs'])})
- **节省空间**: {total_cleanup_size:.1f} KB
- **维护成本**: 大幅降低
- **文档质量**: 更加聚焦核心功能

清理后项目文档将更加简洁、聚焦，便于用户和开发者使用。
"""
        
        return cleanup_plan
    
    def execute_cleanup(self, analysis, confirm=False):
        """执行文档清理"""
        if not confirm:
            print("⚠️ 这是预览模式，不会实际删除文件")
            print("如需执行清理，请设置 confirm=True")
            return
        
        deleted_count = 0
        
        # 删除临时文档
        for doc in analysis["temp_docs"]:
            doc_path = self.project_root / doc["path"]
            if doc_path.exists():
                doc_path.unlink()
                deleted_count += 1
                print(f"✅ 已删除: {doc['path']}")
        
        # 删除过程文档（谨慎）
        for doc in analysis["process_docs"]:
            if any(keyword in doc["name"].lower() for keyword in [
                "cleanup", "sync", "audit", "maintenance", "push"
            ]):
                doc_path = self.project_root / doc["path"]
                if doc_path.exists():
                    doc_path.unlink()
                    deleted_count += 1
                    print(f"✅ 已删除: {doc['path']}")
        
        print(f"\n🎉 清理完成！共删除 {deleted_count} 个文档")

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    analyzer = DocumentCleanupAnalyzer(project_root)
    
    print("🔍 分析项目文档...")
    analysis = analyzer.analyze_documents()
    
    print("📋 生成清理计划...")
    cleanup_plan = analyzer.generate_cleanup_plan(analysis)
    
    # 保存清理计划
    plan_file = Path(project_root) / f"DOCUMENT_CLEANUP_PLAN_{datetime.now().strftime('%Y%m%d')}.md"
    plan_file.write_text(cleanup_plan, encoding='utf-8')
    
    print(f"📄 清理计划已保存: {plan_file}")
    
    # 输出摘要
    print(f"\n📊 文档分析摘要:")
    print(f"总文档: {analysis['total_docs']} 个")
    print(f"核心文档: {len(analysis['core_docs'])} 个 (保留)")
    print(f"过程文档: {len(analysis['process_docs'])} 个 (可清理)")
    print(f"临时文档: {len(analysis['temp_docs'])} 个 (应清理)")
    
    # 询问是否执行清理
    print(f"\n是否要执行清理？(输入 'yes' 确认)")
    user_input = input().strip().lower()
    
    if user_input == 'yes':
        analyzer.execute_cleanup(analysis, confirm=True)
    else:
        print("清理已取消，请查看清理计划文件")

if __name__ == "__main__":
    main()
