import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Fix the model variable shadowing which is destroying instantiation
patch = """                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else custom_key
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

content = re.sub(
    r"                            api_key = model_info\.get\('api_key'\) if isinstance\(model_info, dict\) else custom_key.*?default_model=model\n                            \)",
    patch,
    content,
    flags=re.DOTALL
)

with open("src/router/core.py", "w") as f:
    f.write(content)

