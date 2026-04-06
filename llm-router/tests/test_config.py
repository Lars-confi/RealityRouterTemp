"""
Test cases for configuration manager
"""
import pytest
import os
from src.config.settings import Settings, get_settings, load_models_from_config

def test_settings_initialization():
    """Test settings initialization"""
    settings = Settings()
    assert settings is not None
    assert hasattr(settings, 'app_name')
    assert hasattr(settings, 'debug')
    assert hasattr(settings, 'database_url')

def test_get_settings():
    """Test getting settings instance"""
    settings = get_settings()
    assert settings is not None
    assert isinstance(settings, Settings)

def test_load_models_from_config():
    """Test loading models from configuration"""
    models = load_models_from_config()
    assert isinstance(models, dict)
    assert len(models) > 0
    
    # Check that models have required fields
    for model_id, model_info in models.items():
        assert 'name' in model_info
        assert 'provider' in model_info
        assert 'cost' in model_info
        assert 'time' in model_info
        assert 'probability' in model_info

def test_default_models():
    """Test that default models are loaded"""
    models = load_models_from_config()
    
    # Check that we have at least the default models
    assert 'openai_gpt-3.5-turbo' in models
    assert 'anthropic_claude-haiku' in models
    assert 'cohere_command-r-plus' in models
    
    # Check that models have correct structure
    openai_model = models['openai_gpt-3.5-turbo']
    assert openai_model['name'] == 'OpenAI GPT-3.5 Turbo'
    assert openai_model['provider'] == 'openai'
    assert openai_model['cost'] > 0
    assert openai_model['time'] > 0
    assert 0 <= openai_model['probability'] <= 1

if __name__ == "__main__":
    pytest.main([__file__])