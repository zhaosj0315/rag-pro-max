"""
配置模块测试
Stage 8 - 测试配置加载器和验证器
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch, Mock
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.config_loader import ConfigLoader
from src.config.config_validator import ConfigValidator


class TestConfigLoader(unittest.TestCase):
    """测试配置加载器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_config_file = ConfigLoader.CONFIG_FILE
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")
        ConfigLoader.CONFIG_FILE = self.test_config_file
    
    def tearDown(self):
        """测试后清理"""
        ConfigLoader.CONFIG_FILE = self.original_config_file
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        os.rmdir(self.temp_dir)
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        config = ConfigLoader.load()
        self.assertIsInstance(config, dict)
        self.assertIn('llm_provider', config)
        self.assertIn('embed_provider_idx', config)
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        test_config = {
            'llm_provider': 'OpenAI',
            'llm_model_openai': 'gpt-4'
        }
        
        success = ConfigLoader.save(test_config)
        self.assertTrue(success)
        
        loaded_config = ConfigLoader.load()
        self.assertEqual(loaded_config['llm_provider'], 'OpenAI')
        self.assertEqual(loaded_config['llm_model_openai'], 'gpt-4')
    
    def test_get_default(self):
        """测试获取默认值"""
        value = ConfigLoader.get_default('llm_provider')
        self.assertEqual(value, 'Ollama')
        
        value = ConfigLoader.get_default('nonexistent_key', 'default_value')
        self.assertEqual(value, 'default_value')
    
    def test_quick_setup(self):
        """测试快速配置"""
        config = ConfigLoader.quick_setup()
        self.assertEqual(config['llm_provider'], 'Ollama')
        self.assertEqual(config['embed_provider_idx'], 0)
    
    def test_update_config(self):
        """测试更新配置"""
        # 先保存初始配置
        initial_config = {'llm_provider': 'Ollama'}
        ConfigLoader.save(initial_config)
        
        # 更新配置
        updates = {'llm_model_ollama': 'qwen2.5:14b'}
        updated_config = ConfigLoader.update(updates)
        
        self.assertEqual(updated_config['llm_model_ollama'], 'qwen2.5:14b')
        self.assertEqual(updated_config['llm_provider'], 'Ollama')
    
    def test_get_llm_config_ollama(self):
        """测试提取 Ollama LLM 配置"""
        config = {
            'llm_provider': 'Ollama',
            'llm_url_ollama': 'http://localhost:11434',
            'llm_model_ollama': 'qwen2.5:7b',
            'llm_temperature': 0.7
        }
        
        llm_config = ConfigLoader.get_llm_config(config)
        self.assertEqual(llm_config['provider'], 'Ollama')
        self.assertEqual(llm_config['model'], 'qwen2.5:7b')
        self.assertEqual(llm_config['temperature'], 0.7)
    
    def test_get_llm_config_openai(self):
        """测试提取 OpenAI LLM 配置"""
        config = {
            'llm_provider': 'OpenAI',
            'llm_url_openai': 'https://api.openai.com/v1',
            'llm_model_openai': 'gpt-4',
            'llm_key_openai': 'sk-test',
            'llm_temperature': 0.5
        }
        
        llm_config = ConfigLoader.get_llm_config(config)
        self.assertEqual(llm_config['provider'], 'OpenAI')
        self.assertEqual(llm_config['model'], 'gpt-4')
        self.assertEqual(llm_config['key'], 'sk-test')
    
    def test_get_embed_config_huggingface(self):
        """测试提取 HuggingFace 嵌入配置"""
        config = {
            'embed_provider_idx': 0,
            'embed_model_hf': 'BAAI/bge-small-zh-v1.5'
        }
        
        embed_config = ConfigLoader.get_embed_config(config)
        self.assertEqual(embed_config['provider'], 'HuggingFace')
        self.assertEqual(embed_config['model'], 'BAAI/bge-small-zh-v1.5')


