import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Replace the stray decision.model_id in get_ranked_models that doesn't belong there
bad_str = "if not adapter: print(f'Missing adapter for {decision.model_id}')"
good_str = "if not adapter: logger.warning(f'Missing adapter for {model_id}')"

content = content.replace(bad_str, good_str)

with open("src/router/core.py", "w") as f:
    f.write(content)
