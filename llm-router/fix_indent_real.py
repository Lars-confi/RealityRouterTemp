with open("src/router/core.py", "r") as f:
    content = f.read()

content = content.replace("\ndef load_configured_models(self):\n", "\n    def load_configured_models(self):\n")

with open("src/router/core.py", "w") as f:
    f.write(content)
