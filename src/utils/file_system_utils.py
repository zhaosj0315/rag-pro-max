import os
import stat
import mimetypes
import pathlib
import datetime
import subprocess
import platform
import json
import logging
import hashlib
import binascii
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_deep_file_attributes(file_path: str) -> Dict[str, Any]:
    """获取工业级深度文件属性(增加取证与RAG指标)"""
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    try:
        st = os.stat(file_path)
        p = pathlib.Path(file_path)
        
        # 1. 物理取证：Magic Bytes (文件头指纹)
        magic_hex = "Unknown"
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                magic_hex = binascii.hexlify(header).decode('utf-8').upper()
                magic_hex = " ".join([magic_hex[i:i+2] for i in range(0, len(magic_hex), 2)])
        except: pass

        # 2. 存储效率
        logical_size = st.st_size
        physical_size = getattr(st, 'st_blocks', 0) * 512 if hasattr(st, 'st_blocks') else logical_size
        efficiency = (logical_size / physical_size * 100) if physical_size > 0 else 100

        # 3. RAG 洞察：Token 预估与密度
        # 粗略预估：中文 1:0.6, 英文 1:0.25 (基于一般模型)
        token_estimate = 0
        if logical_size < 10 * 1024 * 1024: # 10MB以内进行分析
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content_sample = f.read(100000) # 读取前10万字
                    token_estimate = len(content_sample) # 基础字符数
            except: pass

        # 4. 文件系统类型 (macOS/Linux)
        fs_type = "Unknown"
        if platform.system() != "Windows":
            try:
                fs_info = subprocess.check_output(["df", "-T", file_path]).decode().split("\n")[1].split()
                fs_type = fs_info[1] # 通常第二列是类型
            except:
                try: # macOS 兼容
                    fs_info = subprocess.check_output(["df", "-t", file_path]).decode().split("\n")[1].split()
                    fs_type = "APFS/HFS+"
                except: pass

        # 5. 指纹与路径
        sha256_hash = hashlib.sha256()
        if logical_size < 100 * 1024 * 1024:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_sha256 = sha256_hash.hexdigest()
        else:
            file_sha256 = "Too large for real-time hash"

        # 6. 时间动力学
        try:
            creation_time = datetime.datetime.fromtimestamp(getattr(st, 'st_birthtime', st.st_ctime))
        except AttributeError:
            creation_time = datetime.datetime.fromtimestamp(st.st_ctime)
        
        longevity_days = (datetime.datetime.now() - creation_time).days

        # 7. macOS 专属元数据 (Spotlight/xattr)
        macos_info = {}
        if platform.system() == "Darwin":
            try:
                # 使用 mdls 获取 JSON 格式的元数据
                # kMDItemUserTags: 标签, kMDItemWhereFroms: 下载来源, kMDItemFinderComment: Finder注释
                cmd = ["mdls", "-json", "-name", "kMDItemUserTags", "-name", "kMDItemWhereFroms", 
                       "-name", "kMDItemFinderComment", "-name", "kMDItemVersion", 
                       "-name", "kMDItemFSLabel", "-name", "kMDItemAuthors", file_path]
                raw_json = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
                md_data = json.loads(raw_json)
                
                macos_info = {
                    "tags": md_data.get("kMDItemUserTags", []),
                    "where_from": md_data.get("kMDItemWhereFroms", []),
                    "finder_comment": md_data.get("kMDItemFinderComment", ""),
                    "version": md_data.get("kMDItemVersion", ""),
                    "label_index": md_data.get("kMDItemFSLabel", 0), # 0-7 对应 Finder 颜色
                    "authors": md_data.get("kMDItemAuthors", [])
                }
                
                # 备选方案：如果 mdls 没拿到 where_from，尝试直接读取 xattr
                if not macos_info["where_from"]:
                    try:
                        import xattr
                        attr_data = xattr.getxattr(file_path, 'com.apple.metadata:kMDItemWhereFroms')
                        # 这里是一个二进制 plist，解析比较复杂，仅尝试捕获是否存在
                        if attr_data:
                            macos_info["where_from"] = ["(存在元数据，建议查看系统简介)"]
                    except: pass
            except: pass

        # 8. 智能内容指纹：从文件头提取 URL (针对爬虫文件)
        header_url = None
        if p.suffix.lower() == '.txt' and logical_size < 1024 * 100: # 提高到100KB以内
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_head:
                    first_line = f_head.readline().strip()
                    # 兼容 "URL: http" 或 "URL:http"
                    if first_line.upper().startswith("URL:"):
                        header_url = first_line[4:].strip()
            except: pass

        return {
            "name": p.name,
            "abs_path": str(p.absolute()),
            "real_path": os.path.realpath(file_path),
            "is_symlink": os.path.islink(file_path),
            # 存储专家
            "logical_size": logical_size,
            "physical_size": physical_size,
            "efficiency": f"{efficiency:.1f}%",
            "fs_type": fs_type,
            "magic_bytes": magic_hex,
            "sha256": file_sha256,
            "inode": st.st_ino,
            # 溯源
            "header_url": header_url,
            # macOS 专属
            "macos": macos_info,
            # RAG 专家
            "token_estimate": token_estimate,
            "longevity_days": longevity_days,
            # 识别
            "mime_type": mimetypes.guess_type(file_path)[0] or "application/octet-stream",
            "extension": p.suffix,
            # 时间轴
            "created": creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "accessed": datetime.datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
            # 权限
            "permissions": stat.filemode(st.st_mode),
            "owner": str(st.st_uid),
            "is_readonly": not os.access(file_path, os.W_OK),
            "is_hidden": p.name.startswith('.')
        }
    except Exception as e:
        return {"error": str(e)}

