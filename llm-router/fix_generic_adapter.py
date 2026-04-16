import re

with open("src/adapters/generic_openai_adapter.py", "r") as f:
    content = f.read()

# Make sure the base_url is parsed right for OpenAI compat
bad_str = """        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )"""

good_str = """        if self.base_url.endswith("/v1/") or self.base_url.endswith("/v1"):
            base = self.base_url
        else:
            if "11434" in self.base_url:
                base = self.base_url + "/v1" if not self.base_url.endswith("/") else self.base_url + "v1"
            else:
                base = self.base_url

        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base
        )"""

content = content.replace(bad_str, good_str)

with open("src/adapters/generic_openai_adapter.py", "w") as f:
    f.write(content)
