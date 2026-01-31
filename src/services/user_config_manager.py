import os
import json
import shutil
from typing import Dict, Any
from src.services.unified_config_service import load_config, save_config
from src.app_logging import LogManager

logger = LogManager()

class UserConfigManager:
    """
    User-specific configuration manager.
    Handles loading and saving of configurations isolated by username.
    """
    
    USER_CONFIG_DIR = "config/users"
    GLOBAL_CONFIG_NAME = "rag_config"

    @classmethod
    def _get_user_config_path(cls, username: str) -> str:
        """Get the file path for a user's configuration."""
        # Sanitize username to prevent path traversal
        safe_username = "".join([c for c in username if c.isalnum() or c in ('_', '-')])
        return os.path.join(cls.USER_CONFIG_DIR, f"{safe_username}_config.json")

    @classmethod
    def load_user_config(cls, username: str) -> Dict[str, Any]:
        """
        Load configuration for a specific user.
        If user config doesn't exist, fall back to global config.
        """
        if not username:
            return load_config(cls.GLOBAL_CONFIG_NAME)

        user_config_path = cls._get_user_config_path(username)
        
        if os.path.exists(user_config_path):
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config for user {username}: {e}")
                # Fallback to global
                return load_config(cls.GLOBAL_CONFIG_NAME)
        else:
            # If no user config, return global default
            # We don't create the file yet, only when they save
            return load_config(cls.GLOBAL_CONFIG_NAME)

    @classmethod
    def save_user_config(cls, username: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for a specific user.
        """
        if not username:
            return False

        user_config_path = cls._get_user_config_path(username)
        
        try:
            os.makedirs(os.path.dirname(user_config_path), exist_ok=True)
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save config for user {username}: {e}")
            return False

    @classmethod
    def reset_user_config(cls, username: str) -> bool:
        """Reset user config to global defaults"""
        if not username: return False
        path = cls._get_user_config_path(username)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except:
                return False
        return True