class TestConfigValidator(unittest.TestCase):
    """测试配置验证器"""
    
    def test_validate_llm_config_empty_provider(self):
        """测试验证空提供商"""
        config = {}
        valid, error = ConfigValidator.validate_llm_config(config)
        self.assertFalse(valid)
        self.assertIn('未指定', error)
    
    def test_validate_llm_config_ollama_missing_url(self):
        """测试验证 Ollama 缺少 URL"""
        config = {'provider': 'Ollama', 'model': 'qwen2.5:7b'}
        valid, error = ConfigValidator.validate_llm_config(config)
        self.assertFalse(valid)
        self.assertIn('URL', error)
    
    def test_validate_llm_config_openai_missing_key(self):
        """测试验证 OpenAI 缺少 Key"""
        config = {
            'provider': 'OpenAI',
            'url': 'https://api.openai.com/v1',
            'model': 'gpt-4'
        }
        valid, error = ConfigValidator.validate_llm_config(config)
        self.assertFalse(valid)
        self.assertIn('Key', error)
    
    def test_validate_embed_config_huggingface(self):
        """测试验证 HuggingFace 嵌入配置"""
        config = {
            'provider': 'HuggingFace',
            'model': 'BAAI/bge-small-zh-v1.5'
        }
        valid, error = ConfigValidator.validate_embed_config(config)
        self.assertTrue(valid)
        self.assertEqual(error, '')
    
    def test_validate_path_empty(self):
        """测试验证空路径"""
        valid, error = ConfigValidator.validate_path('')
        self.assertFalse(valid)
        self.assertIn('不能为空', error)
    
    def test_validate_path_nonexistent(self):
        """测试验证不存在的路径"""
        valid, error = ConfigValidator.validate_path('/nonexistent/path')
        self.assertFalse(valid)
        self.assertIn('不存在', error)
    
    def test_validate_path_valid(self):
        """测试验证有效路径"""
        valid, error = ConfigValidator.validate_path(os.getcwd())
        self.assertTrue(valid)
        self.assertEqual(error, '')
    
    def test_validate_kb_name_empty(self):
        """测试验证空知识库名称"""
        valid, error = ConfigValidator.validate_kb_name('')
        self.assertFalse(valid)
        self.assertIn('不能为空', error)
    
    def test_validate_kb_name_too_long(self):
        """测试验证过长的知识库名称"""
        long_name = 'a' * 51
        valid, error = ConfigValidator.validate_kb_name(long_name)
        self.assertFalse(valid)
        self.assertIn('过长', error)
    
    def test_validate_kb_name_invalid_chars(self):
        """测试验证包含非法字符的知识库名称"""
        invalid_names = ['test/kb', 'test\\kb', 'test:kb', 'test*kb']
        for name in invalid_names:
            valid, error = ConfigValidator.validate_kb_name(name)
            self.assertFalse(valid)
            self.assertIn('非法字符', error)
    
    def test_validate_kb_name_valid(self):
        """测试验证有效的知识库名称"""
        valid, error = ConfigValidator.validate_kb_name('my_knowledge_base')
        self.assertTrue(valid)
        self.assertEqual(error, '')
    
    def test_validate_temperature_invalid_type(self):
        """测试验证无效类型的温度"""
        valid, error = ConfigValidator.validate_temperature('invalid')
        self.assertFalse(valid)
        self.assertIn('数字', error)
    
    def test_validate_temperature_out_of_range(self):
        """测试验证超出范围的温度"""
        valid, error = ConfigValidator.validate_temperature(3.0)
        self.assertFalse(valid)
        self.assertIn('0-2', error)
        
        valid, error = ConfigValidator.validate_temperature(-0.5)
        self.assertFalse(valid)
        self.assertIn('0-2', error)
    
    def test_validate_temperature_valid(self):
        """测试验证有效的温度"""
        valid, error = ConfigValidator.validate_temperature(0.7)
        self.assertTrue(valid)
        self.assertEqual(error, '')


if __name__ == '__main__':
    unittest.main()
