#!/usr/bin/env python3
"""
RAG Pro Max 版本统一工具
统一所有文件中的版本号，确保版本一致性
"""

import os
import re
from pathlib import Path
from datetime import datetime
import logging

class VersionUnifier:
    """版本统一管理器"""
    
    def __init__(self, project_root: str = None, target_version: str = "2.4.7"):
        self.project_root = Path(project_root or os.getcwd())
        self.target_version = target_version
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_dir = self.project_root / "sync_logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"version_unify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def update_apppro_version(self):
        """更新apppro.py中的版本号"""
        apppro_path = self.project_root / "src" / "apppro.py"
        if not apppro_path.exists():
            self.logger.warning("apppro.py 文件不存在")
            return False
        
        with open(apppro_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换版本号
        patterns = [
            r'__version__\s*=\s*["\']([^"\']+)["\']',
            r'VERSION\s*=\s*["\']([^"\']+)["\']',
            r'version\s*=\s*["\']([^"\']+)["\']',
            r'st\.set_page_config\([^)]*title=["\'][^"\']*v([0-9.]+)["\'][^)]*\)'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, content):
                if 'st.set_page_config' in pattern:
                    # 特殊处理streamlit页面配置
                    content = re.sub(
                        r'(st\.set_page_config\([^)]*title=["\'][^"\']*v)([0-9.]+)(["\'][^)]*\))',
                        f'\\1{self.target_version}\\3',
                        content
                    )
                else:
                    content = re.sub(pattern, f'\\g<0>'.replace(re.search(pattern, content).group(1), self.target_version), content)
                updated = True
                self.logger.info(f"更新apppro.py中的版本号: {pattern}")
        
        if updated:
            with open(apppro_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"apppro.py版本号已更新为: {self.target_version}")
            return True
        
        return False
    
    def update_requirements_version(self):
        """更新requirements.txt中的streamlit版本"""
        req_path = self.project_root / "requirements.txt"
        if not req_path.exists():
            self.logger.warning("requirements.txt 文件不存在")
            return False
        
        with open(req_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith('streamlit'):
                # 保持streamlit版本不变，只是记录
                self.logger.info(f"requirements.txt中streamlit版本: {line.strip()}")
                # 如果需要更新streamlit版本，可以在这里修改
                # lines[i] = f"streamlit>={self.target_version}\n"
                # updated = True
        
        if updated:
            with open(req_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            self.logger.info("requirements.txt已更新")
        
        return updated
    
    def add_version_to_apppro(self):
        """在apppro.py中添加版本号定义"""
        apppro_path = self.project_root / "src" / "apppro.py"
        if not apppro_path.exists():
            return False
        
        with open(apppro_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有版本定义
        if '__version__' in content or 'VERSION' in content:
            return self.update_apppro_version()
        
        # 在文件开头添加版本定义
        version_line = f'__version__ = "{self.target_version}"\n'
        
        # 找到合适的位置插入（通常在导入语句之前）
        lines = content.split('\n')
        insert_pos = 0
        
        # 跳过注释和docstring
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                insert_pos = i
                break
        
        lines.insert(insert_pos, version_line)
        
        with open(apppro_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        self.logger.info(f"已在apppro.py中添加版本号: {self.target_version}")
        return True
    
    def update_all_versions(self):
        """更新所有文件中的版本号"""
        self.logger.info(f"开始统一版本号为: {self.target_version}")
        
        results = {
            "apppro_updated": False,
            "requirements_checked": False,
            "total_updates": 0
        }
        
        # 1. 更新apppro.py
        if self.add_version_to_apppro():
            results["apppro_updated"] = True
            results["total_updates"] += 1
        
        # 2. 检查requirements.txt
        if self.update_requirements_version():
            results["requirements_checked"] = True
        
        # 3. 验证README.md和CHANGELOG.md版本（这些应该已经是正确的）
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            if self.target_version in readme_content:
                self.logger.info(f"README.md版本号正确: {self.target_version}")
            else:
                self.logger.warning(f"README.md中未找到版本号: {self.target_version}")
        
        changelog_path = self.project_root / "CHANGELOG.md"
        if changelog_path.exists():
            with open(changelog_path, 'r', encoding='utf-8') as f:
                changelog_content = f.read()
            if self.target_version in changelog_content:
                self.logger.info(f"CHANGELOG.md版本号正确: {self.target_version}")
            else:
                self.logger.warning(f"CHANGELOG.md中未找到版本号: {self.target_version}")
        
        return results
    
    def verify_version_consistency(self):
        """验证版本一致性"""
        files_to_check = {
            "README.md": self.project_root / "README.md",
            "CHANGELOG.md": self.project_root / "CHANGELOG.md", 
            "src/apppro.py": self.project_root / "src" / "apppro.py"
        }
        
        versions_found = {}
        
        for file_name, file_path in files_to_check.items():
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找版本号
                version_matches = re.findall(r'v?(\d+\.\d+\.\d+)', content)
                if version_matches:
                    versions_found[file_name] = version_matches[0]
        
        # 检查一致性
        unique_versions = set(versions_found.values())
        
        if len(unique_versions) == 1:
            self.logger.info(f"✅ 版本一致性验证通过: {list(unique_versions)[0]}")
            return True, list(unique_versions)[0]
        else:
            self.logger.warning(f"❌ 版本不一致: {versions_found}")
            return False, versions_found

def main():
    """主函数"""
    print("🔄 RAG Pro Max 版本统一工具")
    print("=" * 50)
    
    # 从README.md获取目标版本
    readme_path = Path("README.md")
    target_version = "2.4.7"  # 默认版本
    
    if readme_path.exists():
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        version_match = re.search(r'version-v(\d+\.\d+\.\d+)', content)
        if version_match:
            target_version = version_match.group(1)
    
    print(f"🎯 目标版本: {target_version}")
    
    # 初始化版本统一器
    unifier = VersionUnifier(target_version=target_version)
    
    try:
        # 检查当前版本一致性
        print("\n🔍 检查当前版本一致性...")
        is_consistent, current_versions = unifier.verify_version_consistency()
        
        if not is_consistent:
            print("⚠️  发现版本不一致，开始统一...")
            
            # 执行版本统一
            results = unifier.update_all_versions()
            
            print(f"\n📊 统一结果:")
            print(f"  - apppro.py 更新: {'✅' if results['apppro_updated'] else '❌'}")
            print(f"  - requirements.txt 检查: {'✅' if results['requirements_checked'] else '❌'}")
            print(f"  - 总更新数: {results['total_updates']}")
            
            # 再次验证
            print("\n🔍 重新验证版本一致性...")
            is_consistent, final_versions = unifier.verify_version_consistency()
            
            if is_consistent:
                print(f"✅ 版本统一成功! 当前版本: {final_versions}")
            else:
                print(f"❌ 版本统一失败，仍存在不一致: {final_versions}")
        else:
            print(f"✅ 版本已经一致: {current_versions}")
        
    except Exception as e:
        print(f"❌ 版本统一失败: {e}")
        logging.error(f"版本统一失败: {e}", exc_info=True)

if __name__ == "__main__":
    main()
