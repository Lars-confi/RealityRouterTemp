with open("src/adapters/generic_openai_adapter.py", "r") as f:
    content = f.read()

# Let's completely force the issue in the adapter. 
# If the user typed "100.81.4.19:11434" the openai SDK MIGHT be stripping the /v1
# We need to ensure we initialize AsyncOpenAI with the exact url

good_init = """        base = self.base_url
        if "11434" in base and not base.endswith("v1"):
            base = base.rstrip("/") + "/v1"
            
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base
        )"""

import re
content = re.sub(
    r'        if self\.base_url\.endswith.*?base_url=base\n        \)',
    good_init,
    content,
    flags=re.DOTALL
)

with open("src/adapters/generic_openai_adapter.py", "w") as f:
    f.write(content)

