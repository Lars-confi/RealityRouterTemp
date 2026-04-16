import re

with open("src/models/database.py", "r") as f:
    content = f.read()

# Add the two new columns
old_cols = """    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)"""

new_cols = """    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    request_payload = Column(Text)
    response_payload = Column(Text)"""

content = content.replace(old_cols, new_cols)

with open("src/models/database.py", "w") as f:
    f.write(content)
