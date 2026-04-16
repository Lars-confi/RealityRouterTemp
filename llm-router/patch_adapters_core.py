with open("src/router/core.py", "r") as f:
    content = f.read()

bad_init = """        self.adapters = {
            'openai': OpenAIAdapter(),
            'anthropic': AnthropicAdapter(),
            'cohere': CohereAdapter(),
            'huggingface': HuggingFaceAdapter(),
            'gemini': GeminiAdapter(),
            'generic': GenericOpenAIAdapter()
        }"""

good_init = """        self.adapters = {}
        # We will populate these lazily based on config"""

content = content.replace(bad_init, good_init)

with open("src/router/core.py", "w") as f:
    f.write(content)
