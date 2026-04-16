import re

# Update __init__.py
with open("src/adapters/__init__.py", "r") as f:
    init_content = f.read()
if "GeminiAdapter" not in init_content:
    init_content = init_content.replace(
        "from .huggingface_adapter import HuggingFaceAdapter",
        "from .huggingface_adapter import HuggingFaceAdapter\nfrom .gemini_adapter import GeminiAdapter"
    )
    init_content = init_content.replace(
        "'HuggingFaceAdapter'",
        "'HuggingFaceAdapter',\n    'GeminiAdapter'"
    )
    with open("src/adapters/__init__.py", "w") as f:
        f.write(init_content)

# Update core.py to inject gemini
with open("src/router/core.py", "r") as f:
    core_content = f.read()

if "from src.adapters.gemini_adapter import GeminiAdapter" not in core_content:
    core_content = core_content.replace(
        "from src.adapters.huggingface_adapter import HuggingFaceAdapter",
        "from src.adapters.huggingface_adapter import HuggingFaceAdapter\nfrom src.adapters.gemini_adapter import GeminiAdapter"
    )
    
if "'gemini': GeminiAdapter()" not in core_content:
    core_content = core_content.replace(
        "'huggingface': HuggingFaceAdapter(),",
        "'huggingface': HuggingFaceAdapter(),\n            'gemini': GeminiAdapter(),"
    )
    with open("src/router/core.py", "w") as f:
        f.write(core_content)

