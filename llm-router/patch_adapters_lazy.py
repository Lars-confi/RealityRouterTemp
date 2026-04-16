import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Fix get_ranked_models to properly initialize missing adapters lazy-style
lazy_init = """            for model_id, model_info in self.models.items():
                adapter_key = model_id.split('_')[0]
                adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)
                
                # LAZY INIT IF MISSING
                if not adapter:
                    try:
                        provider = model_info.get('provider', adapter_key)
                        if provider == 'openai' or adapter_key == 'openai':
                            from src.adapters.openai_adapter import OpenAIAdapter
                            adapter = OpenAIAdapter()
                        elif provider == 'anthropic' or adapter_key == 'anthropic':
                            from src.adapters.anthropic_adapter import AnthropicAdapter
                            adapter = AnthropicAdapter()
                        elif provider == 'gemini' or adapter_key == 'gemini':
                            from src.adapters.gemini_adapter import GeminiAdapter
                            adapter = GeminiAdapter()
                        elif provider == 'cohere' or adapter_key == 'cohere':
                            from src.adapters.cohere_adapter import CohereAdapter
                            adapter = CohereAdapter()
                        elif provider == 'generic' or adapter_key == 'ollama' or adapter_key == 'custom':
                            from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                            import os
                            custom_url = os.getenv("CUSTOM_LLM_BASE_URL", "http://localhost:11434/v1")
                            custom_key = os.getenv("CUSTOM_LLM_API_KEY", "dummy")
                            adapter = GenericOpenAIAdapter(
                                model_name=model_info.get('name', model_id),
                                api_key=model_info.get('api_key', custom_key),
                                base_url=model_info.get('base_url', custom_url),
                                default_model=model_info.get('model', model_info.get('name', model_id))
                            )
                        
                        if adapter:
                            self.adapters[model_id] = adapter
                    except Exception as e:
                        logger.warning(f"Could not lazy load adapter for {model_id}: {e}")
                
                cost = model_info.get('cost', 0.0)"""

# replace the loop beginning
content = re.sub(
    r"            for model_id, model_info in self\.models\.items\(\):\n                adapter_key = model_id\.split\('_'\)\[0\]\n                adapter = self\.adapters\.get\(model_id\) or self\.adapters\.get\(adapter_key\)\n                \n                cost = model_info\.get\('cost', 0\.0\)",
    lazy_init,
    content,
    flags=re.DOTALL
)

with open("src/router/core.py", "w") as f:
    f.write(content)

