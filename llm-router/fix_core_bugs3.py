with open("src/router/core.py", "r") as f:
    content = f.read()

bad_completions = """        # Convert standard request to internal routing request
        routing_request = RoutingRequest(
            query=request.messages[-1]['content'] if request.messages else "",
            parameters={
                "prompt": request.messages[-1]['content'] if request.messages else "",
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "model": request.model
            }
        )"""

good_completions = """        # Convert standard request to internal routing request
        query_text = ""
        if request.messages:
            last_content = request.messages[-1].get('content', '')
            if isinstance(last_content, str):
                query_text = last_content
            elif isinstance(last_content, list) and len(last_content) > 0:
                query_text = str(last_content[0].get('text', ''))
                
        routing_request = RoutingRequest(
            query=query_text,
            parameters={
                "prompt": query_text,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "model": request.model
            }
        )"""

content = content.replace(bad_completions, good_completions)

with open("src/router/core.py", "w") as f:
    f.write(content)
