import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Make sure Generic is imported locally or correctly inside lazy loader
patch = """                        elif provider == 'generic' or adapter_key == 'ollama' or adapter_key == 'custom':
                            from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                            import os
                            custom_url = os.getenv("CUSTOM_LLM_BASE_URL", "http://localhost:11434/v1")
                            custom_key = os.getenv("CUSTOM_LLM_API_KEY", "dummy")
                            # Explicitly check model_info dictionary, safely
                            base_url = model_info.get('base_url') if isinstance(model_info, dict) else None
                            if not base_url: base_url = custom_url
                            
                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else None
                            if not api_key: api_key = custom_key
                            
                            model = model_info.get('model') if isinstance(model_info, dict) else None
                            if not model: model = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id
                            
                            name = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id

                            adapter = GenericOpenAIAdapter(
                                model_name=name,
                                api_key=api_key,
                                base_url=base_url,
                                default_model=model
                            )"""

content = re.sub(
    r"                        elif provider == 'generic' or adapter_key == 'ollama' or adapter_key == 'custom':.*?default_model=model_info\.get\('model', model_info\.get\('name', model_id\)\)\n                            \)",
    patch,
    content,
    flags=re.DOTALL
)

# And fix the route_request one final time just in case
if "response = router_core.route_request" in content:
    content = content.replace("response = router_core.route_request", "response = await router_core.route_request")

with open("src/router/core.py", "w") as f:
    f.write(content)
