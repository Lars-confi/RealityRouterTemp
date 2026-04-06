"""
Configuration management for LLM routing system
"""
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Settings(BaseModel):
    """Application settings"""
    
    # Application settings
    app_name: str = Field(default="LLM Router", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./llm_router.db", env="DATABASE_URL")
    
    # API keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")
    
    # Routing settings
    default_strategy: str = Field(default="expected_utility", env="DEFAULT_STRATEGY")
    reward: float = Field(default=1.0, env="REWARD")
    cost_sensitivity: float = Field(default=0.5, env="COST_SENSITIVITY")
    time_sensitivity: float = Field(default=0.5, env="TIME_SENSITIVITY")
    
    # Model settings
    models_config: Dict[str, Any] = Field(default_factory=dict, env="MODELS_CONFIG")
    
    # Load balancing settings
    load_balancing_strategy: str = Field(default="weighted", env="LOAD_BALANCING_STRATEGY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def load_models_from_config() -> Dict[str, Dict[str, Any]]:
    """Load model configurations from settings"""
    models = {}
    
    # Load from environment variables or default configuration
    if settings.models_config:
        models.update(settings.models_config)
    else:
        # Default models configuration
        models = {
            "openai_gpt-3.5-turbo": {
                "name": "OpenAI GPT-3.5 Turbo",
                "provider": "openai",
                "cost": 0.002,  # $0.002 per million tokens
                "time": 0.5,     # seconds
                "probability": 0.9,
                "weight": 1.0
            },
            "anthropic_claude-haiku": {
                "name": "Anthropic Claude Haiku",
                "provider": "anthropic",
                "cost": 0.00025,  # $0.25 per million tokens
                "time": 0.8,      # seconds
                "probability": 0.85,
                "weight": 1.0
            },
            "cohere_command-r-plus": {
                "name": "Cohere Command R+",
                "provider": "cohere",
                "cost": 0.001,   # $1.00 per million tokens
                "time": 1.0,     # seconds
                "probability": 0.8,
                "weight": 1.0
            }
        }
    
    logger.info(f"Loaded {len(models)} models from configuration")
    return models