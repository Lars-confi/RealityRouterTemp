with open("src/router/core.py", "r") as f:
    lines = f.readlines()

for i in range(109, 210):
    if lines[i].startswith("def load_configured_models(self):"):
        lines[i] = "    " + lines[i]

with open("src/router/core.py", "w") as f:
    f.writelines(lines)
