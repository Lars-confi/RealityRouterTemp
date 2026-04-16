import re

with open("src/config/settings.py", "r") as f:
    content = f.read()

new_load_logic = """    # Load from environment variables or default configuration
    import os
    import json
    
    config_path = os.getenv("MODELS_CONFIG_PATH", "../user_models.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_models = json.load(f)
                if user_models:
                    logger.info(f"Loaded models from {config_path}")
                    return user_models
        except Exception as e:
            logger.error(f"Failed to load user models from {config_path}: {e}")
            
    if settings.models_config:"""

content = content.replace("    # Load from environment variables or default configuration\n    if settings.models_config:", new_load_logic)

with open("src/config/settings.py", "w") as f:
    f.write(content)

