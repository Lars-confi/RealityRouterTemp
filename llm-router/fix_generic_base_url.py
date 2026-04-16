with open("src/router/core.py", "r") as f:
    content = f.read()

bad_str = """                                        from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                                        self.adapters[mid] = GenericOpenAIAdapter(name, custom_key, custom_url, name)"""

good_str = """                                        from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
                                        self.adapters[mid] = GenericOpenAIAdapter(name, custom_key, custom_url + '/v1' if not custom_url.endswith('/v1') else custom_url, name)"""

content = content.replace(bad_str, good_str)

with open("src/router/core.py", "w") as f:
    f.write(content)
