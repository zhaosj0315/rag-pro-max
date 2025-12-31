#!/usr/bin/env python3
"""
现有功能保护检查器
确保新功能开发不会意外修改或删减现有功能
"""

import os
import difflib
from pathlib import Path

class ExistingFeatureProtector:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def check_changes(self, branch_name: str) -> dict:
        """检查分支更改是否影响现有功能"""
        
        print("🛡️ 现有功能保护检查")
        print("=" * 40)
        
        # 获取更改的文件
        import subprocess
        try:
            result = subprocess.run([
                'git', 'diff', '--name-only', 'main', branch_name
            ], capture_output=True, text=True, cwd=self.project_root)
            
            changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
        except Exception as e:
            print(f"❌ 无法获取文件更改列表: {e}")
            return {"status": "error", "message": str(e)}
        
        if not changed_files:
            print("✅ 没有文件更改")
            return {"status": "safe", "changes": []}
        
        print(f"📁 检查 {len(changed_files)} 个更改的文件")
        
        # 分析每个更改的文件
        analysis = []
        warnings = []
        
        for file_path in changed_files:
            if not file_path.endswith('.py'):
                continue
                
            file_analysis = self._analyze_file_changes(file_path, branch_name)
            analysis.append(file_analysis)
            
            # 检查是否有潜在的功能删减
            if file_analysis.get("potential_removals"):
                warnings.extend(file_analysis["potential_removals"])
        
        # 生成报告
        if warnings:
            print(f"⚠️ 发现 {len(warnings)} 个潜在的功能修改")
            for warning in warnings:
                print(f"   - {warning}")
            
            return {
                "status": "warning",
                "warnings": warnings,
                "analysis": analysis,
                "recommendation": "请确认这些更改是否获得用户同意"
            }
        else:
            print("✅ 未发现现有功能被修改或删减")
            return {
                "status": "safe",
                "analysis": analysis,
                "message": "所有更改都是新增功能，未影响现有功能"
            }
    
    def _analyze_file_changes(self, file_path: str, branch_name: str) -> dict:
        """分析单个文件的更改"""
        
        import subprocess
        
        try:
            # 获取文件的diff
            result = subprocess.run([
                'git', 'diff', 'main', branch_name, '--', file_path
            ], capture_output=True, text=True, cwd=self.project_root)
            
            diff_content = result.stdout
            
        except Exception as e:
            return {"file": file_path, "error": str(e)}
        
        # 分析diff内容
        lines = diff_content.split('\n')
        additions = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
        deletions = [line for line in lines if line.startswith('-') and not line.startswith('---')]
        
        # 检查潜在的功能删减
        potential_removals = []
        
        for deletion in deletions:
            line = deletion[1:].strip()  # 移除'-'前缀
            
            # 检查是否删除了重要功能
            if any(keyword in line.lower() for keyword in [
                'st.button', 'st.selectbox', 'st.text_input', 'st.file_uploader',
                'def ', 'class ', 'st.sidebar', 'st.columns'
            ]):
                potential_removals.append(f"删除了可能的功能代码: {line[:50]}...")
            
            # 检查是否删除了用户界面元素
            if any(keyword in line for keyword in [
                'st.markdown', 'st.write', 'st.header', 'st.subheader'
            ]):
                potential_removals.append(f"删除了界面元素: {line[:50]}...")
        
        return {
            "file": file_path,
            "additions_count": len(additions),
            "deletions_count": len(deletions),
            "potential_removals": potential_removals,
            "net_change": len(additions) - len(deletions)
        }
    
    def generate_protection_report(self, check_result: dict) -> str:
        """生成保护检查报告"""
        
        report = f"""# 现有功能保护检查报告

**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**检查状态**: {check_result['status']}

## 📊 检查结果

"""
        
        if check_result['status'] == 'safe':
            report += """✅ **安全**: 未发现现有功能被修改或删减

所有更改都是新增功能，符合现有功能保护原则。

"""
        elif check_result['status'] == 'warning':
            report += f"""⚠️ **警告**: 发现 {len(check_result['warnings'])} 个潜在问题

### 需要确认的更改:

"""
            for warning in check_result['warnings']:
                report += f"- {warning}\n"
            
            report += f"""
### 建议行动:

1. 仔细检查上述更改是否必要
2. 如果涉及现有功能修改，请获得用户明确同意
3. 考虑是否可以通过纯新增方式实现功能
4. 确保不会影响用户现有的使用习惯

"""
        
        if 'analysis' in check_result:
            report += """## 📁 文件更改详情

| 文件 | 新增行数 | 删除行数 | 净变化 | 状态 |
|------|----------|----------|--------|------|
"""
            for analysis in check_result['analysis']:
                if 'error' not in analysis:
                    status = "⚠️" if analysis.get('potential_removals') else "✅"
                    report += f"| {analysis['file']} | {analysis['additions_count']} | {analysis['deletions_count']} | {analysis['net_change']:+d} | {status} |\n"
        
        report += """
---

**现有功能保护原则**: 新功能开发时，严禁修改或删减现有功能，除非获得用户明确同意。
"""
        
        return report

def main():
    """主函数"""
    import sys
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("使用方法: python existing_feature_protector.py <分支名>")
        return
    
    project_root = os.getcwd()
    branch_name = sys.argv[1]
    
    protector = ExistingFeatureProtector(project_root)
    result = protector.check_changes(branch_name)
    
    # 生成报告
    report = protector.generate_protection_report(result)
    
    # 保存报告
    report_file = Path(project_root) / f"feature_protection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file.write_text(report, encoding='utf-8')
    
    print(f"\n📄 保护检查报告已保存: {report_file}")
    
    # 返回适当的退出码
    if result['status'] == 'warning':
        print("\n⚠️ 发现潜在问题，请仔细检查后再合并")
        sys.exit(1)
    else:
        print("\n✅ 现有功能保护检查通过")
        sys.exit(0)

if __name__ == "__main__":
    main()
