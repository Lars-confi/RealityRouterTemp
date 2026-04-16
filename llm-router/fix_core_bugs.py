import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# 1. Fix the "name 'decision' is not defined" bug in adapter lookup inside route_request
old_route_request = """            for decision in ranked_decisions:
                adapter_key = decision.model_id.split('_')[0]
                model_id = decision.model_id
                adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)
                if not adapter: print(f'Missing adapter for {decision.model_id}')"""

new_route_request = """            for decision in ranked_decisions:
                adapter_key = decision.model_id.split('_')[0]
                model_id = decision.model_id
                adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)
                if not adapter: logger.warning(f'Missing adapter for {decision.model_id}')"""

content = content.replace(old_route_request, new_route_request)

# But more importantly, the exception says "name 'decision' is not defined" 
# which might mean it's in get_ranked_models during the setup.
# Let's fix the get_ranked_models lazy loading scope issue where it used "decision.model_id" 
# before "decision" even existed!
lazy_load_bad = "adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)"
lazy_load_good = "adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)"
# We need to replace ONLY the one inside get_ranked_models.
get_ranked_str = """            for model_id, model_info in self.models.items():
                adapter_key = model_id.split('_')[0]
                adapter = self.adapters.get(decision.model_id) or self.adapters.get(adapter_key)"""
if get_ranked_str in content:
    content = content.replace(
        get_ranked_str,
        """            for model_id, model_info in self.models.items():
                adapter_key = model_id.split('_')[0]
                adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)"""
    )


# 2. Fix the Pydantic validation error for RoutingRequest
# The user is sending Claude/Gemini structured messages `[{'type': 'text', 'text': '...'}]` instead of standard strings.
chat_comp_bad = """        # Convert standard request to internal routing request
        routing_request = RoutingRequest(
            query=request.messages[-1]['content'] if request.messages else "",
            parameters={
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "model": request.model
            }
        )"""

chat_comp_good = """        # Convert standard request to internal routing request
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
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "model": request.model
            }
        )"""

content = content.replace(chat_comp_bad, chat_comp_good)

with open("src/router/core.py", "w") as f:
    f.write(content)
