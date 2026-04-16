with open("src/router/core.py", "r") as f:
    content = f.read()

content = content.replace(
    'class ChatCompletionRequest(BaseModel):',
    '# Global instance\nrouter_core = RouterCore()\n\nclass ChatCompletionRequest(BaseModel):'
)

with open("src/router/core.py", "w") as f:
    f.write(content)
