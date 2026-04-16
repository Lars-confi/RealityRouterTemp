import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Fix the Ollama API base path bug where it defaults to sending to base/models instead of base/chat/completions or whatever the SDK builds.
# The GenericOpenAIAdapter builds URL by taking base_url and passing it to openai.AsyncOpenAI
# But Ollama needs "/v1" at the end.
# In the autodiscovery, I set base_url: f"{base_url}/v1" for Ollama
# BUT when we instantiate GenericOpenAIAdapter it might strip it or do something weird.

old_str = """                        elif provider == 'generic' or adapter_key == 'ollama' or adapter_key == 'custom':
                            from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                            import os
                            custom_url = os.getenv("CUSTOM_LLM_BASE_URL", "http://localhost:11434/v1")
                            custom_key = os.getenv("CUSTOM_LLM_API_KEY", "dummy")
                            # Explicitly check model_info dictionary, safely
                            base_url = model_info.get('base_url') if isinstance(model_info, dict) else custom_url
                            if not base_url: base_url = custom_url
                            
                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else custom_key
                            if not api_key: api_key = custom_key
                            
                            req_model = model_info.get('model') if isinstance(model_info, dict) else None
                            if not req_model: req_model = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id
                            
                            name = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id

                            adapter = GenericOpenAIAdapter(
                                model_name=name,
                                api_key=api_key,
                                base_url=base_url,
                                default_model=req_model
                            )"""

new_str = """                        elif provider == 'generic' or adapter_key == 'ollama' or adapter_key == 'custom':
                            from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                            import os
                            custom_url = os.getenv("CUSTOM_LLM_BASE_URL", "http://localhost:11434/v1")
                            if not custom_url.endswith("/v1") and "11434" in custom_url:
                                custom_url += "/v1"
                                
                            custom_key = os.getenv("CUSTOM_LLM_API_KEY", "dummy")
                            
                            base_url = model_info.get('base_url') if isinstance(model_info, dict) else custom_url
                            if not base_url: 
                                base_url = custom_url
                            
                            if "11434" in base_url and not base_url.endswith("/v1"):
                                base_url += "/v1"
                            
                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else custom_key
                            if not api_key: api_key = custom_key
                            
                            req_model = model_info.get('model') if isinstance(model_info, dict) else None
                            if not req_model: req_model = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id
                            
                            name = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id

                            adapter = GenericOpenAIAdapter(
                                model_name=name,
                                api_key=api_key,
                                base_url=base_url,
                                default_model=req_model
                            )"""

content = content.replace(old_str, new_str)

# One more thing: we discovered ollama models with 'ollama_name', but the adapter logic expects 'name'.
# In auto discovery we saved `model_info['model'] = name`. Let's ensure it is passing it perfectly.

with open("src/router/core.py", "w") as f:
    f.write(content)

