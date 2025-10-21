"""
Tests for Configuration Manager
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_manager import ConfigManager, ConfigurationError, AppConfig


class TestConfigManager:
    """Test configuration manager functionality"""
    
    def test_load_existing_config(self):
        """Test loading existing configuration file"""
        config_manager = ConfigManager("config/config.yaml")
        config = config_manager.load_config()
        
        assert config is not None
        assert isinstance(config, AppConfig)
        assert config.llm.provider in ['ollama', 'llamacpp']
        assert config.database.type == 'sqlite'
    
    def test_generate_default_config(self):
        """Test generating default configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.yaml")
            config_manager = ConfigManager(config_path)
            
            # Generate default config
            config_manager.generate_default_config()
            
            # Verify file was created
            assert os.path.exists(config_path)
            
            # Load and verify
            config = config_manager.load_config()
            assert config is not None
            assert config.llm.model_name == "llama3"
    
    def test_validate_config(self):
        """Test configuration validation"""
        config_manager = ConfigManager("config/config.yaml")
        config = config_manager.load_config()
        
        # Should not raise exception for valid config
        config_manager.validate_config()
    
    def test_invalid_llm_provider(self):
        """Test validation fails for invalid LLM provider"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.yaml")
            config_manager = ConfigManager(config_path)
            config_manager.generate_default_config()
            
            # Load config
            config = config_manager.load_config()
            
            # Modify to invalid provider
            config.llm.provider = "invalid_provider"
            config_manager.config = config
            
            # Should raise ConfigurationError
            with pytest.raises(ConfigurationError):
                config_manager.validate_config()
    
    def test_get_config_before_load(self):
        """Test getting config before loading raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.yaml")
            config_manager = ConfigManager(config_path)
            
            with pytest.raises(ConfigurationError):
                config_manager.get_config()
    
    def test_config_dataclasses(self):
        """Test configuration dataclass structure"""
        config_manager = ConfigManager("config/config.yaml")
        config = config_manager.load_config()
        
        # Test LLM config
        assert hasattr(config.llm, 'provider')
        assert hasattr(config.llm, 'model_name')
        assert hasattr(config.llm, 'temperature')
        
        # Test job search config
        assert hasattr(config.job_search, 'keywords')
        assert hasattr(config.job_search, 'min_salary')
        assert isinstance(config.job_search.keywords, list)
        
        # Test database config
        assert hasattr(config.database, 'type')
        assert hasattr(config.database, 'path')
        
        # Test notification config
        assert hasattr(config.notifications, 'email')
        assert hasattr(config.notifications, 'whatsapp')
        assert hasattr(config.notifications.email, 'enabled')
        
        # Test scoring config
        assert hasattr(config.scoring, 'skills_match_weight')
        total_weight = (
            config.scoring.skills_match_weight +
            config.scoring.salary_match_weight +
            config.scoring.tech_stack_match_weight +
            config.scoring.remote_flexibility_weight +
            config.scoring.company_profile_weight
        )
        assert abs(total_weight - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
