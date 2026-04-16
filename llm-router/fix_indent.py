with open("src/router/core.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == "def load_configured_models(self):":
        # Check current indentation
        current_indent = len(line) - len(line.lstrip())
        print(f"Line {i} indent: {current_indent}")
        break

