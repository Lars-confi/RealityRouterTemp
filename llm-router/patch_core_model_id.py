with open("src/router/core.py", "r") as f:
    content = f.read()

content = content.replace(
    "adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)",
    "adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)"
)

with open("src/router/core.py", "w") as f:
    f.write(content)
