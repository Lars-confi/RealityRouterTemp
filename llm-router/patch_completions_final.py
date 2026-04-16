with open("src/router/core.py", "r") as f:
    content = f.read()

# Fix the routing bug one more time
content = content.replace("adapter_key = decision.model_id.split('_')[0]", "adapter_key = decision.model_id.split('_')[0]\n                model_id = decision.model_id")

with open("src/router/core.py", "w") as f:
    f.write(content)
