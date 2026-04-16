with open("src/router/core.py", "r") as f:
    content = f.read()

bad_str = """        # We will populate these lazily based on config"""
good_str = """        self.adapters = {}"""

content = content.replace(bad_str, good_str)

with open("src/router/core.py", "w") as f:
    f.write(content)
