import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Fix the dictionary access which is causing the issue
patch = """                            # Explicitly check model_info dictionary, safely
                            base_url = model_info.get('base_url') if isinstance(model_info, dict) else custom_url
                            if not base_url: base_url = custom_url
                            
                            api_key = model_info.get('api_key') if isinstance(model_info, dict) else custom_key
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
    r"                            # Explicitly check model_info dictionary, safely.*?default_model=model\n                            \)",
    patch,
    content,
    flags=re.DOTALL
)

with open("src/router/core.py", "w") as f:
    f.write(content)

