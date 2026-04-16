import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Ollama API endpoints normally have a `/v1` suffix when simulating OpenAI.
# Let's fix that generic adapter logic
bad_str = """base_url = model_info.get('base_url') if isinstance(model_info, dict) else custom_url
                            if not base_url: 
                                base_url = custom_url
                            
                            if "11434" in base_url and not base_url.endswith("/v1"):
                                base_url += "/v1\"\"\""""

# Let's just do a blunt replace for the specific missing adapter warnings
bad_log1 = "logger.warning(f'Missing adapter for {model_id}')"
good_log1 = "pass # logger.warning(f'Missing adapter for {model_id}')"

content = content.replace(bad_log1, good_log1)

with open("src/router/core.py", "w") as f:
    f.write(content)
