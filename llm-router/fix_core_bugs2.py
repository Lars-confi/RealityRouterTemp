import re
with open("src/router/core.py", "r") as f:
    content = f.read()

# Make double sure we fixed the NameError in get_ranked_models
bad_str1 = """            for model_id, model_info in self.models.items():
                adapter_key = model_id.split('_')[0]
                adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)"""
good_str1 = """            for model_id, model_info in self.models.items():
                adapter_key = model_id.split('_')[0]
                adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)"""
content = content.replace(bad_str1, good_str1)

with open("src/router/core.py", "w") as f:
    f.write(content)
