with open("src/router/core.py", "r") as f:
    content = f.read()

# Fix the routing bug
content = content.replace("adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)", 
                          "adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)\n                if not adapter: print(f'Missing adapter for {decision.model_id}')")

with open("src/router/core.py", "w") as f:
    f.write(content)
