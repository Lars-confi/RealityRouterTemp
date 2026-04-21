import re

with open("llm-router/src/router/core.py", "r") as f:
    content = f.read()

# Replace prompt_tokens_est with _estimate_tokens and add total_estimated_tokens
replacement_1 = """            # Estimate prompt tokens (roughly 4 chars per token)
            prompt_tokens_est = len(request.query) / 4 if request.query else 0
            total_estimated_tokens = self._estimate_tokens(request)"""

content = content.replace("            # Estimate prompt tokens (roughly 4 chars per token)\n            prompt_tokens_est = len(request.query) / 4 if request.query else 0", replacement_1)

# Add the tools and token checks in the for loop
replacement_2 = """            tools_requested = request.parameters and request.parameters.get("tools")

            model_tasks = []
            for mid, info in self.models.items():
                if tools_requested and not info.get("supports_function_calling", False):
                    continue
                    
                if info.get("max_input_tokens") and total_estimated_tokens > info["max_input_tokens"]:
                    continue
                if info.get("max_tokens") and total_estimated_tokens > info["max_tokens"]:
                    continue"""

content = content.replace("""            model_tasks = []
            for mid, info in self.models.items():""", replacement_2)

with open("llm-router/src/router/core.py", "w") as f:
    f.write(content)
