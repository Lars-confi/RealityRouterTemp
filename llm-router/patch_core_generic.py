import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# 1. Update load_configured_models
old_load = """                self.load_balancer.add_model(
                    model_id=model_id,
                    model_name=model_info.get('name', model_id),
                    weight=weight
                )"""

new_load = """                self.load_balancer.add_model(
                    model_id=model_id,
                    model_name=model_info.get('name', model_id),
                    weight=weight
                )
                
                # Dynamic adapter registration for generic models
                provider = model_info.get('provider', model_id.split('_')[0])
                if provider == 'generic':
                    from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                    self.adapters[model_id] = GenericOpenAIAdapter(
                        model_name=model_info.get('name', model_id),
                        api_key=model_info.get('api_key'),
                        base_url=model_info.get('base_url'),
                        default_model=model_info.get('model')
                    )"""

content = content.replace(old_load, new_load)

# 2. Update get_ranked_models
old_get_adapter1 = "adapter = self.adapters.get(adapter_key)"
new_get_adapter1 = "adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)"
content = content.replace(old_get_adapter1, new_get_adapter1)

# 3. Update route_request
old_get_adapter2 = "adapter = self.adapters.get(adapter_key)"
new_get_adapter2 = "adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)"
content = content.replace(old_get_adapter2, new_get_adapter2)

with open("src/router/core.py", "w") as f:
    f.write(content)

