import re

with open("llm-router/src/router/core.py", "r") as f:
    content = f.read()

estimate_func = """
    def _estimate_tokens(self, request: RoutingRequest) -> int:
        \"\"\"Estimate the number of tokens in the request.\"\"\"
        total_chars = 0
        if request.query:
            total_chars += len(request.query)
            
        if request.parameters and "messages" in request.parameters:
            for msg in request.parameters["messages"]:
                content = msg.get("content", "")
                if isinstance(content, str):
                    total_chars += len(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            total_chars += len(item.get("text", ""))
                            
        return total_chars // 4

    async def get_ranked_models("""

content = content.replace("    async def get_ranked_models(", estimate_func)

with open("llm-router/src/router/core.py", "w") as f:
    f.write(content)
