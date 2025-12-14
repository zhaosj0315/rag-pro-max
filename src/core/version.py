"""
统一版本管理模块
确保所有文件使用一致的版本信息
"""

import os
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

def get_version_info():
    """获取版本信息"""
    version_file = PROJECT_ROOT / "version.json"
    
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # 默认版本信息
        return {
            "version": "2.3.1",
            "release_date": "2025-12-14",
            "codename": "安全增强版"
        }

def get_version():
    """获取版本号"""
    return get_version_info().get("version", "2.3.1")

def get_version_tag():
    """获取版本标签"""
    return f"v{get_version()}"

def get_codename():
    """获取版本代号"""
    return get_version_info().get("codename", "安全增强版")

def get_release_date():
    """获取发布日期"""
    return get_version_info().get("release_date", "2025-12-14")

# 版本常量
VERSION = get_version()
VERSION_TAG = get_version_tag()
CODENAME = get_codename()
RELEASE_DATE = get_release_date()

# 完整版本信息
FULL_VERSION_INFO = f"RAG Pro Max {VERSION_TAG} - {CODENAME}"
