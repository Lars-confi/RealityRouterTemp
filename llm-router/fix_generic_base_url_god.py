import re
with open("src/router/core.py", "r") as f:
    content = f.read()

# Let's see how the base_url is being handled in load_models dynamically
old_lazy = """                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else custom_key
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

new_lazy = """                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else custom_key
                            if not api_key: api_key = custom_key
                            
                            req_model = model_info.get('model') if isinstance(model_info, dict) else None
                            if not req_model: req_model = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id
                            
                            name = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id

                            adapter = GenericOpenAIAdapter(
                                model_name=name,
                                api_key=api_key,
                                base_url=base_url if "11434" not in base_url else (base_url.rstrip("/") + "/v1" if not base_url.endswith("v1") else base_url),
                                default_model=req_model
                            )"""

content = content.replace(old_lazy, new_lazy)

with open("src/router/core.py", "w") as f:
    f.write(content)
