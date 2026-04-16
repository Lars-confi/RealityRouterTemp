import re
with open("src/router/core.py", "r") as f:
    content = f.read()

# I see what's happening. The base_url when passed to GenericOpenAIAdapter via model_info is STILL holding onto
# an old value or stripping /v1 somehow during the HTTPX pass, or the router itself is sending 404
# wait, the logs say: HTTP Request: POST http://100.81.4.19:11434/chat/completions "HTTP/1.1 404 Not Found"
# Notice there is NO /v1 in the log!! 
# That means GenericOpenAIAdapter didn't keep the /v1.

patch = """        if self.base_url.endswith("/v1/") or self.base_url.endswith("/v1"):
            base = self.base_url
        else:
            if "11434" in self.base_url:
                base = self.base_url + "/v1" if not self.base_url.endswith("/") else self.base_url + "v1"
            else:
                base = self.base_url"""

with open("src/adapters/generic_openai_adapter.py", "r") as f:
    generic = f.read()

if "11434" not in generic:
    generic = generic.replace("base_url=self.base_url", patch + "\n\n        self.client = openai.AsyncOpenAI(\n            api_key=self.api_key,\n            base_url=base\n        )")
    with open("src/adapters/generic_openai_adapter.py", "w") as f:
        f.write(generic)
        
