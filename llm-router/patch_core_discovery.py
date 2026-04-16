import re

with open("src/router/core.py", "r") as f:
    content = f.read()

new_method = """    def load_configured_models(self):
        \"\"\"Load models from configuration and dynamically discover them\"\"\"
        try:
            import os
            import requests
            
            # Load static user models if any
            config_models = load_models_from_config()
            for model_id, model_info in config_models.items():
                self.add_model(
                    model_id=model_id,
                    model_name=model_info.get('name', model_id),
                    cost=model_info.get('cost', 0.0),
                    time=model_info.get('time', 1.0),
                    probability=model_info.get('probability', 0.8)
                )
                self.load_balancer.add_model(model_id, model_info.get('name', model_id), 1.0)
                provider = model_info.get('provider', model_id.split('_')[0])
                if provider == 'generic':
                    from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                    self.adapters[model_id] = GenericOpenAIAdapter(
                        model_name=model_info.get('name', model_id),
                        api_key=model_info.get('api_key'),
                        base_url=model_info.get('base_url'),
                        default_model=model_info.get('model')
                    )

            # Auto-Discover Dynamic Models
            logger.info("Auto-discovering models from configured providers...")
            
            # 1. Custom/Local Models (Ollama or Generic)
            custom_url = os.getenv("CUSTOM_LLM_BASE_URL")
            custom_key = os.getenv("CUSTOM_LLM_API_KEY", "dummy")
            if custom_url:
                try:
                    if "11434" in custom_url:  # Ollama
                        ollama_url = custom_url.replace("/v1", "/api/tags") if custom_url.endswith("/v1") else f"{custom_url}/api/tags"
                        resp = requests.get(ollama_url, timeout=3)
                        if resp.status_code == 200:
                            for m in resp.json().get("models", []):
                                name = m.get("name")
                                if name:
                                    mid = f"ollama_{name.replace(':', '-')}"
                                    if mid not in self.models:
                                        self.add_model(mid, name, 0.0, 1.0, 0.8)
                                        self.load_balancer.add_model(mid, name, 1.0)
                                        from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                                        self.adapters[mid] = GenericOpenAIAdapter(name, custom_key, custom_url, name)
                    else:  # Generic OpenAI Compatible
                        resp = requests.get(f"{custom_url}/models", headers={"Authorization": f"Bearer {custom_key}"}, timeout=3)
                        if resp.status_code == 200:
                            for m in resp.json().get("data", []):
                                name = m.get("id")
                                if name:
                                    mid = f"custom_{name.replace(':', '-').replace('.', '-')}"
                                    if mid not in self.models:
                                        self.add_model(mid, name, 0.001, 1.0, 0.8)
                                        self.load_balancer.add_model(mid, name, 1.0)
                                        from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                                        self.adapters[mid] = GenericOpenAIAdapter(name, custom_key, custom_url, name)
                except Exception as e:
                    logger.warning(f"Auto-discovery failed for custom URL {custom_url}: {e}")

            # 2. OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key and openai_key != "dummy" and openai_key != "sk-dummy":
                try:
                    resp = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {openai_key}"}, timeout=3)
                    if resp.status_code == 200:
                        for m in resp.json().get("data", []):
                            name = m.get("id")
                            if "gpt" in name or "o1" in name:
                                mid = f"openai_{name.replace('.', '-')}"
                                if mid not in self.models:
                                    cost = 0.01 if "gpt-4" in name else 0.002
                                    prob = 0.95 if "gpt-4" in name else 0.9
                                    self.add_model(mid, name, cost, 0.5, prob)
                                    self.load_balancer.add_model(mid, name, 1.0)
                except Exception as e:
                    logger.warning(f"Auto-discovery failed for OpenAI: {e}")

            # 3. Gemini
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key and gemini_key != "dummy":
                try:
                    resp = requests.get("https://generativelanguage.googleapis.com/v1beta/openai/models", headers={"Authorization": f"Bearer {gemini_key}"}, timeout=3)
                    if resp.status_code == 200:
                        for m in resp.json().get("data", []):
                            name = m.get("id")
                            mid = f"gemini_{name.replace('.', '-')}"
                            if mid not in self.models:
                                self.add_model(mid, name, 0.00035, 0.4, 0.88)
                                self.load_balancer.add_model(mid, name, 1.0)
                except Exception as e:
                    logger.warning(f"Auto-discovery failed for Gemini: {e}")
                    
            logger.info(f"Total configured and discovered models: {len(self.models)}")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            self.add_default_models()"""

# Replace the old load_configured_models method carefully
start_idx = content.find("    def load_configured_models(self):")
end_idx = content.find("    def add_default_models(self):")
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_method + "\n\n" + content[end_idx:]

with open("src/router/core.py", "w") as f:
    f.write(content)
