with open("src/router/core.py", "r") as f:
    content = f.read()

# Replace 8-space indent with 4-space indent for the method
bad_str = "        def load_configured_models(self):\n        \"\"\"Load models from configuration and dynamically discover them\"\"\""
good_str = "    def load_configured_models(self):\n        \"\"\"Load models from configuration and dynamically discover them\"\"\""

content = content.replace(bad_str, good_str)

with open("src/router/core.py", "w") as f:
    f.write(content)