def reveal_in_file_manager(file_path: str):
    """在文件管理器中定位并显示文件 (跨平台，安全处理)"""
    if not os.path.exists(file_path):
        return False
    
    file_path = os.path.abspath(file_path)
    system = platform.system()
    
    try:
        if system == "Darwin": # macOS
            subprocess.Popen(["open", "-R", file_path])
        elif system == "Windows": # Windows
            # 使用 list 形式防止注入
            subprocess.Popen(["explorer", "/select,", file_path])
        else: # Linux/Unix
            parent_dir = os.path.dirname(file_path)
            subprocess.Popen(["xdg-open", parent_dir])
        return True
    except Exception as e:
        logger.error(f"Failed to reveal file: {e}")
        return False

class NotesManager:
    """管理文件的持久化备注"""
    def __init__(self, storage_path: str = "config/file_notes.json"):
        self.storage_path = storage_path
        self.notes = self._load()
        
    def _load(self) -> Dict[str, str]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load notes: {e}")
        return {}
        
    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Failed to save notes: {e}")
            
    def get_note(self, file_hash: str) -> str:
        return self.notes.get(file_hash, "")
        
    def set_note(self, file_hash: str, note: str):
        self.notes[file_hash] = note
        self._save()

def set_where_from_metadata(file_path: str, url: str):
    """为文件设置 '下载来源' 元数据 (仅限 macOS)"""
    if platform.system() != "Darwin":
        return False
    
    try:
        import xattr
        import plistlib
        
        # macOS 的 kMDItemWhereFroms 是一个二进制 plist 格式的数组
        # 我们构建这个列表并序列化
        urls = [url]
        # 使用 bplist 格式 (macOS 期望的格式)
        plist_data = plistlib.dumps(urls, fmt=plistlib.FMT_BINARY)
        
        xattr.setxattr(file_path, 'com.apple.metadata:kMDItemWhereFroms', plist_data)
        return True
    except Exception as e:
        logger.error(f"Failed to set where_from metadata: {e}")
        return False
