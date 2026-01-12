"""
导出管理器 - 对话记录和数据导出
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import streamlit as st

class ExportManager:
    def __init__(self):
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def export_chat_history(self, messages: List[Dict], kb_name: str, format: str = "txt") -> str:
        """导出对话历史"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{kb_name}_{timestamp}.{format}"
        filepath = self.export_dir / filename
        
        if format == "txt":
            return self._export_to_txt(messages, filepath)
        elif format == "json":
            return self._export_to_json(messages, filepath)
        elif format == "csv":
            return self._export_to_csv(messages, filepath)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _export_to_txt(self, messages: List[Dict], filepath: Path) -> str:
        """导出为TXT格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RAG Pro Max 对话记录\n")
            f.write("=" * 50 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"对话数量: {len(messages)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, msg in enumerate(messages, 1):
                role = "用户" if msg["role"] == "user" else "助手"
                f.write(f"[{i}] {role}:\n")
                f.write(f"{msg['content']}\n")
                f.write("-" * 30 + "\n\n")
        
        return str(filepath)
    
    def _export_to_json(self, messages: List[Dict], filepath: Path) -> str:
        """导出为JSON格式"""
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_messages": len(messages),
            "messages": messages
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def _export_to_csv(self, messages: List[Dict], filepath: Path) -> str:
        """导出为CSV格式"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["序号", "角色", "内容", "时间"])
            
            for i, msg in enumerate(messages, 1):
                role = "用户" if msg["role"] == "user" else "助手"
                content = msg["content"].replace('\n', ' ')  # 移除换行符
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([i, role, content, timestamp])
        
        return str(filepath)
    
    def export_kb_statistics(self, kb_name: str, stats: Dict) -> str:
        """导出知识库统计报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kb_stats_{kb_name}_{timestamp}.txt"
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RAG Pro Max 知识库统计报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"知识库名称: {kb_name}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("📊 基本统计:\n")
            f.write(f"  文档数量: {stats.get('document_count', 0)}\n")
            f.write(f"  总页数: {stats.get('total_pages', 0)}\n")
            f.write(f"  文档片段: {stats.get('total_chunks', 0)}\n")
            f.write(f"  总大小: {stats.get('total_size_mb', 0):.1f}MB\n\n")
            
            f.write("📄 文件类型分布:\n")
            file_types = stats.get('file_types', {})
            for file_type, count in file_types.items():
                f.write(f"  {file_type}: {count}个\n")
            
            f.write("\n🔍 查询统计:\n")
            f.write(f"  总查询数: {stats.get('total_queries', 0)}\n")
            f.write(f"  平均响应时间: {stats.get('avg_response_time', 0):.2f}秒\n")
            f.write(f"  查询成功率: {stats.get('success_rate', 0):.1f}%\n")
        
        return str(filepath)
    
    def backup_knowledge_base(self, kb_name: str, kb_path: str) -> str:
        """备份知识库数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"kb_backup_{kb_name}_{timestamp}"
        backup_path = self.export_dir / backup_name
        
        # 创建备份目录
        backup_path.mkdir(exist_ok=True)
        
        # 备份向量数据库
        import shutil
        if Path(kb_path).exists():
            shutil.copytree(kb_path, backup_path / "vector_db", dirs_exist_ok=True)
        
        # 创建备份信息文件
        backup_info = {
            "kb_name": kb_name,
            "backup_time": datetime.now().isoformat(),
            "original_path": kb_path,
            "backup_version": "v5.5.8"
        }
        
        with open(backup_path / "backup_info.json", 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        return str(backup_path)
    
    def get_export_files(self) -> List[Dict]:
        """获取导出文件列表"""
        files = []
        for file_path in self.export_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "type": file_path.suffix[1:] if file_path.suffix else "folder"
                })
        
        # 按创建时间排序
        files.sort(key=lambda x: x["created"], reverse=True)
        return files
    
    def delete_export_file(self, filepath: str) -> bool:
        """删除导出文件"""
        try:
            Path(filepath).unlink()
            return True
        except Exception:
            return False

# 全局导出管理器
export_manager = ExportManager()
